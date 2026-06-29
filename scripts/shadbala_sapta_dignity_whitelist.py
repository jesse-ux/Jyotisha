#!/usr/bin/env python3
"""Build a minimal whitelist of Sapta dignity mappings most likely causing drift."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.shadbala_sapta_layer_hotspots import build_report as build_hotspot_report


ROOT = Path(__file__).resolve().parents[1]
TARGET_LAYERS = {"D7", "D12", "D3", "D4"}
TARGET_DRIVERS = {"dignity_exalted": "exalted", "dignity_own": "own"}


def build_report(oracle_file: str) -> dict[str, Any]:
    hotspot = build_hotspot_report(oracle_file)
    whitelist_rows = []
    layer_counts: Counter[str] = Counter()

    for row in hotspot.get("rows", []):
        layer = row.get("dominant_layer")
        driver = row.get("driver_guess")
        if layer not in TARGET_LAYERS:
            continue
        if driver not in TARGET_DRIVERS:
            continue
        whitelist_rows.append({
            "case_id": row["case_id"],
            "planet": row["planet"],
            "layer": layer,
            "dignity_type": TARGET_DRIVERS[driver],
            "dominant_layer_score": row["dominant_layer_score"],
            "driver_guess": driver,
        })
        layer_counts[layer] += 1

    whitelist_rows.sort(
        key=lambda row: (-row["dominant_layer_score"], row["layer"], row["case_id"], row["planet"])
    )

    return {
        "scope": "shadbala_sapta_dignity_whitelist",
        "schema_version": 1,
        "summary": {
            "case_count": hotspot.get("summary", {}).get("case_count", 0),
            "global_closure_blocked": True,
            "whitelist_count": len(whitelist_rows),
        },
        "layer_counts": dict(layer_counts),
        "whitelist_rows": whitelist_rows,
        "boundary": (
            "This whitelist isolates D7/D12/D3/D4 exalted-or-own dignity mappings that appear as dominant Sapta "
            "drivers. It is a repair whitelist, not proof of final oracle closure."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Sapta dignity whitelist for Shadbala repair")
    parser.add_argument("--oracle-file", default="references/oracle/dasha_shadbala_oracle_cases.json")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    report = build_report(args.oracle_file)
    if args.format == "markdown":
        lines = [
            "# Shadbala Sapta Dignity Whitelist",
            "",
            f"- case_count: `{report['summary']['case_count']}`",
            f"- whitelist_count: `{report['summary']['whitelist_count']}`",
            "",
            "| Layer | Dignity | Planet | Case | Score |",
            "| --- | --- | --- | --- | ---: |",
        ]
        for row in report["whitelist_rows"]:
            lines.append(
                f"| {row['layer']} | {row['dignity_type']} | {row['planet']} | {row['case_id']} | {row['dominant_layer_score']} |"
            )
        print("\n".join(lines))
        return

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
