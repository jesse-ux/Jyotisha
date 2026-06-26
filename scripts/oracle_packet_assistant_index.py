#!/usr/bin/env python3
"""Aggregate the first-oracle packet assistants into one index."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FRONTS = ["dasha", "tajika_sahams", "shadbala"]


def _run_json(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return json.loads(completed.stdout)


def build_index() -> dict[str, Any]:
    fronts: dict[str, Any] = {}
    for front in FRONTS:
        report = _run_json([PYTHON, "scripts/first_oracle_packet_assistant.py", "--front", front, "--format", "json"])
        fronts[front] = {
            "case_id": report["case_id"],
            "capture_id": report["capture_id"],
            "operator_card": report["operator_card"],
            "packet_template": report["packet_template"],
            "missing_field_count": len(report["missing_fields"]),
            "ready_to_apply": report["ready_to_apply"],
            "apply_command": report["apply_command"],
        }
    recommended_order = sorted(
        [{"front": front, **fronts[front]} for front in FRONTS],
        key=lambda item: item["missing_field_count"],
    )
    return {
        "scope": "first_oracle_packet_assistant_index",
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "front_count": len(FRONTS),
            "all_ready_to_apply": all(fronts[front]["ready_to_apply"] for front in FRONTS),
        },
        "fronts": fronts,
        "recommended_order": recommended_order,
        "boundary": (
            "This index aggregates packet assistants only. It does not create oracle values, "
            "does not validate packets by itself, and does not change oracle files."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# First Oracle Packet Assistant Index",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Fronts",
        "",
        "| front | case_id | missing fields | ready_to_apply |",
        "|---|---|---:|---|",
    ]
    for front in FRONTS:
        row = report["fronts"][front]
        lines.append(
            f"| `{front}` | `{row['case_id']}` | {row['missing_field_count']} | `{str(row['ready_to_apply']).lower()}` |"
        )
    lines.extend(["", "## Recommended Order", ""])
    for item in report["recommended_order"]:
        lines.extend(
            [
                f"### {item['front']}",
                "",
                f"- case_id: `{item['case_id']}`",
                f"- missing_field_count: `{item['missing_field_count']}`",
                f"- operator_card: `{item['operator_card']}`",
                "",
                "```bash",
                item["apply_command"],
                "```",
                "",
            ]
        )
    lines.extend(["## Boundary", "", report["boundary"], ""])
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate first-oracle packet assistants")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", help="Optional output path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_index()
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else render_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
