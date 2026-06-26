#!/usr/bin/env python3
"""Generate a Tajika/Sahams annual benchmark dashboard for the Jyotish skill."""

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


def build_dashboard(oracle_file: str) -> dict[str, Any]:
    queue = _run_json([PYTHON, "scripts/tajika_annual_oracle_queue.py", "--oracle-file", oracle_file, "--format", "json"])
    summary = queue["summary"]
    can_claim_closure = bool(summary["production_tuning_allowed"] and summary["ready_for_calibration"] == summary["total_tasks"])
    remaining_gap = (
        "Solar return exact time, Varsha Lagna, Muntha, Year Lord, Mudda Dasha first lord, "
        "Sahams and Tajika Yogas still need external JHora/PyJHora/book-example evidence before "
        "the Jyotish skill can claim Tajika/Sahams annual closure."
    )
    return {
        "scope": "tajika_sahams_annual_benchmark_dashboard",
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_tasks": summary["total_tasks"],
            "ready_for_collection": summary["ready_for_collection"],
            "ready_for_calibration": summary["ready_for_calibration"],
            "production_tuning_allowed": summary["production_tuning_allowed"],
            "by_status": summary["by_status"],
        },
        "annual_claim": {
            "can_claim_tajika_sahams_closure": can_claim_closure,
            "reason": (
                "Do not claim annual-chart closure until every template row is promoted to "
                "external_verified with human-reviewable artifacts."
            ),
        },
        "remaining_gap": remaining_gap,
        "next_actions": [
            "Fill one Steve Jobs annual evidence packet from JHora or PyJHora.",
            "Add solar return datetime and Varsha Lagna tolerance checks after the first external row exists.",
            "Add Saham-specific tolerance checks for Punya, Rajya and Vivah Saham.",
            "Expand the annual benchmark with at least one printed Varshaphala example.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    claim = report["annual_claim"]
    lines = [
        "# Tajika/Sahams Annual Benchmark Dashboard",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Annual Oracle Readiness",
        "",
        f"- total_tasks: `{summary['total_tasks']}`",
        f"- ready_for_collection: `{summary['ready_for_collection']}`",
        f"- ready_for_calibration: `{summary['ready_for_calibration']}`",
        f"- production_tuning_allowed: `{str(summary['production_tuning_allowed']).lower()}`",
        "",
        "## Annual Closure Claim",
        "",
        f"- can_claim_tajika_sahams_closure: `{str(claim['can_claim_tajika_sahams_closure']).lower()}`",
        f"- reason: {claim['reason']}",
        "",
        "## Remaining Gap",
        "",
        report["remaining_gap"],
        "",
        "## Next Actions",
        "",
    ]
    lines.extend(f"- {item}" for item in report["next_actions"])
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Tajika/Sahams annual benchmark dashboard")
    parser.add_argument("--oracle-file", default="references/oracle/tajika_annual_oracle_cases.json")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", help="Optional output path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_dashboard(args.oracle_file)
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else render_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
