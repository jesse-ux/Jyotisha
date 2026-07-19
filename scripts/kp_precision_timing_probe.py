#!/usr/bin/env python3
"""Minimal KP star/sub-lord + significator probe.

This is a probe artifact, not a timing oracle.  It reuses the local
`kp_system.py` implementation and keeps exact event timing blocked until
external examples and negative holdout validation exist.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from kp_system import calc_kp_analysis


ROOT = Path(__file__).resolve().parents[1]


CANONICAL_PLANETS = {
    "Sun": {"sign": "Aries", "degree": 10.0, "house": 1},
    "Moon": {"sign": "Taurus", "degree": 5.0, "house": 2},
    "Mars": {"sign": "Gemini", "degree": 18.0, "house": 3},
    "Mercury": {"sign": "Pisces", "degree": 22.0, "house": 12},
    "Jupiter": {"sign": "Cancer", "degree": 12.0, "house": 4},
    "Venus": {"sign": "Aquarius", "degree": 27.0, "house": 11},
    "Saturn": {"sign": "Capricorn", "degree": 3.0, "house": 10},
    "Rahu": {"sign": "Scorpio", "degree": 17.0, "house": 8},
    "Ketu": {"sign": "Taurus", "degree": 17.0, "house": 2},
}


def _stable_hash(data: Any) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_probe() -> dict[str, Any]:
    raw = calc_kp_analysis(CANONICAL_PLANETS, asc_sign="Aries")
    planets = raw.get("planets", {})
    houses = raw.get("houses", {})
    kp_lords_by_planet = {
        planet: value.get("kp_lords", {})
        for planet, value in sorted(planets.items())
    }
    planet_significators = {
        planet: value.get("significators", {})
        for planet, value in sorted(planets.items())
    }
    house_significators = {
        str(house): value.get("significators", {})
        for house, value in sorted(houses.items(), key=lambda item: int(item[0]))
    }
    return {
        "scope": "kp_star_sub_lord_significator_probe",
        "created_at": "2026-07-19",
        "production_tuning_allowed": False,
        "claim_status": "probe_only_not_timing_truth",
        "external_oracle_status": "partial_sublord_csv_only",
        "negative_holdout_status": "missing",
        "input_contract": {
            "planet_format": "{planet: {sign, degree_in_sign, house}}",
            "asc_sign": "Aries",
            "ayanamsa": "caller_supplied_sidereal_positions",
            "house_contract": "whole-sign house probe, not precise KP cusp oracle",
        },
        "local_reuse": {
            "module": "scripts/kp_system.py",
            "functions": ["calc_kp_analysis", "get_kp_lords", "get_planet_significators", "get_house_significators"],
            "license_boundary": "Local implementation cites diliprk/VedicAstro MIT; keep source/oracle audit before commercial precise timing.",
        },
        "kp_lords_by_planet": kp_lords_by_planet,
        "planet_significators": planet_significators,
        "house_significators": house_significators,
        "raw_sha256": _stable_hash(raw),
        "claim_boundary": "This probe can expose KP star/sub-lord and significator fields, but cannot drive precise event timing without exact KP cusp oracle and independent negative holdout validation.",
    }


def main() -> int:
    print(json.dumps(build_probe(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
