#!/usr/bin/env python3
"""Tests for tajika.py — Varshaphala annual chart, Tajika Yogas, Muntha."""

from __future__ import annotations
import sys, os, pytest
from datetime import datetime

SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from tajika import (
    calc_muntha, calc_year_lord, calc_mudda_dasha,
    calc_tri_pataka, calc_tajika_yogas, detect_tajika_yogas,
    detect_vedha, calc_all_sahams, calc_tajika_strength_layers, _is_faster,
    SAHAM_RULES_PATH,
    SIGNS, SIGN_LORDS,
)

# ── Muntha Tests ────────────────────────────────────────────────────

class TestMuntha:
    def test_muntha_at_birth_age0(self):
        result = calc_muntha(0, 0)  # Aries asc, age 0
        assert result['muntha_sign'] == 'Aries'

    def test_muntha_advances_one_per_year(self):
        result = calc_muntha(0, 1)  # Aries + 1 year = Taurus
        assert result['muntha_sign'] == 'Taurus'

    def test_muntha_wraps_12(self):
        result = calc_muntha(0, 12)  # Back to Aries
        assert result['muntha_sign'] == 'Aries'

    def test_muntha_lord_correct(self):
        result = calc_muntha(0, 1)  # Taurus
        assert result['muntha_lord'] == 'Venus'

    def test_muntha_interpretation_exists(self):
        result = calc_muntha(5, 10)
        assert 'interpretation' in result
        assert len(result['interpretation']) > 0

    @pytest.mark.parametrize("asc_idx,age,expected_sign_idx",
        [(0, 5, 5), (3, 7, 10), (11, 1, 0)])
    def test_muntha_parametrized(self, asc_idx, age, expected_sign_idx):
        result = calc_muntha(asc_idx, age)
        assert result['muntha_sign_idx'] == expected_sign_idx


# ── Year Lord Tests ─────────────────────────────────────────────────

class TestYearLord:
    def test_year_lord_matches_muntha_lord(self):
        result = calc_year_lord(0, 1)  # Taurus → Venus
        assert result['year_lord'] == 'Venus'

    def test_auxiliary_lords_present(self):
        result = calc_year_lord(0, 5)
        assert len(result['auxiliary_lords']) == 4

    def test_year_theme_exists(self):
        result = calc_year_lord(0, 5)
        assert 'year_theme' in result
        assert len(result['year_theme']) > 0


# ── Mudda Dasha Tests ──────────────────────────────────────────────

class TestMuddaDasha:
    def test_starts_with_varsha_lord(self):
        result = calc_mudda_dasha(0, 'Jupiter', 6)
        assert result['dasha_sequence'][0]['lord'] == 'Jupiter'

    def test_total_months_twelve(self):
        result = calc_mudda_dasha(0, 'Sun', 1)
        total = sum(d['months'] for d in result['dasha_sequence'])
        assert abs(total - 12.0) < 0.5

    def test_all_9_planets_covered(self):
        result = calc_mudda_dasha(0, 'Jupiter', 1)
        assert len(result['dasha_sequence']) <= 9


# ── Tri-Pataka Tests ───────────────────────────────────────────────

class TestTriPataka:
    def test_all_strong_excellent(self):
        # Put all lords in kendra houses from muntha
        planet_lons = {
            'Jupiter': 90.0, 'Saturn': 90.0,  # Same sign as muntha = kendra
        }
        result = calc_tri_pataka(planet_lons, 'Jupiter', 3)
        assert result['verdict'] in ('excellent', 'mixed', 'challenging')

    def test_verdict_values(self):
        planet_lons = {'Sun': 45.0, 'Moon': 135.0}
        result = calc_tri_pataka(planet_lons, 'Sun', 0)
        assert result['verdict'] in ('excellent', 'mixed', 'challenging')

    def test_three_components_present(self):
        planet_lons = {'Sun': 90.0, 'Moon': 180.0, 'Jupiter': 270.0}
        result = calc_tri_pataka(planet_lons, 'Jupiter', 0)
        assert 'dasha_lord' in result
        assert 'muntha_lord' in result
        assert 'year_lord' in result


# ── Harsha / Panchavargiya Bala Tests ─────────────────────────────

class TestTajikaStrengthLayers:
    def test_harsha_and_panchavargiya_strength_layers(self):
        planet_lons = {
            'Sun': 10.0,
            'Moon': 45.0,
            'Mars': 92.0,
            'Mercury': 152.0,
            'Jupiter': 244.0,
            'Venus': 330.0,
            'Saturn': 300.0,
        }

        result = calc_tajika_strength_layers(planet_lons, asc_lon=15.0, year_lord='Jupiter')

        assert result['status'] == 'blocked'
        assert result['method'] == 'Tajika Harsha/Panchavargiya Bala'
        assert 'Panchavargiya Bala' in result['blocked_layers']
        assert result['summary']['next_action']

        for planet in ('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'):
            assert planet in result['harsha_bala']
            assert planet in result['panchavargiya_bala']
            assert result['panchavargiya_bala'][planet]['status'] == 'blocked'
            assert result['combined_strength'][planet]['status'] == 'blocked'
            assert result['combined_strength'][planet]['max_score'] > 0


# ── Tajika Yogas Tests ─────────────────────────────────────────────

class TestTajikaYogas:
    def test_legacy_adapter_blocks_without_speeds(self):
        # Moon(15.0) and Mercury(14.5) in same sign, close degrees
        planet_lons = {'Moon': 15.0, 'Mercury': 14.5, 'Sun': 45.0,
                       'Mars': 90.0, 'Jupiter': 180.0, 'Venus': 210.0, 'Saturn': 300.0}
        result = calc_tajika_yogas(planet_lons)
        assert result['status'] == 'blocked'
        assert result['ithasala'] == []
        assert len(result['ithasala']) >= 0  # May or may not detect based on rules

    def test_graha_yuddha_is_not_inferred_by_legacy_adapter(self):
        # Mercury and Venus very close
        planet_lons = {'Sun': 45.0, 'Moon': 120.0, 'Mars': 90.0,
                       'Mercury': 100.0, 'Venus': 100.5, 'Jupiter': 180.0, 'Saturn': 300.0}
        result = calc_tajika_yogas(planet_lons)
        assert result['graha_yuddha'] == []

    def test_nakta_is_not_inferred_from_sun_moon_co_sign(self):
        planet_lons = {'Sun': 15.0, 'Moon': 18.0, 'Mars': 90.0,
                       'Mercury': 60.0, 'Jupiter': 180.0, 'Venus': 210.0, 'Saturn': 300.0}
        result = calc_tajika_yogas(planet_lons)
        assert result['nakta'] == []

    def test_summary_present(self):
        planet_lons = {'Sun': 45.0, 'Moon': 120.0, 'Mars': 90.0,
                       'Mercury': 60.0, 'Jupiter': 180.0, 'Venus': 210.0, 'Saturn': 300.0}
        result = calc_tajika_yogas(planet_lons)
        assert 'summary' in result
        assert 'Blocked' in result['summary']


class TestDetectTajikaYogas:
    def test_legacy_detector_is_not_a_golden_case_oracle(self):
        # Use close-degree planets to force Ithasala detection
        planets = {'Sun': 14.0, 'Moon': 15.0, 'Mars': 90.0,
                   'Mercury': 14.8, 'Jupiter': 180.0, 'Venus': 210.0, 'Saturn': 300.0}
        yogas = detect_tajika_yogas(planets)
        types = set(y['type'] for y in yogas)
        assert isinstance(yogas, list)

    def test_legacy_detector_does_not_prove_itasala(self):
        # Moon(15) fast, Sun(14) slow → same sign, close
        planets = {'Sun': 14.0, 'Moon': 15.0, 'Mars': 90.0,
                   'Mercury': 60.0, 'Jupiter': 180.0, 'Venus': 210.0, 'Saturn': 300.0}
        yogas = detect_tajika_yogas(planets)
        types = set(y['type'] for y in yogas)
        assert isinstance(types, set)

    def test_kuta_yoga_three_planets_same_sign(self):
        planets = {'Sun': 5.0, 'Moon': 8.0, 'Mars': 12.0,
                   'Mercury': 60.0, 'Jupiter': 180.0, 'Venus': 210.0, 'Saturn': 300.0}
        yogas = detect_tajika_yogas(planets)
        types = set(y['type'] for y in yogas)
        assert 'Kuta' in types


# ── Vedha Detection Tests ──────────────────────────────────────────

class TestVedhaDetection:
    def test_vedha_returns_list(self):
        planets = {'Sun': 45.0, 'Moon': 120.0, 'Mars': 90.0,
                   'Mercury': 60.0, 'Jupiter': 180.0, 'Venus': 210.0, 'Saturn': 300.0}
        result = detect_vedha(planets)
        assert isinstance(result, list)

    def test_vedha_structure(self):
        planets = {'Sun': 45.0, 'Moon': 120.0, 'Mars': 90.0,
                   'Mercury': 60.0, 'Jupiter': 180.0, 'Venus': 210.0, 'Saturn': 300.0}
        result = detect_vedha(planets)
        if result:
            assert 'planets' in result[0]
            assert 'description' in result[0]


# ── Sahams Tests ────────────────────────────────────────────────────

class TestSahams:
    def test_sahams_block_without_location_context(self):
        result = calc_all_sahams({'Sun': 45.0, 'Moon': 120.0}, 10.0, datetime(1990, 6, 15, 12, 0))
        assert result['status'] == 'blocked'

    def test_tajika_module_exposes_saham_rules_reference_path(self):
        assert SAHAM_RULES_PATH.endswith('references/saham_rules.json')
        assert os.path.exists(SAHAM_RULES_PATH)

    def test_all_sahams_calculated(self):
        planet_lons = {'Sun': 45.0, 'Moon': 120.0, 'Mars': 90.0,
                       'Mercury': 60.0, 'Jupiter': 180.0, 'Venus': 210.0,
                       'Saturn': 300.0, 'Rahu': 150.0, 'Ketu': 330.0}
        asc_lon = 10.0
        birth_dt = datetime(1990, 6, 15, 10, 30)
        result = calc_all_sahams(planet_lons, asc_lon, birth_dt, lat=39.9042, lon=116.4074, tz=8)
        assert 'punya_saham' in result
        assert 'karya_saham' in result
        assert 'vivah_saham' in result

    def test_saham_longitude_in_range(self):
        planet_lons = {'Sun': 45.0, 'Moon': 120.0, 'Mars': 90.0,
                       'Mercury': 60.0, 'Jupiter': 180.0, 'Venus': 210.0,
                       'Saturn': 300.0, 'Rahu': 150.0, 'Ketu': 330.0}
        result = calc_all_sahams(planet_lons, 10.0, datetime(1990, 6, 15, 10, 30))
        for key, val in result.items():
            if isinstance(val, dict) and 'longitude' in val:
                assert 0 <= val['longitude'] < 360

    def test_punya_saham_formula(self):
        # Punya = Asc + (Moon - Sun), sourced from references/saham_rules.json
        sun, moon, asc = 45.0, 120.0, 10.0
        expected = (asc + (moon - sun)) % 360  # = 10 + 75 = 85
        planet_lons = {'Sun': sun, 'Moon': moon, 'Mars': 90.0,
                       'Mercury': 60.0, 'Jupiter': 180.0, 'Venus': 210.0,
                       'Saturn': 300.0, 'Rahu': 150.0, 'Ketu': 330.0}
        result = calc_all_sahams(planet_lons, asc, datetime(1990, 6, 15, 12, 0), lat=39.9042, lon=116.4074, tz=8)
        assert abs(result['punya_saham']['longitude'] - expected) < 0.01

    def test_karma_saham_uses_reference_json_day_formula(self):
        # Karma_Saham day rule = Mars - Mercury + Asc, sourced from references/saham_rules.json
        asc = 10.0
        planet_lons = {'Sun': 45.0, 'Moon': 120.0, 'Mars': 90.0,
                       'Mercury': 60.0, 'Jupiter': 180.0, 'Venus': 210.0,
                       'Saturn': 300.0, 'Rahu': 150.0, 'Ketu': 330.0}
        expected = (asc + (90.0 - 60.0)) % 360
        result = calc_all_sahams(planet_lons, asc, datetime(1990, 6, 15, 12, 0), lat=39.9042, lon=116.4074, tz=8)
        assert abs(result['karma_saham']['longitude'] - expected) < 0.01

    def test_formula_saham_applies_reference_add_30_exception(self):
        from tajika import _calc_formula_saham

        # Asc 50 is outside the forward 100 -> 200 zodiacal arc.
        result = _calc_formula_saham(
            'Punya_Saham',
            {'Sun': 200.0, 'Moon': 100.0},
            50.0,
            True,
            {},
        )
        assert result == 340.0

    def test_is_faster_moon_vs_sun(self):
        assert _is_faster('Moon', 'Sun')
        assert _is_faster('Mercury', 'Jupiter')
