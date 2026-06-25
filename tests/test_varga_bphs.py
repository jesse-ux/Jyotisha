#!/usr/bin/env python3
"""Regression tests for BPHS divisional chart mappings."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st
from varga import SIGNS, calc_varga, varga_map


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


def test_varga_map_boundary_examples() -> None:
    assert varga_map(0, 0, 9) == 0  # Aries Navamsa starts Aries
    assert varga_map(1, 0, 9) == 9  # Taurus Navamsa starts Capricorn (9th from sign)
    assert varga_map(2, 0, 9) == 6  # Gemini Navamsa starts Libra (5th from sign)
    assert varga_map(1, 0, 10) == 9  # Taurus Dasamsa starts Capricorn
    assert varga_map(0, 2, 3) == 8  # Aries third Drekkana = Sagittarius


def test_navamsa_matches_user_jhora_pdf_reference_chart() -> None:
    """Regression from 印度占星1.pdf: JHora-style D9 table for REDACTED_DATE 14:45:20 Fengfeng."""
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
