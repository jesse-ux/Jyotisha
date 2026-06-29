#!/usr/bin/env python3
"""Targeted Sthana Bala audit across external-verified oracle cases."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from scripts import jyotish_engine
from scripts.oracle_boundary_audit import _load_oracle, _namespace_from_template
from scripts.shadbala_oracle_comparison import compare_case


ROOT = Path(__file__).resolve().parents[1]


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


def _suspected_driver(sthana: dict[str, Any], delta: float) -> str:
    sapta = float(sthana.get("sapta_score", 0.0))
    ucha = float(sthana.get("ucha_bala", 0.0))
    kendra = float(sthana.get("kendra_bala", 0.0))
    ojayugma = float(sthana.get("ojayugma_bala", 0.0))
    drekkana = float(sthana.get("drekkana_bala", 0.0))

    if sapta >= max(ucha, kendra, ojayugma, drekkana):
        d1_score = float(sthana.get("sapta_d1", 0.0))
        dignity = _normalize_dignity_bucket(d1_score)
        if dignity in {"own", "exalted", "debilitated"}:
            return f"sapta_dignity_{dignity}"
        return f"sapta_friend_enemy_{dignity}"
    if ucha >= max(kendra, ojayugma, drekkana):
        return "ucha_axis"
    if kendra >= max(ojayugma, drekkana):
        return "kendra_house_tiering"
    if ojayugma >= drekkana:
        return "ojayugma_parity"
    return "drekkana_bucket"


def build_report(oracle_file: str) -> dict[str, Any]:
    oracle = _load_oracle(oracle_file)
    cases = []
    for key in ("template_cases", "shadbala_cases"):
        for case in oracle.get(key, []):
            if case.get("status") != "external_verified":
                continue
            if not isinstance(case.get("target", {}).get("shadbala_components"), dict):
                continue
            cases.append(case)

    rows: list[dict[str, Any]] = []
    driver_counts: Counter[str] = Counter()

    for case in cases:
        case_id = case.get("id") or case.get("case_id")
        comparison = compare_case(oracle_file=oracle_file, case_id=case_id)
        result = jyotish_engine.cmd_shadbala(_namespace_from_template(case))
        for planet, comp_row in comparison.get("comparison", {}).items():
            sthana_component = (comp_row.get("components") or {}).get("sthana") or {}
            local_planet = (result.get("planets") or {}).get(planet) or {}
            sthana = local_planet.get("sthana_bala") or {}
            diff = sthana_component.get("diff_rupa")
            if not isinstance(diff, (int, float)):
                continue
            driver = _suspected_driver(sthana, float(diff))
            driver_counts[driver] += 1
            d1_score = float(sthana.get("sapta_d1", 0.0))
            rows.append({
                "case_id": case_id,
                "planet": planet,
                "sthana_diff_rupa": round(float(diff), 4),
                "abs_sthana_diff_rupa": round(abs(float(diff)), 4),
                "d1_dignity_bucket": _normalize_dignity_bucket(d1_score),
                "sapta_score": round(float(sthana.get("sapta_score", 0.0)), 2),
                "ucha_bala": round(float(sthana.get("ucha_bala", 0.0)), 2),
                "kendra_bala": round(float(sthana.get("kendra_bala", 0.0)), 2),
                "ojayugma_bala": round(float(sthana.get("ojayugma_bala", 0.0)), 2),
                "drekkana_bala": round(float(sthana.get("drekkana_bala", 0.0)), 2),
                "suspected_driver": driver,
            })

    rows.sort(key=lambda row: (-row["abs_sthana_diff_rupa"], row["case_id"], row["planet"]))

    return {
        "scope": "shadbala_sthana_targeted_audit",
        "schema_version": 1,
        "summary": {
            "case_count": len(cases),
            "row_count": len(rows),
            "global_closure_blocked": True,
            "top_driver": rows[0]["suspected_driver"] if rows else None,
        },
        "driver_counts": dict(driver_counts),
        "rows": rows,
        "boundary": (
            "This targeted audit reuses local Shadbala output plus oracle comparisons to classify Sthana divergence "
            "into dignity/friend-enemy/house-tiering style buckets. It is diagnostic, not a calibration override."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Targeted audit for Sthana Bala divergence")
    parser.add_argument("--oracle-file", default="references/oracle/dasha_shadbala_oracle_cases.json")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    report = build_report(args.oracle_file)
    if args.format == "markdown":
        lines = [
            "# Shadbala Sthana Targeted Audit",
            "",
            f"- case_count: `{report['summary']['case_count']}`",
            f"- row_count: `{report['summary']['row_count']}`",
            f"- top_driver: `{report['summary']['top_driver']}`",
            "",
            "## Driver Counts",
            "",
        ]
        for name, count in sorted(report["driver_counts"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- `{name}`: {count}")
        lines.extend([
            "",
            "## Largest Sthana Deltas",
            "",
            "| Case | Planet | Abs Diff | D1 Bucket | Suspected Driver |",
            "| --- | --- | ---: | --- | --- |",
        ])
        for row in report["rows"][:20]:
            lines.append(
                f"| {row['case_id']} | {row['planet']} | {row['abs_sthana_diff_rupa']} | "
                f"{row['d1_dignity_bucket']} | {row['suspected_driver']} |"
            )
        print("\n".join(lines))
        return

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
