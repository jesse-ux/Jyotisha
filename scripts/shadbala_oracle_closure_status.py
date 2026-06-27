#!/usr/bin/env python3
"""Report the shortest path to Shadbala external absolute-value closure."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIRST_PRIORITY_CASE_ID = "template_redacted_place_shadbala_raman"
FIRST_PRIORITY_TEMPLATE_PATH = "references/oracle/evidence_packet_templates/shadbala_redacted_place_raman_first_packet.json"
SHADBALA_TARGET_FIELD = "target.shadbala_components"
SUPPORTING_TARGET_FIELDS = ["target.moon_sidereal_longitude_deg"]
REQUIRED_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
REQUIRED_COMPONENTS = ["sthana", "dig", "kala", "chesta", "naisargika", "drik", "total_rupa"]


def _run_json(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return json.loads(completed.stdout)


def _metadata_missing(packet: dict[str, Any]) -> list[str]:
    metadata = packet.get("metadata", {})
    missing: list[str] = []
    for field in packet.get("required_metadata_fields", []):
        value = metadata.get(field)
        if value is None or value == "" or value == [] or value == {}:
            missing.append(f"metadata.{field}")
    source_artifact = metadata.get("source_artifact")
    if source_artifact in {"references/oracle/artifacts/", "references/oracle/artifacts", "", None}:
        if "metadata.source_artifact" not in missing:
            missing.append("metadata.source_artifact")
    return missing


def _shadbala_missing(packet: dict[str, Any]) -> list[str]:
    placeholders = packet.get("target_placeholders", {})
    value = placeholders.get(SHADBALA_TARGET_FIELD)
    missing: list[str] = []
    if not isinstance(value, dict):
        return [
            f"{SHADBALA_TARGET_FIELD}.{planet}.{component}"
            for planet in REQUIRED_PLANETS
            for component in REQUIRED_COMPONENTS
        ]
    for planet in REQUIRED_PLANETS:
        row = value.get(planet)
        if not isinstance(row, dict):
            missing.extend(f"{SHADBALA_TARGET_FIELD}.{planet}.{component}" for component in REQUIRED_COMPONENTS)
            continue
        for component in REQUIRED_COMPONENTS:
            component_value = row.get(component)
            if component_value is None or component_value == "" or component_value == [] or component_value == {}:
                missing.append(f"{SHADBALA_TARGET_FIELD}.{planet}.{component}")
    return missing


def _supporting_missing(packet: dict[str, Any], target_fields: list[str]) -> list[str]:
    placeholders = packet.get("target_placeholders", {})
    missing: list[str] = []
    for field in SUPPORTING_TARGET_FIELDS:
        if field not in target_fields:
            continue
        value = placeholders.get(field)
        if value is None or value == "" or value == [] or value == {}:
            missing.append(field)
    return missing


def _shadbala_target_filled(task: dict[str, Any]) -> bool:
    packet = task.get("evidence_packet", {})
    return (
        task.get("status") == "external_verified"
        and not _supporting_missing(packet, task.get("target_fields", []))
        and not _shadbala_missing(packet)
    )


def _group_missing_fields(missing_fields: list[str]) -> dict[str, Any]:
    metadata_fields = [field for field in missing_fields if field.startswith("metadata.")]
    target_fields = [field for field in missing_fields if field.startswith("target.")]
    body_groups: dict[str, list[str]] = {}
    prefix = f"{SHADBALA_TARGET_FIELD}."
    for field in target_fields:
        if not field.startswith(prefix):
            continue
        remainder = field[len(prefix):]
        body, _, component = remainder.partition(".")
        if not body or not component:
            continue
        body_groups.setdefault(body, []).append(field)
    grouped_bodies = {
        body: {
            "count": len(fields),
            "fields": fields,
        }
        for body, fields in sorted(body_groups.items())
    }
    return {
        "metadata": {
            "count": len(metadata_fields),
            "fields": metadata_fields,
        },
        "target": {
            "count": len(target_fields),
            "fields": target_fields,
        },
        "bodies": grouped_bodies,
    }


def _prefilled_fields(packet: dict[str, Any], missing_fields: list[str]) -> dict[str, Any]:
    missing = set(missing_fields)
    metadata = {
        key: value
        for key, value in packet.get("metadata", {}).items()
        if f"metadata.{key}" not in missing and value not in ("", None, [], {})
    }
    settings = {
        key: value
        for key, value in packet.get("settings", {}).items()
        if value not in ("", None, [], {})
    }
    return {
        "status": packet.get("status"),
        "promotion_status_after_fill": packet.get("promotion_status_after_fill"),
        "metadata": metadata,
        "settings": settings,
    }


def _manual_fill_plan(packet: dict[str, Any], missing_fields: list[str]) -> dict[str, Any]:
    return {
        "status_value": packet.get("promotion_status_after_fill", "external_verified"),
        "manual_entry_count": len(missing_fields),
        "remaining_manual_fields": missing_fields,
    }


def _apply_command(packet_path: str, oracle_file: str) -> str:
    return (
        "python3 scripts/oracle_collection_queue.py "
        f"--oracle-file {oracle_file} "
        f"--apply-packet {packet_path} "
        "--format json"
    )


def _validate_command(oracle_file: str) -> str:
    return (
        "python3 scripts/oracle_collection_queue.py "
        f"--oracle-file {oracle_file} --format json > /tmp/jyotish_oracle_queue_filled.json && "
        "python3 scripts/oracle_evidence_validator.py --queue-file /tmp/jyotish_oracle_queue_filled.json"
    )


def build_status(oracle_file: str) -> dict[str, Any]:
    queue = _run_json([PYTHON, "scripts/oracle_collection_queue.py", "--oracle-file", oracle_file, "--format", "json"])
    shadbala_tasks = [
        task for task in queue.get("tasks", [])
        if SHADBALA_TARGET_FIELD in task.get("target_fields", [])
    ]
    unverified_shadbala_tasks = [
        task for task in shadbala_tasks
        if not _shadbala_target_filled(task)
    ]
    priority_pool = unverified_shadbala_tasks or shadbala_tasks
    priority = next((task for task in priority_pool if task.get("case_id") == FIRST_PRIORITY_CASE_ID), None)
    if priority is None and priority_pool:
        priority = priority_pool[0]
    if priority is None and shadbala_tasks:
        raise RuntimeError("No Shadbala target task found")

    external_verified = [
        task for task in shadbala_tasks
        if _shadbala_target_filled(task)
    ]
    closure_complete = bool(shadbala_tasks) and len(external_verified) == len(shadbala_tasks)

    if closure_complete:
        return {
            "scope": "shadbala_external_absolute_value_closure_status",
            "schema_version": 1,
            "summary": {
                "shadbala_task_count": len(shadbala_tasks),
                "external_verified_shadbala_tasks": len(external_verified),
                "can_claim_shadbala_absolute_closure": True,
                "production_tuning_allowed": False,
                "required_planets": REQUIRED_PLANETS,
                "required_components": REQUIRED_COMPONENTS,
            },
            "first_priority": None,
            "next_actions": [
                "Shadbala external absolute-value closure is complete for the current target set.",
                "Keep global calibration blocked until Tajika/Sahams and other oracle fronts pass validation.",
            ],
            "boundary": (
                "This board isolates Shadbala absolute values. Dasha boundary dates are a separate closure task. "
                "Production tuning remains forbidden until external component-level evidence is complete."
            ),
        }

    if priority is None:
        raise RuntimeError("No Shadbala target task found")

    queue_packet = priority["evidence_packet"]
    capture_id = queue_packet["capture_id"]
    packet_path = f"references/oracle/artifacts/pending_packets/{capture_id}.json"
    template_path = FIRST_PRIORITY_TEMPLATE_PATH if priority["case_id"] == FIRST_PRIORITY_CASE_ID else packet_path
    packet = json.loads((ROOT / template_path).read_text(encoding="utf-8"))
    target_fields = priority.get("target_fields", [])
    supporting_target_fields = [field for field in SUPPORTING_TARGET_FIELDS if field in target_fields]
    missing_fields = _metadata_missing(packet) + _supporting_missing(packet, target_fields) + _shadbala_missing(packet)
    missing_groups = _group_missing_fields(missing_fields)

    return {
        "scope": "shadbala_external_absolute_value_closure_status",
        "schema_version": 1,
        "summary": {
            "shadbala_task_count": len(shadbala_tasks),
            "external_verified_shadbala_tasks": len(external_verified),
            "can_claim_shadbala_absolute_closure": closure_complete,
            "production_tuning_allowed": False,
            "required_planets": REQUIRED_PLANETS,
            "required_components": REQUIRED_COMPONENTS,
        },
        "first_priority": {
            "case_id": priority["case_id"],
            "capture_id": capture_id,
            "packet_path": packet_path,
            "birth": priority.get("birth", {}),
            "settings": priority.get("settings", {}),
            "required_target_fields": supporting_target_fields + [SHADBALA_TARGET_FIELD],
            "missing_fields": missing_fields,
            "missing_groups": missing_groups,
            "prefilled_fields": _prefilled_fields(packet, missing_fields),
            "manual_fill_plan": _manual_fill_plan(packet, missing_fields),
            "external_sources": [
                "JHora Shadbala component table screenshot",
                "PyJHora black-box shadbala output",
                "documented printed/software Shadbala example",
            ],
            "artifact_policy": "Save redacted screenshots or stdout snippets under references/oracle/artifacts/.",
            "reject_global_scaling": True,
            "apply_command": _apply_command(packet_path, oracle_file),
            "validate_command": _validate_command(oracle_file),
        },
        "next_actions": [
            "Fill any supporting target fields on the same oracle row, such as Moon sidereal longitude, before validator review.",
            "Fill all seven planets with Sthana, Dig, Kala, Chesta, Naisargika, Drik and total_rupa from an external oracle.",
            "Do not use a single global multiplier to force totals; validator checks component sums.",
            "Set status to external_verified only after artifact path and all Shadbala targets are filled.",
            "Apply the packet, regenerate the queue, and run oracle_evidence_validator.py.",
        ],
        "boundary": (
            "This board isolates Shadbala absolute values. Dasha boundary dates are a separate closure task. "
            "Production tuning remains forbidden until external component-level evidence is complete."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    first = report["first_priority"]
    lines = [
        "# Shadbala External Absolute-Value Closure Status",
        "",
        f"- shadbala_task_count: `{summary['shadbala_task_count']}`",
        f"- external_verified_shadbala_tasks: `{summary['external_verified_shadbala_tasks']}`",
        f"- can_claim_shadbala_absolute_closure: `{str(summary['can_claim_shadbala_absolute_closure']).lower()}`",
        f"- production_tuning_allowed: `{str(summary['production_tuning_allowed']).lower()}`",
        "",
    ]
    if first is None:
        lines.extend([
            "## Closure Complete",
            "",
            "Shadbala external absolute-value closure is complete for the current target set.",
            "",
            "## Next Actions",
            "",
        ])
        lines.extend(f"- {item}" for item in report["next_actions"])
        lines.extend(["", "## Boundary", "", report["boundary"], ""])
        return "\n".join(lines)

    lines.extend([
        "## First Priority Packet",
        "",
        f"- case_id: `{first['case_id']}`",
        f"- capture_id: `{first['capture_id']}`",
        f"- packet_path: `{first['packet_path']}`",
        f"- required_target_fields: `{', '.join(first['required_target_fields'])}`",
        f"- reject_global_scaling: `{str(first['reject_global_scaling']).lower()}`",
        "",
        "## Missing Summary",
        "",
        f"- metadata: `{first['missing_groups']['metadata']['count']}`",
        f"- target: `{first['missing_groups']['target']['count']}`",
    ])
    if first["missing_groups"]["bodies"]:
        lines.extend(["- bodies:", ""])
        lines.extend(
            f"  - {body}: `{payload['count']}`"
            for body, payload in first["missing_groups"]["bodies"].items()
        )
    lines.extend(
        [
            "",
            "## Prefilled Fields",
            "",
            f"- status: `{first['prefilled_fields']['status']}`",
            f"- promotion_status_after_fill: `{first['prefilled_fields']['promotion_status_after_fill']}`",
            "",
        ]
    )
    if first["prefilled_fields"]["metadata"]:
        lines.append("- metadata:")
        lines.append("")
        lines.extend(
            f"  - {key}: `{value}`"
            for key, value in first["prefilled_fields"]["metadata"].items()
        )
        lines.append("")
    if first["prefilled_fields"]["settings"]:
        lines.append("- settings:")
        lines.append("")
        lines.extend(
            f"  - {key}: `{value}`"
            for key, value in first["prefilled_fields"]["settings"].items()
        )
        lines.append("")
    lines.extend(
        [
            "## Manual Fill Plan",
            "",
            f"- status_value: `{first['manual_fill_plan']['status_value']}`",
            f"- manual_entry_count: `{first['manual_fill_plan']['manual_entry_count']}`",
            "",
            "## Missing Fields",
            "",
        ]
    )
    lines.extend(f"- `{field}`" for field in first["missing_fields"])
    lines.extend(
        [
        "## Required Matrix",
        "",
        f"- planets: `{', '.join(summary['required_planets'])}`",
        f"- components: `{', '.join(summary['required_components'])}`",
        "",
        "## Commands",
        "",
        "```bash",
        first["apply_command"],
        "```",
        "",
        "```bash",
        first["validate_command"],
        "```",
        "",
        "## Next Actions",
        "",
        ]
    )
    lines.extend(f"- {item}" for item in report["next_actions"])
    lines.extend(["", "## Boundary", "", report["boundary"], ""])
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report Shadbala external absolute-value closure status")
    parser.add_argument("--oracle-file", default="references/oracle/dasha_shadbala_oracle_cases.json")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", help="Optional output path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_status(args.oracle_file)
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else render_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
