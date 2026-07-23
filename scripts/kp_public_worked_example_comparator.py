#!/usr/bin/env python3
"""Compare one public KP cusp row with an isolated VedicAstro observation.

This is a field-level observation. It must not be promoted to verified KP
timing, prediction, or truth-matrix evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPECTED: dict[str, Any] = {
    "HouseNr": 5,
    "LonDecDeg": 69 + 7 / 60 + 14 / 3600,
    "Rasi": "Gemini",
    "RasiLord": "Mercury",
    "Nakshatra": "Ardra",
    "NakshatraLord": "Rahu",
    "SubLord": "Jupiter",
    "SubSubLord": "Saturn",
}
PUBLIC_AYANAMSA_DEGREES = 23 + 32 / 60 + 29 / 3600

COMPARABLE_FIELDS = (
    "Rasi",
    "RasiLord",
    "Nakshatra",
    "NakshatraLord",
    "SubLord",
    "SubSubLord",
)
LONGITUDE_TOLERANCE_ARCSECONDS = 60.0


def _find_house(raw: dict[str, Any], house_number: int) -> dict[str, Any]:
    for house in raw.get("raw", {}).get("houses", []):
        if house.get("HouseNr") == house_number:
            return house
    raise ValueError(f"Missing house {house_number}")


def build_report(observed_house: dict[str, Any], observed_ayanamsa_degrees: float | None = None) -> dict[str, Any]:
    delta_arcseconds = round(
        abs(float(observed_house["LonDecDeg"]) - EXPECTED["LonDecDeg"]) * 3600,
        1,
    )
    field_comparisons = [
        {
            "field": field,
            "public_value": EXPECTED[field],
            "vedicastro_value": observed_house.get(field),
            "matches": observed_house.get(field) == EXPECTED[field],
        }
        for field in COMPARABLE_FIELDS
    ]
    matched_count = sum(row["matches"] for row in field_comparisons)
    longitude_within_tolerance = delta_arcseconds <= LONGITUDE_TOLERANCE_ARCSECONDS
    ayanamsa_delta_arcseconds = (
        round(abs(observed_ayanamsa_degrees - PUBLIC_AYANAMSA_DEGREES) * 3600, 1)
        if observed_ayanamsa_degrees is not None
        else None
    )

    return {
        "scope": "kp_public_worked_example_field_comparison",
        "status": (
            "public_kp_worked_example_partial_field_match"
            if matched_count == len(field_comparisons) and longitude_within_tolerance
            else "public_kp_worked_example_field_mismatch"
        ),
        "claim_status": "observation_only",
        "consumer_policy": "research_observation_only",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "public_source": {
            "url": "https://www.scribd.com/document/462272035/KP-Ezine-159-April-2020",
            "source_lines": [2775, 2782, 2800, 2807, 2816, 2859, 2869],
            "case_boundary": (
                "The public page supplies one 5th-cusp row and case settings; "
                "it is not a full independent timing validation."
            ),
        },
        "public_case": {
            "birth": "1983-11-04 14:04:00, Brunswick, Georgia, USA",
            "coordinates": "31N08, 81W30",
            "timezone": "UTC-05:00, DST 0",
            "ayanamsa": "KP Ayanamsa / KP New value printed as 23°32'29\"",
            "house_system": "Placidus",
            "expected_fifth_cusp": EXPECTED,
        },
        "comparison": {
            "longitude_delta_arcseconds": delta_arcseconds,
            "longitude_tolerance_arcseconds": LONGITUDE_TOLERANCE_ARCSECONDS,
            "longitude_within_tolerance": longitude_within_tolerance,
            "public_ayanamsa_degrees": PUBLIC_AYANAMSA_DEGREES,
            "vedicastro_ayanamsa_degrees": observed_ayanamsa_degrees,
            "ayanamsa_delta_arcseconds": ayanamsa_delta_arcseconds,
            "field_comparisons": field_comparisons,
        },
        "summary": {
            "matched_field_count": matched_count,
            "mismatched_field_count": len(field_comparisons) - matched_count,
            "longitude_within_tolerance": longitude_within_tolerance,
        },
        "claim_boundary": (
            "The source's fifth-cusp sign, star, sub and sub-sub labels agree with "
            "this isolated VedicAstro replay, and the cusp longitude differs by less "
            "than one arcminute. The printed KP New and replayed Krishnamurti ayanamsa "
            "also differ by 43 arcseconds, so they must not be treated as identical. "
            "This does not identify hosted VedAstro, validate remaining cusps or "
            "sub-sub-sub values, or validate timing/predictions."
        ),
        "remaining_requirements": [
            "A source or software identity proving the exact KP New ayanamsa implementation used by the public table.",
            "Complete multi-cusp and planet rows with independent reproduction before exact KP timing claims.",
            "Independent outcome holdout; no prediction claim follows from one technical row.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vedicastro-raw", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw = json.loads(args.vedicastro_raw.read_text(encoding="utf-8"))
    observed_ayanamsa = raw.get("raw", {}).get("ayanamsa_identity", {}).get("value_degrees")
    report = build_report(_find_house(raw, 5), observed_ayanamsa_degrees=observed_ayanamsa)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
