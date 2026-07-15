#!/usr/bin/env python3
"""Regression tests for BPHS divisional chart mappings."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st
from varga import (
    SIGNS,
    calc_bhrigu_bindu,
    calc_22nd_drekkana,
    calc_64th_navamsa,
    calc_sarpa_drekkana,
    calc_varga,
    varga_map,
)


def navamsa_ref(lon: float) -> int:
    sign_index = int((lon % 360) / 30) % 12
    degree_in_sign = (lon % 360) - sign_index * 30
    part_index = int(degree_in_sign / (30 / 9))
    if sign_index % 3 == 0:
        start = sign_index
    elif sign_index % 3 == 1:
        start = (sign_index + 8) % 12
    else:
        start = (sign_index + 4) % 12
    return (start + part_index) % 12


def dasamsa_ref(lon: float) -> int:
    sign_index = int((lon % 360) / 30) % 12
    degree_in_sign = (lon % 360) - sign_index * 30
    part_index = int(degree_in_sign / 3)
    start = sign_index if sign_index % 2 == 0 else (sign_index + 8) % 12
    return (start + part_index) % 12


def drekkana_ref(lon: float) -> int:
    sign_index = int((lon % 360) / 30) % 12
    degree_in_sign = (lon % 360) - sign_index * 30
    part_index = int(degree_in_sign / 10)
    return (sign_index + part_index * 4) % 12


def chaturthamsa_ref(lon: float) -> int:
    sign_index = int((lon % 360) / 30) % 12
    degree_in_sign = (lon % 360) - sign_index * 30
    part_index = int(degree_in_sign / (30 / 4))
    return (sign_index + part_index * 3) % 12


@given(st.floats(min_value=0, max_value=359.999999, allow_nan=False, allow_infinity=False))
def test_navamsa_matches_bphs_reference(lon: float) -> None:
    result = calc_varga(lon, 9)
    assert result["sign_idx"] == navamsa_ref(lon)
    assert result["sign"] == SIGNS[navamsa_ref(lon)]
    assert 0 <= result["degree_in_sign"] < 30


@given(st.floats(min_value=0, max_value=359.999999, allow_nan=False, allow_infinity=False))
def test_dasamsa_matches_bphs_reference(lon: float) -> None:
    result = calc_varga(lon, 10)
    assert result["sign_idx"] == dasamsa_ref(lon)
    assert result["sign"] == SIGNS[dasamsa_ref(lon)]
    assert 0 <= result["degree_in_sign"] < 30


@given(st.floats(min_value=0, max_value=359.999999, allow_nan=False, allow_infinity=False))
def test_drekkana_uses_same_plus_four_plus_eight(lon: float) -> None:
    result = calc_varga(lon, 3)
    assert result["sign_idx"] == drekkana_ref(lon)


@given(st.floats(min_value=0, max_value=359.999999, allow_nan=False, allow_infinity=False))
def test_chaturthamsa_matches_pyjhora_parashara_reference(lon: float) -> None:
    result = calc_varga(lon, 4)
    assert result["sign_idx"] == chaturthamsa_ref(lon)
    assert result["sign"] == SIGNS[chaturthamsa_ref(lon)]
    assert 0 <= result["degree_in_sign"] < 30


def test_chaturthamsa_reference_boundary_examples() -> None:
    assert [varga_map(0, part, 4) for part in range(4)] == [0, 3, 6, 9]
    assert [varga_map(8, part, 4) for part in range(4)] == [8, 11, 2, 5]
    assert [varga_map(11, part, 4) for part in range(4)] == [11, 2, 5, 8]


def test_varga_map_boundary_examples() -> None:
    assert varga_map(0, 0, 9) == 0  # Aries Navamsa starts Aries
    assert varga_map(1, 0, 9) == 9  # Taurus Navamsa starts Capricorn (9th from sign)
    assert varga_map(2, 0, 9) == 6  # Gemini Navamsa starts Libra (5th from sign)
    assert varga_map(1, 0, 10) == 9  # Taurus Dasamsa starts Capricorn
    assert varga_map(0, 2, 3) == 8  # Aries third Drekkana = Sagittarius


def test_navamsa_matches_user_jhora_pdf_reference_chart() -> None:
    """Regression from private_chart_reference.pdf: JHora-style D9 table for public sample birth datetime San Francisco."""
    expected = {
        132.355025: "Cancer",      # Ascendant 12 Leo 21'18.09"
        3.5226611111111112: "Taurus",
        311.78995555555554: "Capricorn",
        91.33091388888889: "Cancer",
        338.5488: "Virgo",
        163.83150833333335: "Taurus",
        340.5554638888889: "Libra",
        304.3033805555556: "Scorpio",
        231.04509444444443: "Capricorn",
        51.045094444444445: "Cancer",
    }
    for longitude, expected_sign in expected.items():
        assert calc_varga(longitude, 9)["sign"] == expected_sign


def test_64th_navamsa_counts_forward_from_moon_navamsa() -> None:
    moon_lon = 42.3
    result = calc_64th_navamsa(moon_lon)
    expected_sign_idx = (navamsa_ref(moon_lon) + 63) % 12
    assert result["sign_idx"] == expected_sign_idx
    assert result["sign"] == SIGNS[expected_sign_idx]
    assert result["offset_from_moon_navamsa"] == 64


def test_22nd_drekkana_counts_forward_from_lagna_drekkana() -> None:
    asc_lon = 25.5
    result = calc_22nd_drekkana(asc_lon)
    expected_sign_idx = (drekkana_ref(asc_lon) + 21) % 12
    assert result["sign_idx"] == expected_sign_idx
    assert result["sign"] == SIGNS[expected_sign_idx]
    assert result["offset_from_lagna_drekkana"] == 22


def test_bhrigu_bindu_uses_rahu_to_moon_arc_midpoint() -> None:
    result = calc_bhrigu_bindu(270.5, 160.2333333333)
    assert result["longitude"] == 215.3667
    assert result["sign"] == "Scorpio"
    assert result["degree_in_sign"] == 5.3667


def test_bhrigu_bindu_handles_wraparound_across_zero_aries() -> None:
    result = calc_bhrigu_bindu(10.0, 350.0)
    assert result["longitude"] == 0.0
    assert result["sign"] == "Aries"
    assert result["degree_in_sign"] == 0.0


def test_sarpa_drekkana_detects_classical_sensitive_ranges() -> None:
    cancer_second = calc_sarpa_drekkana(105.0)
    scorpio_first = calc_sarpa_drekkana(215.0)
    pisces_third = calc_sarpa_drekkana(355.0)
    safe_aries = calc_sarpa_drekkana(15.0)

    assert cancer_second["is_sarpa_drekkana"] is True
    assert cancer_second["sign"] == "Cancer"
    assert cancer_second["drekkana_number"] == 2

    assert scorpio_first["is_sarpa_drekkana"] is True
    assert scorpio_first["sign"] == "Scorpio"
    assert scorpio_first["drekkana_number"] == 1

    assert pisces_third["is_sarpa_drekkana"] is True
    assert pisces_third["sign"] == "Pisces"
    assert pisces_third["drekkana_number"] == 3

    assert safe_aries["is_sarpa_drekkana"] is False
