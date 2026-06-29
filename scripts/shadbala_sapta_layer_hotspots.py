#!/usr/bin/env python3
"""Identify which Sapta Varga layers dominate Sthana oracle drift."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from scripts import jyotish_engine
from scripts.oracle_boundary_audit import _load_oracle, _namespace_from_template


ROOT = Path(__file__).resolve().parents[1]
SAPTA_KEYS = ["sapta_d1", "sapta_d2", "sapta_d3", "sapta_d4", "sapta_d7", "sapta_d9", "sapta_d12"]
LAYER_LABELS = {
    "sapta_d1": "D1",
    "sapta_d2": "D2",
    "sapta_d3": "D3",
    "sapta_d4": "D4",
    "sapta_d7": "D7",
    "sapta_d9": "D9",
    "sapta_d12": "D12",
}


def _discover_cases(oracle: dict[str, Any]) -> list[dict[str, Any]]:
    cases = []
    for key in ("template_cases", "shadbala_cases"):
        for case in oracle.get(key, []):
            if case.get("status") != "external_verified":
                continue
            if not isinstance(case.get("target", {}).get("shadbala_components"), dict):
                continue
            cases.append(case)
    return cases


def _normalize_dignity_bucket(score: float) -> str:
    if score >= 50:
        return "dignity_exalted"
    if score >= 45:
        return "dignity_own"
    if score >= 35:
        return "friend_enemy_friend"
    if score >= 25:
        return "friend_enemy_neutral"
    if score >= 15:
        return "friend_enemy_enemy"
    return "dignity_debilitated"


def build_report(oracle_file: str) -> dict[str, Any]:
    oracle = _load_oracle(oracle_file)
    cases = _discover_cases(oracle)

    layer_values: dict[str, list[float]] = defaultdict(list)
    rows: list[dict[str, Any]] = []
    driver_mix: Counter[str] = Counter()

    for case in cases:
        case_id = case.get("id") or case.get("case_id")
        result = jyotish_engine.cmd_shadbala(_namespace_from_template(case))
        for planet, pdata in (result.get("planets") or {}).items():
            sthana = pdata.get("sthana_bala") or {}
            layer_pairs = [(key, float(sthana.get(key, 0.0))) for key in SAPTA_KEYS]
            dominant_key, dominant_value = max(layer_pairs, key=lambda item: item[1])
            driver = _normalize_dignity_bucket(dominant_value)
            driver_mix[driver] += 1
            layer_values[dominant_key].append(dominant_value)
            rows.append({
                "case_id": case_id,
                "planet": planet,
                "dominant_layer_key": dominant_key,
                "dominant_layer": LAYER_LABELS[dominant_key],
                "dominant_layer_score": round(dominant_value, 2),
                "driver_guess": driver,
                "layer_scores": {LAYER_LABELS[key]: round(value, 2) for key, value in layer_pairs},
            })

    rows.sort(key=lambda row: (-row["dominant_layer_score"], row["case_id"], row["planet"]))
    layer_hotspots = sorted(
        [
            {
                "layer": LAYER_LABELS[key],
                "avg_score": round(sum(values) / len(values), 4),
                "max_score": round(max(values), 4),
                "sample_count": len(values),
            }
            for key, values in layer_values.items()
            if values
        ],
        key=lambda row: (-row["avg_score"], -row["max_score"], row["layer"]),
    )

    return {
        "scope": "shadbala_sapta_layer_hotspots",
        "schema_version": 1,
        "summary": {
            "case_count": len(cases),
            "row_count": len(rows),
            "global_closure_blocked": True,
            "top_layer": layer_hotspots[0]["layer"] if layer_hotspots else None,
        },
        "layer_hotspots": layer_hotspots,
        "driver_mix": dict(driver_mix),
        "rows": rows,
        "boundary": (
            "This hotspot table ranks Sapta Varga sublayers by their local score dominance so we can decide "
            "which dignity/friend-enemy mapping layer to audit first. It does not change oracle tolerances."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Sapta Varga layer hotspots for Shadbala")
    parser.add_argument("--oracle-file", default="references/oracle/dasha_shadbala_oracle_cases.json")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    report = build_report(args.oracle_file)
    if args.format == "markdown":
        lines = [
            "# Shadbala Sapta Layer Hotspots",
            "",
            f"- case_count: `{report['summary']['case_count']}`",
            f"- row_count: `{report['summary']['row_count']}`",
            f"- top_layer: `{report['summary']['top_layer']}`",
            "",
            "## Layer Hotspots",
            "",
            "| Layer | Avg Score | Max Score | Samples |",
            "| --- | ---: | ---: | ---: |",
        ]
        for row in report["layer_hotspots"]:
            lines.append(
                f"| {row['layer']} | {row['avg_score']} | {row['max_score']} | {row['sample_count']} |"
            )
        lines.extend([
            "",
            "## Driver Mix",
            "",
        ])
        for driver, count in sorted(report["driver_mix"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- `{driver}`: {count}")
        print("\n".join(lines))
        return

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
