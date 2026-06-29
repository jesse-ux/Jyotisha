#!/usr/bin/env python3
"""Summarize all external-verified Shadbala oracle cases using the existing comparison entrypoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.shadbala_oracle_comparison import compare_case


ROOT = Path(__file__).resolve().parents[1]


def _load_oracle(path: str) -> dict[str, Any]:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = ROOT / resolved
    return json.loads(resolved.read_text(encoding="utf-8"))


def _discover_case_ids(oracle: dict[str, Any]) -> list[str]:
    case_ids: list[str] = []
    for key in ("template_cases", "shadbala_cases"):
        for case in oracle.get(key, []):
            if case.get("status") != "external_verified":
                continue
            if not isinstance(case.get("target", {}).get("shadbala_components"), dict):
                continue
            case_id = case.get("id") or case.get("case_id")
            if isinstance(case_id, str):
                case_ids.append(case_id)
    return case_ids


def build_report(oracle_file: str) -> dict[str, Any]:
    oracle = _load_oracle(oracle_file)
    case_ids = _discover_case_ids(oracle)
    rows = []
    fully_within_tolerance = 0

    for case_id in case_ids:
        report = compare_case(oracle_file=oracle_file, case_id=case_id)
        within = report["summary"]["planet_count"] == report["summary"]["planets_within_total_tolerance"]
        if within:
            fully_within_tolerance += 1
        rows.append({
            "case_id": report["case_id"],
            "status": report["status"],
            "ayanamsa": report["settings"].get("ayanamsa"),
            "node_mode": report["settings"].get("node_mode"),
            "planets_within_total_tolerance": report["summary"]["planets_within_total_tolerance"],
            "planet_count": report["summary"]["planet_count"],
            "max_abs_total_delta_rupa": report["summary"]["max_abs_total_delta_rupa"],
            "global_scaling_recommendation": report["global_scaling_check"].get("recommendation"),
            "within_case_tolerance": within,
        })

    return {
        "scope": "shadbala_oracle_batch_summary",
        "schema_version": 1,
        "summary": {
            "case_count": len(rows),
            "external_verified_case_count": len(case_ids),
            "fully_within_tolerance_case_count": fully_within_tolerance,
            "global_closure_blocked": True,
        },
        "rows": rows,
        "boundary": (
            "This summary reuses shadbala_oracle_comparison.py for every external-verified Shadbala case. "
            "It is diagnostic and keeps global closure blocked until enough cases converge."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a batch summary for external-verified Shadbala oracle cases")
    parser.add_argument("--oracle-file", default="references/oracle/dasha_shadbala_oracle_cases.json")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    report = build_report(args.oracle_file)
    if args.format == "markdown":
        lines = [
            "# Shadbala Oracle Batch Summary",
            "",
            f"- case_count: `{report['summary']['case_count']}`",
            f"- external_verified_case_count: `{report['summary']['external_verified_case_count']}`",
            f"- fully_within_tolerance_case_count: `{report['summary']['fully_within_tolerance_case_count']}`",
            f"- global_closure_blocked: `{str(report['summary']['global_closure_blocked']).lower()}`",
            "",
            "| Case | Ayanamsa | Node | Within Total Tolerance | Max Delta |",
            "| --- | --- | --- | --- | ---: |",
        ]
        for row in report["rows"]:
            lines.append(
                f"| {row['case_id']} | {row['ayanamsa']} | {row['node_mode']} | "
                f"{row['planets_within_total_tolerance']}/{row['planet_count']} | {row['max_abs_total_delta_rupa']} |"
            )
        print("\n".join(lines))
        return

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
