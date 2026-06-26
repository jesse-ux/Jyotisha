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
SHADBALA_TARGET_FIELD = "target.shadbala_components"
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
    priority = next((task for task in shadbala_tasks if task.get("case_id") == FIRST_PRIORITY_CASE_ID), None)
    if priority is None and shadbala_tasks:
        priority = shadbala_tasks[0]
    if priority is None:
        raise RuntimeError("No Shadbala target task found")

    packet = priority["evidence_packet"]
    capture_id = packet["capture_id"]
    packet_path = f"references/oracle/artifacts/pending_packets/{capture_id}.json"
    missing_fields = _metadata_missing(packet) + _shadbala_missing(packet)
    external_verified = [
        task for task in shadbala_tasks
        if task.get("status") == "external_verified" and not _shadbala_missing(task.get("evidence_packet", {}))
    ]

    return {
        "scope": "shadbala_external_absolute_value_closure_status",
        "schema_version": 1,
        "summary": {
            "shadbala_task_count": len(shadbala_tasks),
            "external_verified_shadbala_tasks": len(external_verified),
            "can_claim_shadbala_absolute_closure": bool(shadbala_tasks) and len(external_verified) == len(shadbala_tasks),
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
            "required_target_fields": [SHADBALA_TARGET_FIELD],
            "missing_fields": missing_fields,
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
        "## First Priority Packet",
        "",
        f"- case_id: `{first['case_id']}`",
        f"- capture_id: `{first['capture_id']}`",
        f"- packet_path: `{first['packet_path']}`",
        f"- required_target_fields: `{', '.join(first['required_target_fields'])}`",
        f"- missing_fields: `{', '.join(first['missing_fields'])}`",
        f"- reject_global_scaling: `{str(first['reject_global_scaling']).lower()}`",
        "",
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
