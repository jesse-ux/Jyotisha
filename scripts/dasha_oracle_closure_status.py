#!/usr/bin/env python3
"""Report the shortest path to the first Dasha external-oracle closure."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIRST_PRIORITY_CASE_ID = "template_steve_jobs_dasha_lahiri"
DASHA_TARGET_FIELD = "target.vimshottari_start_date"
FIRST_PRIORITY_TEMPLATE_PATH = "references/oracle/evidence_packet_templates/dasha_steve_jobs_lahiri_first_packet_only.json"


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


def _target_missing(packet: dict[str, Any], fields: list[str]) -> list[str]:
    placeholders = packet.get("target_placeholders", {})
    missing: list[str] = []
    for field in fields:
        value = placeholders.get(field)
        if value is None or value == "" or value == [] or value == {}:
            missing.append(field)
    return missing


def _dasha_target_filled(task: dict[str, Any], fields: list[str]) -> bool:
    packet = task.get("evidence_packet", {})
    return task.get("status") == "external_verified" and not _target_missing(packet, fields)


def _group_missing_fields(missing_fields: list[str]) -> dict[str, Any]:
    metadata_fields = [field for field in missing_fields if field.startswith("metadata.")]
    target_fields = [field for field in missing_fields if field.startswith("target.")]
    return {
        "metadata": {
            "count": len(metadata_fields),
            "fields": metadata_fields,
        },
        "target": {
            "count": len(target_fields),
            "fields": target_fields,
        },
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
    dasha_tasks = [
        task for task in queue.get("tasks", [])
        if DASHA_TARGET_FIELD in task.get("target_fields", [])
    ]
    required_target_fields = [DASHA_TARGET_FIELD]
    unverified_dasha_tasks = [
        task for task in dasha_tasks
        if not _dasha_target_filled(task, required_target_fields)
    ]
    dasha_closed = bool(dasha_tasks) and not unverified_dasha_tasks
    priority_pool = unverified_dasha_tasks if not dasha_closed else []
    priority = next((task for task in priority_pool if task.get("case_id") == FIRST_PRIORITY_CASE_ID), None)
    if priority is None and priority_pool:
        priority = priority_pool[0]
    if priority is None and not dasha_closed:
        raise RuntimeError("No Dasha target task found")
    external_verified = [
        task for task in dasha_tasks
        if _dasha_target_filled(task, required_target_fields)
    ]
    first_priority = None
    if priority is not None:
        queue_packet = priority["evidence_packet"]
        capture_id = queue_packet["capture_id"]
        packet_path = f"references/oracle/artifacts/pending_packets/{capture_id}.json"
        template_path = FIRST_PRIORITY_TEMPLATE_PATH if priority["case_id"] == FIRST_PRIORITY_CASE_ID else packet_path
        packet = json.loads((ROOT / template_path).read_text(encoding="utf-8"))
        missing_fields = _metadata_missing(packet) + _target_missing(packet, required_target_fields)
        missing_groups = _group_missing_fields(missing_fields)
        first_priority = {
            "case_id": priority["case_id"],
            "capture_id": capture_id,
            "packet_path": packet_path,
            "birth": priority.get("birth", {}),
            "settings": priority.get("settings", {}),
            "required_target_fields": required_target_fields,
            "missing_fields": missing_fields,
            "missing_groups": missing_groups,
            "prefilled_fields": _prefilled_fields(packet, missing_fields),
            "manual_fill_plan": _manual_fill_plan(packet, missing_fields),
            "external_sources": [
                "JHora Vimshottari Dasha screenshot",
                "PyJHora black-box dasha output",
                "documented printed/software example",
            ],
            "artifact_policy": "Save redacted screenshots or stdout snippets under references/oracle/artifacts/.",
            "apply_command": _apply_command(packet_path, oracle_file),
            "validate_command": _validate_command(oracle_file),
        }
    next_actions = [
        "Dasha-only external oracle closure is complete for the current target set.",
        "Keep global calibration blocked until Shadbala and other non-Dasha oracle packets pass validation.",
    ] if dasha_closed else [
        "Open the first priority packet and fill metadata from an external oracle.",
        "Fill target.vimshottari_start_date only from JHora/PyJHora/book example, not from this repository.",
        "Set status to external_verified after the artifact path and Dasha target are filled.",
        "Apply the packet, regenerate the queue, and run oracle_evidence_validator.py.",
    ]

    return {
        "scope": "dasha_external_oracle_closure_status",
        "schema_version": 1,
        "summary": {
            "dasha_task_count": len(dasha_tasks),
            "external_verified_dasha_tasks": len(external_verified),
            "can_claim_dasha_oracle_closure": bool(dasha_tasks) and len(external_verified) == len(dasha_tasks),
            "production_tuning_allowed": False,
        },
        "first_priority": first_priority,
        "next_actions": next_actions,
        "boundary": (
            "This board isolates the Dasha shortest path. Shadbala remains a separate absolute-value "
            "closure task and must not block collecting the first Dasha boundary date."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    first = report["first_priority"]
    lines = [
        "# Dasha External Oracle Closure Status",
        "",
        f"- dasha_task_count: `{summary['dasha_task_count']}`",
        f"- external_verified_dasha_tasks: `{summary['external_verified_dasha_tasks']}`",
        f"- can_claim_dasha_oracle_closure: `{str(summary['can_claim_dasha_oracle_closure']).lower()}`",
        f"- production_tuning_allowed: `{str(summary['production_tuning_allowed']).lower()}`",
        "",
    ]
    if first is None:
        lines.extend(
            [
                "## First Priority Packet",
                "",
                "- none: Dasha-only external oracle closure is complete for the current target set.",
                "",
                "## Next Actions",
                "",
            ]
        )
        lines.extend(f"- {item}" for item in report["next_actions"])
        lines.extend(["", "## Boundary", "", report["boundary"], ""])
        return "\n".join(lines)

    lines.extend(
        [
        "## First Priority Packet",
        "",
        f"- case_id: `{first['case_id']}`",
        f"- capture_id: `{first['capture_id']}`",
        f"- packet_path: `{first['packet_path']}`",
        f"- required_target_fields: `{', '.join(first['required_target_fields'])}`",
        "",
        "## Missing Summary",
        "",
        f"- metadata: `{first['missing_groups']['metadata']['count']}`",
        f"- target: `{first['missing_groups']['target']['count']}`",
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
    parser = argparse.ArgumentParser(description="Report Dasha external oracle closure status")
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
