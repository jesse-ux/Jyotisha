#!/usr/bin/env python3
"""Build a compact batch closure report by reusing existing oracle entrypoints."""

from __future__ import annotations

import argparse
import json
from typing import Any

from scripts.dasha_oracle_closure_status import build_status as build_dasha_status
from scripts.shadbala_oracle_comparison import compare_case as compare_shadbala_case


SHADBALA_CASE_IDS = [
    "template_steve_jobs_dasha_lahiri",
    "template_steve_jobs_dasha_lahiri",
]


def build_report(oracle_file: str) -> dict[str, Any]:
    dasha = build_dasha_status(oracle_file)
    shadbala_rows = []
    shadbala_within_tolerance = 0

    for case_id in SHADBALA_CASE_IDS:
        report = compare_shadbala_case(oracle_file=oracle_file, case_id=case_id)
        within = report["summary"]["planet_count"] == report["summary"]["planets_within_total_tolerance"]
        if within:
            shadbala_within_tolerance += 1
        shadbala_rows.append({
            "kind": "shadbala",
            "case_id": report["case_id"],
            "status": report["status"],
            "ayanamsa": report["settings"].get("ayanamsa"),
            "planets_within_total_tolerance": report["summary"]["planets_within_total_tolerance"],
            "planet_count": report["summary"]["planet_count"],
            "max_abs_total_delta_rupa": report["summary"]["max_abs_total_delta_rupa"],
            "global_scaling_recommendation": report["global_scaling_check"].get("recommendation"),
            "within_case_tolerance": within,
        })

    rows = [{
        "kind": "dasha",
        "dasha_task_count": dasha["summary"]["dasha_task_count"],
        "external_verified_dasha_tasks": dasha["summary"]["external_verified_dasha_tasks"],
        "can_claim_dasha_oracle_closure": dasha["summary"]["can_claim_dasha_oracle_closure"],
        "production_tuning_allowed": dasha["summary"]["production_tuning_allowed"],
    }, *shadbala_rows]

    return {
        "scope": "oracle_batch_closure_pack",
        "schema_version": 1,
        "summary": {
            "dasha_can_claim_closure": dasha["summary"]["can_claim_dasha_oracle_closure"],
            "shadbala_case_count": len(shadbala_rows),
            "shadbala_within_tolerance_case_count": shadbala_within_tolerance,
            "global_oracle_closure_blocked": True,
        },
        "rows": rows,
        "boundary": (
            "This pack reuses existing Dasha and Shadbala oracle entrypoints. "
            "Dasha-only closure can be complete while global oracle closure remains blocked "
            "until Shadbala and other non-Dasha fronts are closed."
        ),
        "next_actions": [
            "Keep reusing dasha_oracle_closure_status.py for Dasha truth instead of duplicating logic.",
            "Expand Shadbala comparison case count before changing any production-tuning claim.",
            "Do not apply a global scaling factor when component-level deltas disagree by planet.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a compact batched oracle closure report")
    parser.add_argument("--oracle-file", default="references/oracle/dasha_shadbala_oracle_cases.json")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    report = build_report(args.oracle_file)
    if args.format == "markdown":
        lines = [
            "# Oracle Batch Closure Pack",
            "",
            f"- dasha_can_claim_closure: `{str(report['summary']['dasha_can_claim_closure']).lower()}`",
            f"- shadbala_case_count: `{report['summary']['shadbala_case_count']}`",
            f"- shadbala_within_tolerance_case_count: `{report['summary']['shadbala_within_tolerance_case_count']}`",
            f"- global_oracle_closure_blocked: `{str(report['summary']['global_oracle_closure_blocked']).lower()}`",
            "",
            "| Kind | Case | Status | Notes |",
            "| --- | --- | --- | --- |",
        ]
        for row in report["rows"]:
            if row["kind"] == "dasha":
                lines.append(
                    f"| dasha | target_set | {'closed' if row['can_claim_dasha_oracle_closure'] else 'open'} | "
                    f"{row['external_verified_dasha_tasks']}/{row['dasha_task_count']} external verified |"
                )
            else:
                lines.append(
                    f"| shadbala | {row['case_id']} | {row['status']} | "
                    f"{row['planets_within_total_tolerance']}/{row['planet_count']} planets within tolerance; "
                    f"max delta {row['max_abs_total_delta_rupa']} |"
                )
        print("\n".join(lines))
        return

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
