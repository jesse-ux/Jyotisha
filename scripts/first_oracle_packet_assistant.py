#!/usr/bin/env python3
"""Assist filling the first external oracle packet without inventing oracle values."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

FRONTS = {
    "dasha": {
        "status_command": [
            PYTHON,
            "scripts/dasha_oracle_closure_status.py",
            "--oracle-file",
            "references/oracle/dasha_shadbala_oracle_cases.json",
            "--format",
            "json",
        ],
        "operator_card": "docs/benchmark/dasha_steve_jobs_first_packet_operator_card.md",
        "packet_template": "references/oracle/evidence_packet_templates/dasha_steve_jobs_lahiri_first_packet_only.json",
        "external_sources": [
            "JHora Vimshottari Dasha screen",
            "PyJHora black-box dasha output",
            "documented printed/software example",
        ],
    },
    "tajika_sahams": {
        "status_command": [
            PYTHON,
            "scripts/tajika_annual_closure_status.py",
            "--oracle-file",
            "references/oracle/tajika_annual_oracle_cases.json",
            "--format",
            "json",
        ],
        "operator_card": "docs/benchmark/tajika_steve_jobs_1984_first_packet_operator_card.md",
        "packet_template": "references/oracle/evidence_packet_templates/tajika_steve_jobs_1984_first_packet.json",
        "external_sources": [
            "JHora Varshaphala/Tajika annual chart screen",
            "PyJHora black-box annual output",
            "printed Tajika/Varshaphala example",
        ],
    },
    "shadbala": {
        "status_command": [
            PYTHON,
            "scripts/shadbala_oracle_closure_status.py",
            "--oracle-file",
            "references/oracle/dasha_shadbala_oracle_cases.json",
            "--format",
            "json",
        ],
        "operator_card": "docs/benchmark/shadbala_redacted_place_raman_first_packet_operator_card.md",
        "packet_template": "references/oracle/evidence_packet_templates/shadbala_redacted_place_raman_first_packet.json",
        "external_sources": [
            "JHora Shadbala component table screenshot",
            "PyJHora black-box shadbala output",
            "documented printed/software Shadbala example",
        ],
    }
}


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


def _packet_missing(packet_path: str) -> list[str]:
    packet = json.loads((ROOT / packet_path).read_text(encoding="utf-8"))
    missing: list[str] = []
    metadata = packet.get("metadata", {})
    for field in packet.get("required_metadata_fields", []):
        value = metadata.get(field)
        if value is None or value == "" or value == [] or value == {}:
            missing.append(f"metadata.{field}")
    if metadata.get("source_artifact") in {"references/oracle/artifacts/", "references/oracle/artifacts", "", None}:
        if "metadata.source_artifact" not in missing:
            missing.append("metadata.source_artifact")
    def walk(prefix: str, value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                walk(f"{prefix}.{key}" if prefix else key, child)
            return
        if value is None or value == "" or value == [] or value == {}:
            missing.append(prefix)

    for field, value in packet.get("target_placeholders", {}).items():
        walk(field, value)
    return missing


def build_report(front: str) -> dict[str, Any]:
    if front not in FRONTS:
        raise RuntimeError(f"Unsupported front: {front}")
    config = FRONTS[front]
    status = _run_json(config["status_command"])
    first = status["first_priority"]
    packet_missing = _packet_missing(config["packet_template"])
    return {
        "scope": "first_external_oracle_packet_assistant",
        "schema_version": 1,
        "front": front,
        "case_id": first["case_id"],
        "capture_id": first["capture_id"],
        "operator_card": config["operator_card"],
        "packet_template": config["packet_template"],
        "missing_fields": packet_missing,
        "ready_to_apply": not packet_missing,
        "external_sources": config["external_sources"],
        "apply_command": first["apply_command"].replace(first["packet_path"], config["packet_template"]),
        "validate_command": first["validate_command"],
        "boundary": (
            "This assistant only reports what to fill. It must not invent external oracle values, "
            "must not use local engine output as evidence, and must not copy incompatible external code."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# First External Oracle Packet Assistant",
        "",
        f"- front: `{report['front']}`",
        f"- case_id: `{report['case_id']}`",
        f"- capture_id: `{report['capture_id']}`",
        f"- ready_to_apply: `{str(report['ready_to_apply']).lower()}`",
        f"- operator_card: `{report['operator_card']}`",
        f"- packet_template: `{report['packet_template']}`",
        "",
        "## Missing Fields",
        "",
    ]
    lines.extend(f"- `{field}`" for field in report["missing_fields"])
    lines.extend(
        [
            "",
            "## External Sources",
            "",
        ]
    )
    lines.extend(f"- {source}" for source in report["external_sources"])
    lines.extend(
        [
            "",
            "## Apply",
            "",
            "```bash",
            report["apply_command"],
            "```",
            "",
            "## Validate",
            "",
            "```bash",
            report["validate_command"],
            "```",
            "",
            "## Boundary",
            "",
            report["boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assist the first external oracle packet")
    parser.add_argument("--front", choices=sorted(FRONTS), required=True)
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", help="Optional output path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(args.front)
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else render_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
