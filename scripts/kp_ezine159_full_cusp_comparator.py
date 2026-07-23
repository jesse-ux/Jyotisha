#!/usr/bin/env python3
"""Compare transcribed KP Ezine 159 cusp lord rows with VedicAstro raw.

The public source is treated as a partial worked example: eleven cusp rows have
usable sign/star/sub/sub-sub labels, but this is still observation-only and does
not validate KP timing or prediction claims.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FIELDS = ("RasiLord", "Nakshatra", "NakshatraLord", "SubLord", "SubSubLord")

TRANSCRIBED_ROWS: dict[int, dict[str, str]] = {
    1: {"Rasi": "Aquarius", "RasiLord": "Saturn", "Nakshatra": "Dhanishta", "NakshatraLord": "Mars", "SubLord": "Venus", "SubSubLord": "Ketu"},
    2: {"Rasi": "Pisces", "RasiLord": "Jupiter", "Nakshatra": "Revati", "NakshatraLord": "Mercury", "SubLord": "Mercury", "SubSubLord": "Ketu"},
    3: {"Rasi": "Aries", "RasiLord": "Mars", "Nakshatra": "Bharani", "NakshatraLord": "Venus", "SubLord": "Jupiter", "SubSubLord": "Jupiter"},
    4: {"Rasi": "Taurus", "RasiLord": "Venus", "Nakshatra": "Rohini", "NakshatraLord": "Moon", "SubLord": "Saturn", "SubSubLord": "Mercury"},
    5: {"Rasi": "Gemini", "RasiLord": "Mercury", "Nakshatra": "Ardra", "NakshatraLord": "Rahu", "SubLord": "Jupiter", "SubSubLord": "Saturn"},
    6: {"Rasi": "Cancer", "RasiLord": "Moon", "Nakshatra": "Pushya", "NakshatraLord": "Saturn", "SubLord": "Saturn", "SubSubLord": "Saturn"},
    7: {"Rasi": "Leo", "RasiLord": "Sun", "Nakshatra": "Maghā", "NakshatraLord": "Ketu", "SubLord": "Mars", "SubSubLord": "Rahu"},
    8: {"Rasi": "Virgo", "RasiLord": "Mercury", "Nakshatra": "Hasta", "NakshatraLord": "Moon", "SubLord": "Saturn", "SubSubLord": "Moon"},
    9: {"Rasi": "Libra", "RasiLord": "Venus", "Nakshatra": "Vishakha", "NakshatraLord": "Jupiter", "SubLord": "Jupiter", "SubSubLord": "Jupiter"},
    10: {"Rasi": "Scorpio", "RasiLord": "Mars", "Nakshatra": "Anuradha", "NakshatraLord": "Saturn", "SubLord": "Jupiter", "SubSubLord": "Sun"},
    11: {"Rasi": "Sagittarius", "RasiLord": "Jupiter", "Nakshatra": "Mula", "NakshatraLord": "Ketu", "SubLord": "Jupiter", "SubSubLord": "Rahu"},
}


def _houses_by_number(raw: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(row["HouseNr"]): row for row in raw["raw"]["houses"]}


def build_report(raw: dict[str, Any]) -> dict[str, Any]:
    houses = _houses_by_number(raw)
    comparisons = []
    for house_nr, expected in TRANSCRIBED_ROWS.items():
        observed = houses[house_nr]
        for field in FIELDS:
            comparisons.append(
                {
                    "house": house_nr,
                    "field": field,
                    "public_value": expected[field],
                    "vedicastro_value": observed.get(field),
                    "matches": observed.get(field) == expected[field],
                }
            )

    matched = sum(row["matches"] for row in comparisons)
    mismatched = len(comparisons) - matched

    return {
        "scope": "kp_ezine159_full_cusp_label_comparison",
        "status": (
            "public_kp_eleven_cusp_lord_rows_match_observation"
            if mismatched == 0
            else "public_kp_eleven_cusp_lord_rows_mismatch_observation"
        ),
        "claim_status": "observation_only",
        "consumer_policy": "research_observation_only",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "public_source": {
            "url": "https://www.scribd.com/document/462272035/KP-Ezine-159-April-2020",
            "source_boundary": "Publicly visible table rows were transcribed only for available cusp lord labels; this packet does not establish a complete numeric KP oracle.",
        },
        "summary": {
            "transcribed_cusp_count": len(TRANSCRIBED_ROWS),
            "matched_field_count": matched,
            "mismatched_field_count": mismatched,
            "untranscribed_cusps": [12],
        },
        "comparisons": comparisons,
        "claim_boundary": (
            "Eleven public cusp label rows agree with one isolated VedicAstro replay. "
            "Exact longitudes, the twelfth cusp row, software identity, full KP event "
            "significator workflow, and timing outcome validation remain blocked."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vedicastro-raw", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = build_report(json.loads(args.vedicastro_raw.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
