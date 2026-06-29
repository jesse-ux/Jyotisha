#!/usr/bin/env python3
"""Audit whether D3 drift is caused by D3 mapping itself or dignity use in Shadbala."""

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

import jyotish_engine  # type: ignore
from divisional_charts_extended import DivisionalChartsCalculator  # type: ignore
from oracle_boundary_audit import _load_oracle, _namespace_from_template  # type: ignore
from shadbala_sapta_dignity_whitelist import build_report as build_whitelist_report  # type: ignore
from varga import calc_varga  # type: ignore


def _normalize_dignity_bucket(score: float) -> str:
    if score >= 50:
        return "exalted"
    if score >= 45:
        return "own"
    if score >= 35:
        return "friend"
    if score >= 25:
        return "neutral"
    if score >= 15:
        return "enemy"
    return "debilitated"


def _discover_cases(oracle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}
    for key in ("template_cases", "shadbala_cases"):
        for case in oracle.get(key, []):
            cid = case.get("id") or case.get("case_id")
            if isinstance(cid, str):
                cases[cid] = case
    return cases


def build_report(oracle_file: str) -> dict[str, Any]:
    whitelist = build_whitelist_report(oracle_file)
    oracle = _load_oracle(oracle_file)
    cases = _discover_cases(oracle)
    calc = DivisionalChartsCalculator()

    rows = []
    mapping_fault = 0
    dignity_fault = 0

    for row in whitelist.get("whitelist_rows", []):
        if row.get("layer") != "D3":
            continue
        case = cases[row["case_id"]]
        result = jyotish_engine.cmd_shadbala(_namespace_from_template(case))
        chart, _asc_idx, _jd, _aya = jyotish_engine._compute_chart_from_args(_namespace_from_template(case))
        planet = row["planet"]
        planet_data = (chart or {}).get("planets", {}).get(planet, {})
        lon = float(planet_data.get("degree", 0.0))

        d3_simple = calc_varga(lon, 3)
        d3_extended_abs = calc._calculate_d3(int(lon // 30), lon % 30)
        d3_extended = {
            "sign_idx": int(d3_extended_abs // 30) % 12,
            "sign": calc.SIGNS[int(d3_extended_abs // 30) % 12],
        }

        sthana = ((result.get("planets") or {}).get(planet) or {}).get("sthana_bala") or {}
        engine_d3_score = float(sthana.get("sapta_d3", 0.0))
        dignity_bucket = _normalize_dignity_bucket(engine_d3_score)
        mapping_matches = d3_simple.get("sign") == d3_extended["sign"]

        suspected = "d3_dignity_path" if mapping_matches else "d3_mapping_path"
        if mapping_matches:
            dignity_fault += 1
        else:
            mapping_fault += 1

        rows.append({
            "case_id": row["case_id"],
            "planet": planet,
            "mapping_matches_engine_sign": mapping_matches,
            "d3_simple_sign": d3_simple.get("sign"),
            "d3_extended_sign": d3_extended["sign"],
            "d3_dignity_bucket": dignity_bucket,
            "sapta_d3_score": round(engine_d3_score, 2),
            "suspected_path": suspected,
        })

    return {
        "scope": "shadbala_d3_mapping_audit",
        "schema_version": 1,
        "summary": {
            "case_count": len({row["case_id"] for row in rows}),
            "row_count": len(rows),
            "global_closure_blocked": True,
        },
        "suspected_fault_split": {
            "d3_mapping_path": mapping_fault,
            "d3_dignity_path": dignity_fault,
        },
        "rows": rows,
        "boundary": (
            "This audit compares two local D3 mapping paths against the D3 score consumed by Shadbala. "
            "If both mappings agree, the remaining suspect is the dignity score path rather than the D3 sign mapping."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit D3 mapping vs dignity path for Shadbala")
    parser.add_argument("--oracle-file", default="references/oracle/dasha_shadbala_oracle_cases.json")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    report = build_report(args.oracle_file)
    if args.format == "markdown":
        lines = [
            "# Shadbala D3 Mapping Audit",
            "",
            f"- case_count: `{report['summary']['case_count']}`",
            f"- row_count: `{report['summary']['row_count']}`",
            "",
            f"- suspected_fault_split: `{report['suspected_fault_split']}`",
            "",
            "| Case | Planet | Simple D3 | Extended D3 | D3 Dignity | Suspected Path |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for row in report["rows"]:
            lines.append(
                f"| {row['case_id']} | {row['planet']} | {row['d3_simple_sign']} | {row['d3_extended_sign']} | "
                f"{row['d3_dignity_bucket']} | {row['suspected_path']} |"
            )
        print("\n".join(lines))
        return

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
