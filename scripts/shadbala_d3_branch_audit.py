#!/usr/bin/env python3
"""Pin D3 drift to the exact calc_sthana_bala branch used by Shadbala."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from shadbala_d3_mapping_audit import build_report as build_mapping_report  # type: ignore
from shadbala_oracle_comparison import compare_case  # type: ignore


def _branch_name(row: dict[str, Any]) -> str:
    bucket = row.get("d3_dignity_bucket")
    if bucket == "exalted":
        return "direct_exaltation_branch"
    if bucket == "own":
        return "direct_own_sign_branch"
    if bucket == "debilitated":
        return "direct_debilitation_branch"
    return "fallback_dignity_score_branch"


def build_report(oracle_file: str) -> dict[str, Any]:
    mapping = build_mapping_report(oracle_file)
    rows = []
    branch_counts: dict[str, int] = {}
    branch_diffs: dict[str, list[float]] = {}

    for row in mapping.get("rows", []):
        branch = _branch_name(row)
        branch_counts[branch] = branch_counts.get(branch, 0) + 1
        comparison = compare_case(oracle_file, row["case_id"])
        planet_comparison = comparison.get("comparison", {}).get(row["planet"], {})
        sthana_component = planet_comparison.get("components", {}).get("sthana", {})
        abs_component_diff = sthana_component.get("abs_diff_rupa")
        if isinstance(abs_component_diff, (int, float)):
            branch_diffs.setdefault(branch, []).append(float(abs_component_diff))
        rows.append({
            **row,
            "sthana_abs_diff_rupa": abs_component_diff,
            "suspected_function": "calc_sthana_bala",
            "suspected_branch": branch,
            "branch_code_path": "calc_sthana_bala -> sapta_d3 -> own/exalted/debilitated/_dignity_score",
        })

    branch_hotspots = {}
    for branch, diffs in branch_diffs.items():
        branch_hotspots[branch] = {
            "row_count": len(diffs),
            "avg_abs_component_diff_rupa": round(sum(diffs) / len(diffs), 4) if diffs else None,
            "max_abs_component_diff_rupa": round(max(diffs), 4) if diffs else None,
        }

    return {
        "scope": "shadbala_d3_branch_audit",
        "schema_version": 1,
        "summary": {
            "row_count": len(rows),
            "global_closure_blocked": True,
        },
        "branch_counts": branch_counts,
        "branch_hotspots": branch_hotspots,
        "rows": rows,
        "boundary": (
            "This report does not change Shadbala scoring. It only maps each D3 drift case onto the exact "
            "calc_sthana_bala branch currently responsible for the local dignity score."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit exact D3 branch used by calc_sthana_bala")
    parser.add_argument("--oracle-file", default="references/oracle/dasha_shadbala_oracle_cases.json")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    report = build_report(args.oracle_file)
    if args.format == "markdown":
        lines = [
            "# Shadbala D3 Branch Audit",
            "",
            f"- row_count: `{report['summary']['row_count']}`",
            "",
            f"- branch_counts: `{report['branch_counts']}`",
            "",
            "| Case | Planet | D3 Bucket | Branch |",
            "| --- | --- | --- | --- |",
        ]
        for row in report["rows"]:
            lines.append(
                f"| {row['case_id']} | {row['planet']} | {row['d3_dignity_bucket']} | {row['suspected_branch']} |"
            )
        print("\n".join(lines))
        return

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
