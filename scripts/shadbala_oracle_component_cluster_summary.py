#!/usr/bin/env python3
"""Cluster Shadbala oracle deltas to identify the narrowest closure target."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from scripts.shadbala_oracle_batch_summary import _discover_case_ids, _load_oracle
from scripts.shadbala_oracle_comparison import compare_case


ROOT = Path(__file__).resolve().parents[1]


def _safe_avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def build_report(oracle_file: str) -> dict[str, Any]:
    oracle = _load_oracle(oracle_file)
    case_ids = _discover_case_ids(oracle)

    component_deltas: dict[str, list[float]] = defaultdict(list)
    planet_deltas: dict[str, list[float]] = defaultdict(list)
    case_count = 0
    planet_count = 0

    for case_id in case_ids:
        report = compare_case(oracle_file=oracle_file, case_id=case_id)
        case_count += 1
        for planet, row in report.get("comparison", {}).items():
            total_abs = row.get("abs_diff_total_rupa")
            if isinstance(total_abs, (int, float)):
                planet_deltas[planet].append(float(total_abs))
            planet_count = max(planet_count, len(report.get("comparison", {})))
            for component, component_row in (row.get("components") or {}).items():
                abs_diff = component_row.get("abs_diff_rupa")
                if isinstance(abs_diff, (int, float)):
                    component_deltas[component].append(float(abs_diff))

    component_hotspots = sorted(
        [
            {
                "component": component,
                "avg_abs_diff_rupa": _safe_avg(values),
                "max_abs_diff_rupa": round(max(values), 4),
                "sample_count": len(values),
            }
            for component, values in component_deltas.items()
            if values
        ],
        key=lambda row: (-row["avg_abs_diff_rupa"], -row["max_abs_diff_rupa"], row["component"]),
    )

    planet_hotspots = sorted(
        [
            {
                "planet": planet,
                "avg_abs_total_delta_rupa": _safe_avg(values),
                "max_abs_total_delta_rupa": round(max(values), 4),
                "sample_count": len(values),
            }
            for planet, values in planet_deltas.items()
            if values
        ],
        key=lambda row: (-row["avg_abs_total_delta_rupa"], -row["max_abs_total_delta_rupa"], row["planet"]),
    )

    top_component = component_hotspots[0]["component"] if component_hotspots else None
    targeted_fix = (
        f"Prioritize {top_component} component reconciliation before touching global scaling or unrelated layers."
        if top_component
        else "No hotspot identified."
    )

    return {
        "scope": "shadbala_oracle_component_cluster_summary",
        "schema_version": 1,
        "summary": {
            "case_count": case_count,
            "planet_count": planet_count,
            "global_closure_blocked": True,
            "targeted_fix_recommendation": targeted_fix,
        },
        "component_hotspots": component_hotspots,
        "planet_hotspots": planet_hotspots,
        "boundary": (
            "This report clusters absolute Shadbala delta hotspots across all external_verified cases. "
            "It reuses the existing comparison pipeline and narrows closure work to the most divergent component first."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Shadbala component hotspots across oracle cases")
    parser.add_argument("--oracle-file", default="references/oracle/dasha_shadbala_oracle_cases.json")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    report = build_report(args.oracle_file)
    if args.format == "markdown":
        lines = [
            "# Shadbala Oracle Component Cluster Summary",
            "",
            f"- case_count: `{report['summary']['case_count']}`",
            f"- planet_count: `{report['summary']['planet_count']}`",
            f"- global_closure_blocked: `{str(report['summary']['global_closure_blocked']).lower()}`",
            f"- targeted_fix_recommendation: `{report['summary']['targeted_fix_recommendation']}`",
            "",
            "## Component Hotspots",
            "",
            "| Component | Avg Abs Diff (Rupa) | Max Abs Diff | Samples |",
            "| --- | ---: | ---: | ---: |",
        ]
        for row in report["component_hotspots"]:
            lines.append(
                f"| {row['component']} | {row['avg_abs_diff_rupa']} | {row['max_abs_diff_rupa']} | {row['sample_count']} |"
            )
        lines.extend([
            "",
            "## Planet Hotspots",
            "",
            "| Planet | Avg Abs Total Delta (Rupa) | Max Abs Delta | Samples |",
            "| --- | ---: | ---: | ---: |",
        ])
        for row in report["planet_hotspots"]:
            lines.append(
                f"| {row['planet']} | {row['avg_abs_total_delta_rupa']} | {row['max_abs_total_delta_rupa']} | {row['sample_count']} |"
            )
        print("\n".join(lines))
        return

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
