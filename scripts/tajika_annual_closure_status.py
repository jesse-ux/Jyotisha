#!/usr/bin/env python3
"""Report the shortest path to Tajika/Sahams annual external closure."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIRST_PRIORITY_CASE_ID = "template_steve_jobs_varshaphala_1984_lahiri"
FIRST_PRIORITY_TEMPLATE_PATH = "references/oracle/evidence_packet_templates/tajika_steve_jobs_1984_first_packet.json"
REQUIRED_TARGET_FIELDS = [
    "target.solar_return_datetime",
    "target.varsha_lagna_deg",
    "target.muntha_sign",
    "target.year_lord",
    "target.mudda_dasha_first_lord",
    "target.sahams.punya_saham",
    "target.sahams.rajya_saham",
    "target.sahams.vivah_saham",
    "target.tajika_yogas",
    "target.source_artifact",
]


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


def _target_missing(packet: dict[str, Any]) -> list[str]:
    placeholders = packet.get("target_placeholders", {})
    missing: list[str] = []
    for field in REQUIRED_TARGET_FIELDS:
        value = placeholders.get(field)
        if value is None or value == "" or value == [] or value == {}:
            missing.append(field)
    return missing


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
        "python3 scripts/tajika_annual_oracle_queue.py "
        f"--oracle-file {oracle_file} "
        f"--apply-packet {packet_path} "
        "--format json"
    )


def _validate_command(oracle_file: str) -> str:
    return (
        "python3 scripts/tajika_annual_oracle_queue.py "
        f"--oracle-file {oracle_file} --format json && "
        "python3 scripts/tajika_annual_benchmark_dashboard.py "
        f"--oracle-file {oracle_file} --format json"
    )


def build_status(oracle_file: str) -> dict[str, Any]:
    queue = _run_json([PYTHON, "scripts/tajika_annual_oracle_queue.py", "--oracle-file", oracle_file, "--format", "json"])
    annual_tasks = queue.get("tasks", [])
    priority = next((task for task in annual_tasks if not task.get("ready_for_calibration")), None)
    if priority is None:
        priority = next((task for task in annual_tasks if task.get("case_id") == FIRST_PRIORITY_CASE_ID), None)
    if priority is None and annual_tasks:
        priority = annual_tasks[0]
    if priority is None:
        raise RuntimeError("No Tajika annual task found")

    queue_packet = priority["evidence_packet"]
    capture_id = queue_packet["capture_id"]
    packet_path = f"references/oracle/artifacts/pending_packets/{capture_id}.json"
    template_path = FIRST_PRIORITY_TEMPLATE_PATH if priority["case_id"] == FIRST_PRIORITY_CASE_ID else packet_path
    template_file = ROOT / template_path
    if template_file.exists():
        packet = json.loads(template_file.read_text(encoding="utf-8"))
    else:
        packet = queue_packet
    missing_fields = _metadata_missing(packet) + _target_missing(packet)
    missing_groups = _group_missing_fields(missing_fields)
    external_verified = [
        task for task in annual_tasks
        if task.get("status") == "external_verified" and not _target_missing(task.get("evidence_packet", {}))
    ]

    return {
        "scope": "tajika_sahams_annual_closure_status",
        "schema_version": 1,
        "summary": {
            "annual_task_count": len(annual_tasks),
            "external_verified_annual_tasks": len(external_verified),
            "can_claim_tajika_sahams_closure": bool(annual_tasks) and len(external_verified) == len(annual_tasks),
            "production_tuning_allowed": False,
        },
        "first_priority": {
            "case_id": priority["case_id"],
            "capture_id": capture_id,
            "packet_path": packet_path,
            "birth": priority.get("birth", {}),
            "settings": priority.get("settings", {}),
            "required_target_fields": REQUIRED_TARGET_FIELDS,
            "missing_fields": missing_fields,
            "missing_groups": missing_groups,
            "prefilled_fields": _prefilled_fields(packet, missing_fields),
            "manual_fill_plan": _manual_fill_plan(packet, missing_fields),
            "external_sources": [
                "JHora Varshaphala screenshot",
                "PyJHora black-box annual output",
                "printed Tajika/Varshaphala example",
            ],
            "artifact_policy": "Save redacted screenshots, stdout snippets or book citations under references/oracle/artifacts/.",
            "apply_command": _apply_command(packet_path, oracle_file),
            "validate_command": _validate_command(oracle_file),
        },
        "next_actions": [
            "Fill solar return datetime, Varsha Lagna, Muntha, Year Lord, first Mudda Dasha lord, three Sahams and Tajika Yogas from an external annual source.",
            "Document timezone/DST and solar-return convention before promoting the row.",
            "Set the row to external_verified only after target.source_artifact and metadata.source_artifact point to reviewable evidence.",
            "Regenerate the annual queue and benchmark dashboard.",
        ],
        "boundary": (
            "This board isolates Tajika/Sahams annual closure. Local scripts/varshaphala.py output is not an "
            "external oracle and must not be used as production tuning evidence."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    first = report["first_priority"]
    lines = [
        "# Tajika/Sahams Annual Closure Status",
        "",
        f"- annual_task_count: `{summary['annual_task_count']}`",
        f"- external_verified_annual_tasks: `{summary['external_verified_annual_tasks']}`",
        f"- can_claim_tajika_sahams_closure: `{str(summary['can_claim_tajika_sahams_closure']).lower()}`",
        f"- production_tuning_allowed: `{str(summary['production_tuning_allowed']).lower()}`",
        "",
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
    parser = argparse.ArgumentParser(description="Report Tajika/Sahams annual external closure status")
    parser.add_argument("--oracle-file", default="references/oracle/tajika_annual_oracle_cases.json")
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
