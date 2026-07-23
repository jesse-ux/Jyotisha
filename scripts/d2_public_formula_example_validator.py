#!/usr/bin/env python3
"""Validate published D2 arithmetic examples against declared mapping variants.

This is method evidence only. It does not establish a canonical school, a
same-input external oracle, a wealth interpretation, or predictive accuracy.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from scripts.divisional_charts_extended import DivisionalChartsCalculator

SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# AstroAvastha publishes these four positions and their D2 sign outputs in its
# method explainer. They are examples of the stated parity rule, not a chart
# fixture or a software-oracle response.
PUBLISHED_EXAMPLES = (
    {"planet": "Jupiter", "sign": "Aries", "degree": 12.0, "expected_sign": "Leo"},
    {"planet": "Venus", "sign": "Taurus", "degree": 22.5, "expected_sign": "Leo"},
    {"planet": "Mars", "sign": "Scorpio", "degree": 8.25, "expected_sign": "Cancer"},
    {"planet": "Mercury", "sign": "Gemini", "degree": 17.75, "expected_sign": "Cancer"},
)

SOURCE = {
    "publisher": "AstroAvastha",
    "url": "https://astroavastha.com/blog/hora-d2-chart/",
    "tier": "secondary_method_reference",
    "supports": "Published arithmetic examples for the odd/even-sign Leo/Cancer D2 mapping.",
    "does_not_support": "Canonical-school selection, software identity, same-input oracle parity, wealth outcomes, or timing.",
}


def local_parashara_d2_sign(sign: str, degree: float) -> str:
    """Return the D2 sign from the project's active divisional-chart calculator."""
    sign_index = SIGNS.index(sign)
    d2_longitude = DivisionalChartsCalculator()._calculate_d2(sign_index, degree)
    return SIGNS[int(d2_longitude // 30.0) % 12]


def jyotishyamitra_sequential_d2_sign(sign: str, degree: float) -> str:
    """Return the sequential 15-degree rule observed in the pinned source."""
    absolute_degree = SIGNS.index(sign) * 30.0 + degree
    return SIGNS[int(absolute_degree // 15.0) % 12]


def build_report() -> dict:
    examples = []
    for source_row in PUBLISHED_EXAMPLES:
        local_result = local_parashara_d2_sign(source_row["sign"], source_row["degree"])
        sequential_result = jyotishyamitra_sequential_d2_sign(source_row["sign"], source_row["degree"])
        examples.append({
            **source_row,
            "local_parashara_result": local_result,
            "local_engine_source": "scripts.divisional_charts_extended.DivisionalChartsCalculator._calculate_d2",
            "jyotishyamitra_sequential_result": sequential_result,
            "local_parashara_matches": local_result == source_row["expected_sign"],
            "jyotishyamitra_sequential_matches": sequential_result == source_row["expected_sign"],
        })

    return {
        "scope": "public_secondary_d2_formula_examples",
        "generated_on": date.today().isoformat(),
        "status": "secondary_formula_examples_support_local_parashara_mapping",
        "claim_status": "observation_only",
        "consumer_policy": "research_observation_only",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "source": SOURCE,
        "variants": {
            "local_parashara": "Odd signs: 0-<15 Leo, 15-<30 Cancer; even signs invert that order.",
            "jyotishyamitra_sequential": "Sequential 15-degree chunks across absolute zodiac, observed in support/mod_divisional.py::hora_from_long.",
        },
        "examples": examples,
        "summary": {
            "example_count": len(examples),
            "local_parashara_match_count": sum(row["local_parashara_matches"] for row in examples),
            "jyotishyamitra_sequential_match_count": sum(row["jyotishyamitra_sequential_matches"] for row in examples),
        },
        "claim_boundary": (
            "These publisher-stated arithmetic examples support the project's declared Parashara-style D2 mapping "
            "over the observed sequential alternative for this limited example set. They do not create an external "
            "software oracle, settle all Hora traditions, validate a birth chart, or support wealth/timing claims."
        ),
        "remaining_requirements": [
            "A same-input, independently reproducible D2 software replay with documented settings.",
            "A primary or scholarly source that identifies the intended Hora tradition and boundary convention.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_report(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
