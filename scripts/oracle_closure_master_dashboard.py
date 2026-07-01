#!/usr/bin/env python3
"""Generate a unified dashboard for Jyotish external-oracle closure fronts."""

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
        timeout=90,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return json.loads(completed.stdout)


def _front_from_status(name: str, status: dict[str, Any], task_key: str, verified_key: str, claim_key: str) -> dict[str, Any]:
    summary = status["summary"]
    first = status["first_priority"]
    task_count = int(summary[task_key])
    verified = int(summary[verified_key])
    if first is None:
        return {
            "front": name,
            "task_count": task_count,
            "external_verified_tasks": verified,
            "open_tasks": task_count - verified,
            "can_claim_closure": bool(summary[claim_key]),
            "production_tuning_allowed": bool(summary.get("production_tuning_allowed", False)),
            "first_priority": None,
        }
    missing_fields = first.get("missing_fields", [])
    return {
        "front": name,
        "task_count": task_count,
        "external_verified_tasks": verified,
        "open_tasks": task_count - verified,
        "can_claim_closure": bool(summary[claim_key]),
        "production_tuning_allowed": bool(summary.get("production_tuning_allowed", False)),
        "first_priority": {
            "case_id": first["case_id"],
            "capture_id": first["capture_id"],
            "packet_path": first["packet_path"],
            "missing_field_count": len(missing_fields),
            "missing_fields": missing_fields,
            "missing_groups": first.get("missing_groups", {}),
            "prefilled_fields": first.get("prefilled_fields", {}),
            "manual_fill_plan": first.get("manual_fill_plan", {}),
            "apply_command": first.get("apply_command", ""),
            "validate_command": first.get("validate_command", ""),
        },
    }


def build_dashboard(dasha_oracle_file: str, tajika_oracle_file: str) -> dict[str, Any]:
    dasha_status = _run_json([
        PYTHON,
        "scripts/dasha_oracle_closure_status.py",
        "--oracle-file",
        dasha_oracle_file,
        "--format",
        "json",
    ])
    shadbala_status = _run_json([
        PYTHON,
        "scripts/shadbala_oracle_closure_status.py",
        "--oracle-file",
        dasha_oracle_file,
        "--format",
        "json",
    ])
    tajika_status = _run_json([
        PYTHON,
        "scripts/tajika_annual_closure_status.py",
        "--oracle-file",
        tajika_oracle_file,
        "--format",
        "json",
    ])

    fronts = {
        "dasha": _front_from_status(
            "dasha",
            dasha_status,
            "dasha_task_count",
            "external_verified_dasha_tasks",
            "can_claim_dasha_oracle_closure",
        ),
        "shadbala": _front_from_status(
            "shadbala",
            shadbala_status,
            "shadbala_task_count",
            "external_verified_shadbala_tasks",
            "can_claim_shadbala_absolute_closure",
        ),
        "tajika_sahams": _front_from_status(
            "tajika_sahams",
            tajika_status,
            "annual_task_count",
            "external_verified_annual_tasks",
            "can_claim_tajika_sahams_closure",
        ),
    }
    total_tasks = sum(front["task_count"] for front in fronts.values())
    verified_tasks = sum(front["external_verified_tasks"] for front in fronts.values())
    current_target_set_closed = total_tasks > 0 and verified_tasks == total_tasks
    next_action_order = sorted(
        [
            {
                "front": front["front"],
                "case_id": front["first_priority"]["case_id"],
                "capture_id": front["first_priority"]["capture_id"],
                "missing_field_count": front["first_priority"]["missing_field_count"],
                "manual_entry_count": int(front["first_priority"].get("manual_fill_plan", {}).get("manual_entry_count", front["first_priority"]["missing_field_count"])),
                "apply_command": front["first_priority"]["apply_command"],
            }
            for front in fronts.values()
            if not front["can_claim_closure"] and front["first_priority"] is not None
        ],
        key=lambda item: item["missing_field_count"],
    )
    return {
        "scope": "jyotish_external_oracle_closure_master_dashboard",
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_tasks": total_tasks,
            "external_verified_tasks": verified_tasks,
            "open_tasks": total_tasks - verified_tasks,
            "can_claim_current_target_set_closure": current_target_set_closed,
            "can_claim_global_oracle_closure": False,
            "production_tuning_allowed": False,
        },
        "fronts": fronts,
        "next_action_order": next_action_order,
        "boundary": (
            "This dashboard merges current target-set external evidence readiness only. A closed target set does not "
            "claim global oracle closure, does not claim prediction accuracy, does not tune production constants, "
            "and does not treat local engine output as oracle evidence."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Jyotish External Oracle Closure Master Dashboard",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- total_tasks: `{summary['total_tasks']}`",
        f"- external_verified_tasks: `{summary['external_verified_tasks']}`",
        f"- open_tasks: `{summary['open_tasks']}`",
        f"- can_claim_current_target_set_closure: `{str(summary['can_claim_current_target_set_closure']).lower()}`",
        f"- can_claim_global_oracle_closure: `{str(summary['can_claim_global_oracle_closure']).lower()}`",
        f"- production_tuning_allowed: `{str(summary['production_tuning_allowed']).lower()}`",
        "",
        "## Fronts",
        "",
        "| front | tasks | verified | first priority | missing fields | manual entries | metadata missing | target missing |",
        "|---|---:|---:|---|---:|---:|---:|---:|",
    ]
    for key in ["dasha", "tajika_sahams", "shadbala"]:
        front = report["fronts"][key]
        first = front["first_priority"]
        if first is None:
            lines.append(
                f"| `{key}` | {front['task_count']} | {front['external_verified_tasks']} | `complete` | "
                "0 | 0 | 0 | 0 |"
            )
            continue
        missing_groups = first.get("missing_groups", {})
        manual_fill_plan = first.get("manual_fill_plan", {})
        lines.append(
            f"| `{key}` | {front['task_count']} | {front['external_verified_tasks']} | `{first['case_id']}` | "
            f"{first['missing_field_count']} | {manual_fill_plan.get('manual_entry_count', first['missing_field_count'])} | "
            f"{missing_groups.get('metadata', {}).get('count', 0)} | {missing_groups.get('target', {}).get('count', 0)} |"
        )
    lines.extend(["", "## Next Action Order", ""])
    for item in report["next_action_order"]:
        lines.extend(
            [
                f"### {item['front']}",
                "",
                f"- case_id: `{item['case_id']}`",
                f"- capture_id: `{item['capture_id']}`",
                f"- missing_field_count: `{item['missing_field_count']}`",
                f"- manual_entry_count: `{item['manual_entry_count']}`",
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
    parser = argparse.ArgumentParser(description="Generate unified external-oracle closure dashboard")
    parser.add_argument("--dasha-oracle-file", default="references/oracle/dasha_shadbala_oracle_cases.json")
    parser.add_argument("--tajika-oracle-file", default="references/oracle/tajika_annual_oracle_cases.json")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", help="Optional output path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_dashboard(args.dasha_oracle_file, args.tajika_oracle_file)
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else render_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
