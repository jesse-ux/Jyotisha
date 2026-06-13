#!/usr/bin/env python3
"""Tests for divisional_charts_extended module — D2 variants, D3 variants,
composite vargas, custom D-N, and list_available_variants."""

from __future__ import annotations

import sys
import os
import pytest

# Add scripts dir to path
SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from divisional_charts_extended import DivisionalChartsCalculator, VargaType

calc = DivisionalChartsCalculator()


# ── D2 Hora Variant Tests ──────────────────────────────────────────

D2_VARIANTS = ['parashara', 'pariveshta', 'parivritta',
               'parivritta_trayodamsa', 'surya_chandra', 'ahoratra']


@pytest.mark.parametrize("variant", D2_VARIANTS)
def test_d2_variant_returns_valid_longitude(variant):
    """Each D2 variant must return a longitude in [0, 360)."""
    lon = calc._calculate_d2_variant(0, 15.5, variant)
    assert 0 <= lon < 360, f"{variant}: lon={lon} out of range"


@pytest.mark.parametrize("variant", D2_VARIANTS)
def test_d2_variant_sign_is_leo_or_cancer_for_odd_first_half(variant):
    """For Aries (odd) 0-15 degrees, Parashara/Surya/Chandra/Ahoratra → Leo."""
    if variant in ('parashara', 'surya_chandra', 'ahoratra'):
        lon = calc._calculate_d2_variant(0, 5.0, variant)
        sign_idx = int(lon // 30)
        assert sign_idx == 4, f"{variant}: expected Leo (4), got {calc.SIGNS[sign_idx]}"


@pytest.mark.parametrize("variant", D2_VARIANTS)
def test_d2_variant_second_half_odd_sign(variant):
    """For Aries (odd) 15-30 degrees, Parashara → Cancer."""
    if variant in ('parashara', 'surya_chandra', 'ahoratra'):
        lon = calc._calculate_d2_variant(0, 20.0, variant)
        sign_idx = int(lon // 30)
        assert sign_idx == 3, f"{variant}: expected Cancer (3), got {calc.SIGNS[sign_idx]}"


def test_d2_pariveshta_first_half_same_sign():
    """Pariveshta: first half stays in same sign."""
    lon = calc._calculate_d2_variant(0, 5.0, 'pariveshta')
    assert int(lon // 30) == 0  # Aries


def test_d2_pariveshta_second_half_next_sign():
    """Pariveshta: second half goes to next sign."""
    lon = calc._calculate_d2_variant(0, 20.0, 'pariveshta')
    assert int(lon // 30) == 1  # Taurus


def test_d2_parivritta_even_sign_reverses():
    """Parivritta: even signs reverse degree order."""
    lon = calc._calculate_d2_variant(1, 5.0, 'parivritta')  # Taurus even, first half
    sign_idx = int(lon // 30)
    assert sign_idx == 3  # Cancer for even first half


def test_d2_trayodamsa_13_divisions():
    """Parivritta-Trayodamsa: 13 divisions produce different signs."""
    results = set()
    for deg in range(0, 30, 2):
        lon = calc._calculate_d2_variant(0, float(deg), 'parivritta_trayodamsa')
        results.add(int(lon // 30))
    assert len(results) > 1, "Should produce more than 1 sign across 13 parts"


def test_d2_unknown_variant_raises():
    """Unknown D2 variant should raise ValueError."""
    with pytest.raises(ValueError, match="Unknown D2 variant"):
        calc._calculate_d2_variant(0, 15.0, 'nonexistent')


# ── D3 Drekkana Variant Tests ──────────────────────────────────────

D3_VARIANTS = ['parashara', 'parivritta_trayodamsa', 'somaja', 'khara']


@pytest.mark.parametrize("variant", D3_VARIANTS)
def test_d3_variant_returns_valid_longitude(variant):
    lon = calc._calculate_d3_variant(0, 15.0, variant)
    assert 0 <= lon < 360


def test_d3_parashara_first_drekkana_same_sign():
    """First 10° of Aries stays in Aries."""
    lon = calc._calculate_d3_variant(0, 5.0, 'parashara')
    assert int(lon // 30) == 0  # Aries


def test_d3_parashara_second_drekkana_plus4():
    """10-20° of Aries → 5th sign (Leo)."""
    lon = calc._calculate_d3_variant(0, 15.0, 'parashara')
    assert int(lon // 30) == 4  # Leo


def test_d3_parashara_third_drekkana_plus8():
    """20-30° of Aries → 9th sign (Sagittarius)."""
    lon = calc._calculate_d3_variant(0, 25.0, 'parashara')
    assert int(lon // 30) == 8  # Sagittarius


def test_d3_somaja_moon_signs():
    """Somaja always maps to Cancer/Scorpio/Pisces."""
    for deg in [5.0, 15.0, 25.0]:
        lon = calc._calculate_d3_variant(0, deg, 'somaja')
        sign_idx = int(lon // 30)
        assert sign_idx in (3, 7, 11), f"Expected Cancer/Scorpio/Pisces, got {calc.SIGNS[sign_idx]}"


def test_d3_khara_even_sign_offset():
    """Khara: even signs use +5 offset for first drekkana."""
    lon = calc._calculate_d3_variant(1, 5.0, 'khara')  # Taurus, 1st drekkana
    sign_idx = int(lon // 30)
    assert sign_idx == (1 + 5) % 12  # Virgo


def test_d3_unknown_variant_raises():
    with pytest.raises(ValueError, match="Unknown D3 variant"):
        calc._calculate_d3_variant(0, 15.0, 'nonexistent')


# ── Composite Varga Tests ──────────────────────────────────────────

def test_composite_d9_d12_equals_d108():
    """D9×D12 composite should produce consistent sign."""
    result = calc.calc_composite_varga(45.0, 9, 12)
    assert result['composite_div'] == 108
    assert 'sign' in result
    assert 0 <= result['sign_idx'] < 12


def test_composite_d12_d12_equals_d144():
    result = calc.calc_composite_varga(45.0, 12, 12)
    assert result['composite_div'] == 144


def test_composite_d9_d9_equals_d81():
    result = calc.calc_composite_varga(45.0, 9, 9)
    assert result['composite_div'] == 81


def test_composite_intermediate_preserved():
    """Composite should preserve intermediate outer result."""
    result = calc.calc_composite_varga(45.0, 9, 12)
    assert 'intermediate' in result
    assert 'outer_sign' in result['intermediate']


# ── Custom D-N Tests ───────────────────────────────────────────────

def test_custom_d150_valid():
    result = calc.calc_custom_varga(45.0, 150)
    assert result['div'] == 150
    assert 0 <= result['sign_idx'] < 12


def test_custom_d300_valid():
    result = calc.calc_custom_varga(45.0, 300)
    assert result['div'] == 300
    assert 0 <= result['sign_idx'] < 12


def test_custom_d9_matches_standard():
    """Custom D9 should match standard D9 calculation."""
    custom = calc.calc_custom_varga(45.0, 9)
    standard = calc._calculate_varga_position(45.0, 9)
    assert custom['sign_idx'] == int(standard // 30)


def test_custom_d2_matches_standard():
    custom = calc.calc_custom_varga(30.0, 2)
    standard = calc._calculate_varga_position(30.0, 2)
    assert custom['sign_idx'] == int(standard // 30)


def test_custom_out_of_range_raises():
    with pytest.raises(ValueError, match="2-300"):
        calc.calc_custom_varga(45.0, 1)
    with pytest.raises(ValueError, match="2-300"):
        calc.calc_custom_varga(45.0, 301)


def test_custom_amsa_size():
    """Amsa size should be 30/N."""
    result = calc.calc_custom_varga(45.0, 150)
    assert abs(result['amsa_size'] - 30.0 / 150) < 0.001


# ── calc_varga_with_variant Tests ──────────────────────────────────

def test_varga_with_d2_variant():
    result = calc.calc_varga_with_variant(15.5, 2, 'pariveshta')
    assert result['variant'] == 'pariveshta'
    assert result['div'] == 2


def test_varga_without_variant_uses_parashara():
    result = calc.calc_varga_with_variant(15.5, 9, None)
    assert result['variant'] == 'parashara'


def test_varga_d3_variant():
    result = calc.calc_varga_with_variant(15.0, 3, 'somaja')
    assert result['variant'] == 'somaja'


# ── list_available_variants Tests ───────────────────────────────────

def test_list_available_variants_structure():
    variants = calc.list_available_variants()
    assert 'D2' in variants
    assert 'D3' in variants
    assert 'composite' in variants
    assert 'custom' in variants


def test_list_d2_has_six_variants():
    variants = calc.list_available_variants()
    assert len(variants['D2']['variants']) == 6


def test_list_d3_has_four_variants():
    variants = calc.list_available_variants()
    assert len(variants['D3']['variants']) == 4


# ── Full varga calculation Tests ────────────────────────────────────

def test_calculate_all_vargas_returns_all_types():
    planets = {"Sun": 15.5, "Moon": 125.3}
    asc = 10.0
    result = calc.calculate_all_vargas(planets, asc)
    for vt in VargaType:
        assert vt.varga_name in result


def test_house_chart_has_12_houses():
    planets = {"Sun": 15.5, "Moon": 125.3}
    asc = 10.0
    result = calc.calculate_all_vargas(planets, asc)
    for varga_name, data in result.items():
        assert len(data['house_chart']) == 12


def test_d9_navamsa_aries_0_degrees():
    """Aries 0° → Navamsa sign should be Aries (movable sign, part 0)."""
    lon = calc._calculate_varga_position(0.0, 9)
    assert int(lon // 30) == 0  # Aries


def test_d60_shashtiamsa_many_signs():
    """D60 should traverse many signs across 0-30 degrees."""
    signs = set()
    for deg in range(0, 30, 1):
        lon = calc._calculate_varga_position(float(deg), 60)
        signs.add(int(lon // 30))
    assert len(signs) >= 5, "D60 should produce at least 5 different signs"


# ── D30 Trimsamsa special algorithm ────────────────────────────────

def test_d30_odd_sign_mars_region():
    """Odd sign, 0-5° → Aries (Mars region)."""
    lon = calc._calculate_varga_position(2.0, 30)  # Aries 2°
    assert int(lon // 30) == 0  # Aries


def test_d30_even_sign_venus_region():
    """Even sign, 0-5° → Taurus (Venus region)."""
    lon = calc._calculate_varga_position(32.0, 30)  # Taurus 2°
    assert int(lon // 30) == 1  # Taurus
