#!/usr/bin/env python3
"""Ashtakavarga mathematical invariant tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ashtakavarga import (
    ALL_SOURCES,
    BAV_TOTALS,
    EXPECTED_SAV_TOTAL,
    SEVEN_PLANETS,
    SIGNS,
    calc_ashtakavarga,
    calc_prastara_av,
    calc_yoga_pinda,
)


def _planet_signs(offset: int = 0, step: int = 1) -> dict[str, dict[str, str]]:
    return {planet: {"sign": SIGNS[(offset + index * step) % 12]} for index, planet in enumerate(SEVEN_PLANETS)}


def test_ashtakavarga_totals_are_position_independent() -> None:
    samples = [
        (_planet_signs(offset=0, step=1), 0),
        (_planet_signs(offset=2, step=3), 4),
        (_planet_signs(offset=7, step=5), 11),
    ]
    for planets, asc_sign_idx in samples:
        result = calc_ashtakavarga(planets, asc_sign_idx)

        assert result["sav"]["total"] == EXPECTED_SAV_TOTAL
        assert result["sav"]["valid"] is True
        assert result["sav"]["full_total_with_lagna"] == EXPECTED_SAV_TOTAL + BAV_TOTALS["Lagna"]
        assert result["all_bav_valid"] is True

        for planet in ALL_SOURCES:
            assert result["bav"][planet]["total"] == BAV_TOTALS[planet]
            assert result["bav"][planet]["valid"] is True


def test_ashtakavarga_output_contract() -> None:
    planets = {planet: {"sign": SIGNS[index % 12]} for index, planet in enumerate(SEVEN_PLANETS)}
    result = calc_ashtakavarga(planets, asc_sign_idx=0)

    assert result["method"] == "Ashtakavarga八分法（BPHS/PVR书例校准v2.1）"
    assert result["version"] == "2.1"
    assert set(result["sav"]["scores"].keys()) == set(SIGNS)
    assert len(result["house_scores"]) == 12
    assert len(result["house_scores_full"]) == 12


def test_prastara_matrix_reconstructs_each_planets_bav() -> None:
    planets = {planet: {"sign": SIGNS[(index * 2) % 12]} for index, planet in enumerate(SEVEN_PLANETS)}
    result = calc_ashtakavarga(planets, asc_sign_idx=3)
    pav = calc_prastara_av(planets, asc_sign_idx=3)

    assert pav["all_valid"] is True
    assert pav["matrix_shape"] == {"planets": 7, "signs": 12, "sources": 8}

    for planet in SEVEN_PLANETS:
        reconstructed = [0] * 12
        for source in ALL_SOURCES:
            for index, value in enumerate(pav["pav"][planet][source]):
                reconstructed[index] += value
        assert reconstructed == result["bav"][planet]["bindus"]


def test_yoga_pinda_is_first_class_contract() -> None:
    planets = {planet: {"sign": SIGNS[(index * 3) % 12]} for index, planet in enumerate(SEVEN_PLANETS)}
    result = calc_ashtakavarga(planets, asc_sign_idx=5)
    yoga_pinda = calc_yoga_pinda(result["bav"], planets, asc_sign_idx=5)

    assert yoga_pinda["method"] == "Yoga Pinda"
    assert yoga_pinda["all_valid"] is True
    assert yoga_pinda["summary"]["strongest_planet"] in SEVEN_PLANETS
    assert yoga_pinda["summary"]["total_yoga_pinda"] == sum(
        item["yoga_pinda"] for item in yoga_pinda["planets"].values()
    )

    for planet in SEVEN_PLANETS:
        row = yoga_pinda["planets"][planet]
        legacy = result["shodhya_pinda"][planet]
        assert row["rashi_pinda"] == legacy["rashi_pinda"]
        assert row["graha_pinda"] == legacy["graha_pinda"]
        assert row["yoga_pinda"] == legacy["total_pinda"]
        assert row["bindu_at_own_sign"] == legacy["bindu_at_own_sign"]
