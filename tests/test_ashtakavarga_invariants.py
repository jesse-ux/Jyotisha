#!/usr/bin/env python3
"""Ashtakavarga mathematical invariant tests."""

from __future__ import annotations

from ashtakavarga import ALL_SOURCES, BAV_TOTALS, EXPECTED_SAV_TOTAL, SEVEN_PLANETS, SIGNS, calc_ashtakavarga
from hypothesis import given, settings
from hypothesis import strategies as st


@st.composite
def planet_signs(draw: st.DrawFn) -> dict[str, dict[str, str]]:
    return {planet: {"sign": draw(st.sampled_from(SIGNS))} for planet in SEVEN_PLANETS}


@settings(deadline=None)
@given(planet_signs(), st.integers(min_value=0, max_value=11))
def test_ashtakavarga_totals_are_position_independent(planets: dict[str, dict[str, str]], asc_sign_idx: int) -> None:
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
