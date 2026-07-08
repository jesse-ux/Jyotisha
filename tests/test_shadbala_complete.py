#!/usr/bin/env python3
"""Tests for shadbala.py — 6-fold strength, Kendra 3-tier, Bhava Bala, Hora Bala."""

from __future__ import annotations
import json
import sys, os, pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from shadbala import (
    calc_shadbala, calc_sthana_bala, calc_dig_bala, calc_kala_bala,
    calc_chesta_bala, calc_drik_bala, calc_bhava_bala,
    NAISARGIKA_BALA, MIN_REQUIRED, DIG_BALA_HOUSE,
    EXALTATION_DEG, DEBILITATION_DEG, FRIENDSHIP, SHADBALA_CONSTANTS_PATH,
)
from scripts.shadbala_oracle_comparison import compare_case

# Standard test chart data
def _sample_planets():
    return {
        'Sun': {'sign': 'Gemini', 'degree': 70.0, 'house': 3, 'retrograde': False, 'speed': 1.0},
        'Moon': {'sign': 'Taurus', 'degree': 45.0, 'house': 2, 'retrograde': False, 'speed': 13.0},
        'Mars': {'sign': 'Capricorn', 'degree': 280.0, 'house': 10, 'retrograde': False, 'speed': 0.5},
        'Mercury': {'sign': 'Gemini', 'degree': 80.0, 'house': 3, 'retrograde': False, 'speed': 1.2},
        'Jupiter': {'sign': 'Cancer', 'degree': 105.0, 'house': 5, 'retrograde': False, 'speed': 0.08},
        'Venus': {'sign': 'Leo', 'degree': 130.0, 'house': 4, 'retrograde': False, 'speed': 1.2},
        'Saturn': {'sign': 'Aquarius', 'degree': 320.0, 'house': 12, 'retrograde': True, 'speed': -0.03},
    }


def _shadbala_constants():
    with open(os.path.join(os.path.dirname(__file__), '..', 'references', 'shat_bala_constants.json'), 'r', encoding='utf-8') as handle:
        return json.load(handle)


# ── Sthana Bala Tests ───────────────────────────────────────────────

class TestSthanaBala:
    def test_ucha_bala_range(self):
        result = calc_sthana_bala('Sun', 70.0, 'Gemini', 3)
        assert 0 <= result['ucha_bala'] <= 60

    def test_exalted_planet_high_ucha(self):
        # Sun exalted at 10° Aries
        result = calc_sthana_bala('Sun', 10.0, 'Aries', 1)
        assert result['ucha_bala'] > 55  # Near max

    def test_debilitated_planet_low_ucha(self):
        # Sun debilitated in Libra
        result = calc_sthana_bala('Sun', 190.0, 'Libra', 7)
        assert result['ucha_bala'] < 5

    def test_sapta_score_has_7_components(self):
        result = calc_sthana_bala('Jupiter', 105.0, 'Cancer', 5)
        for key in ['sapta_d1', 'sapta_d2', 'sapta_d3', 'sapta_d4',
                     'sapta_d7', 'sapta_d9', 'sapta_d12']:
            assert key in result

    def test_own_sign_d1_score(self):
        # Sun in Leo = own sign
        result = calc_sthana_bala('Sun', 125.0, 'Leo', 5)
        assert result['sapta_d1'] == 45.0

    def test_ojayugma_bala_range(self):
        result = calc_sthana_bala('Mercury', 80.0, 'Gemini', 3)
        assert result['ojayugma_bala'] in (0, 15)

    def test_drekkana_bala_range(self):
        result = calc_sthana_bala('Sun', 5.0, 'Aries', 1)
        assert result['drekkana_bala'] in (0, 15)

    def test_sapta_d3_exaltation_branch_is_capped_below_d1_exaltation(self):
        result = calc_sthana_bala('Sun', 0.0, 'Aries', 1)
        assert result['sapta_d1'] == 50.0
        assert result['sapta_d3'] == 45.0

    def test_sapta_d3_own_sign_branch_is_capped_below_d1_own_sign(self):
        result = calc_sthana_bala('Venus', 30.0, 'Taurus', 2)
        assert result['sapta_d1'] == 45.0
        assert result['sapta_d3'] == 30.0

    def test_total_positive(self):
        result = calc_sthana_bala('Jupiter', 105.0, 'Cancer', 5)
        assert result['total'] > 0


# ── Kendra Bala 3-Tier Tests ───────────────────────────────────────

class TestKendraBala:
    @pytest.mark.precision
    def test_kendra_house_60(self):
        result = calc_sthana_bala('Sun', 70.0, 'Gemini', 1)  # House 1 = Kendra
        assert result['kendra_bala'] == 60.0

    @pytest.mark.precision
    def test_panapara_house_30(self):
        result = calc_sthana_bala('Sun', 70.0, 'Gemini', 2)  # House 2 = Panapara
        assert result['kendra_bala'] == 30.0

    @pytest.mark.precision
    def test_apoklima_house_15(self):
        result = calc_sthana_bala('Sun', 70.0, 'Gemini', 3)  # House 3 = Apoklima
        assert result['kendra_bala'] == 15.0

    @pytest.mark.parametrize("house,expected", [
        (1, 60.0), (4, 60.0), (7, 60.0), (10, 60.0),
        (2, 30.0), (5, 30.0), (8, 30.0), (11, 30.0),
        (3, 15.0), (6, 15.0), (9, 15.0), (12, 15.0),
    ])
    def test_all_houses_kendra_bala(self, house, expected):
        result = calc_sthana_bala('Sun', 70.0, 'Gemini', house)
        assert result['kendra_bala'] == expected


# ── Dig Bala Tests ──────────────────────────────────────────────────

class TestDigBala:
    def test_sun_in_10th_max(self):
        assert calc_dig_bala('Sun', 10) == 60.0

    def test_sun_in_4th_min(self):
        assert calc_dig_bala('Sun', 4) == 0.0

    def test_jupiter_in_1st_max(self):
        assert calc_dig_bala('Jupiter', 1) == 60.0

    def test_saturn_in_7th_max(self):
        assert calc_dig_bala('Saturn', 7) == 60.0

    def test_moon_in_4th_max(self):
        assert calc_dig_bala('Moon', 4) == 60.0

    def test_midrange_positive(self):
        assert 0 < calc_dig_bala('Sun', 7) < 60

    def test_dig_bala_jupiter_synthetic_north_china_case_needs_better_than_house_only_linear_model(self):
        comparison = compare_case("references/oracle/dasha_shadbala_oracle_cases.json", "template_synthetic_north_china_shadbala_raman")
        jupiter_dig_gap = comparison["comparison"]["Jupiter"]["components"]["dig"]["abs_diff_rupa"]

        assert jupiter_dig_gap < 3.6348


# ── Kala Bala Tests ─────────────────────────────────────────────────

class TestKalaBala:
    def test_mercury_always_60_nathonnata(self):
        result = calc_kala_bala('Mercury', False, True, 45.0, 120.0, 12.0)
        assert result['nathonnata'] == 60.0

    def test_nathonnata_day_birth_sun(self):
        result = calc_kala_bala('Sun', False, True, 45.0, 120.0, 12.0)
        assert result['nathonnata'] == 60.0  # Noon

    def test_nathonnata_night_birth_moon(self):
        result = calc_kala_bala('Moon', True, True, 45.0, 120.0, 0.0)
        assert result['nathonnata'] == 60.0  # Midnight

    def test_paksha_bala_range(self):
        result = calc_kala_bala('Jupiter', False, True, 45.0, 120.0, 12.0)
        assert 0 <= result['paksha'] <= 30

    def test_hora_bala_present(self):
        result = calc_kala_bala('Sun', False, True, 45.0, 120.0, 12.0)
        assert 'hora' in result

    def test_hora_lord_gets_60(self):
        # Test that some planet gets hora = 60
        results = []
        for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
            r = calc_kala_bala(pname, False, True, 45.0, 120.0, 12.0)
            results.append(r['hora'])
        assert 60.0 in results  # At least one planet is hora lord

    def test_total_positive(self):
        result = calc_kala_bala('Jupiter', False, True, 45.0, 120.0, 12.0)
        assert result['total'] > 0


# ── Chesta Bala Tests ───────────────────────────────────────────────

class TestChestaBala:
    def test_retrograde_max(self):
        assert calc_chesta_bala('Mars', True, -0.5, 45.0, 120.0) == 60.0

    def test_moon_full_max(self):
        # Moon opposite Sun → full moon → 60
        assert calc_chesta_bala('Moon', False, 13.0, 0.0, 180.0) == 60.0

    def test_moon_new_min(self):
        assert calc_chesta_bala('Moon', False, 13.0, 0.0, 0.0) == 0.0

    def test_sun_speed_based(self):
        result = calc_chesta_bala('Sun', False, 0.985, 45.0, 120.0)
        assert 0 <= result <= 60

    def test_direct_fast_moderate(self):
        result = calc_chesta_bala('Mars', False, 1.5, 45.0, 120.0)
        assert 0 <= result <= 60


# ── Drik Bala Tests ─────────────────────────────────────────────────

class TestDrikBala:
    def test_drik_bala_range(self):
        planets = _sample_planets()
        result = calc_drik_bala('Jupiter', 'Cancer', 5, planets)
        assert -60 <= result <= 60

    def test_benefic_aspect_positive(self):
        planets = _sample_planets()
        result = calc_drik_bala('Mars', 'Capricorn', 10, planets)
        assert isinstance(result, float)


# ── Full Shadbala Tests ─────────────────────────────────────────────

class TestShadbalaFull:
    def test_shadbala_module_exposes_reference_constants_path(self):
        assert SHADBALA_CONSTANTS_PATH.endswith('references/shat_bala_constants.json')
        assert os.path.exists(SHADBALA_CONSTANTS_PATH)

    def test_static_shadbala_constants_are_loaded_from_reference_json(self):
        constants = _shadbala_constants()
        sun_exalt = constants['exaltation_degrees']['Sun']
        saturn_debil = constants['debilitation_degrees']['Saturn']
        mercury_rel = constants['natural_relationships']['Mercury']

        assert EXALTATION_DEG['Sun'] == pytest.approx(sun_exalt['sign'] * 30 + sun_exalt['degree'])
        assert DEBILITATION_DEG['Saturn'] == pytest.approx(saturn_debil['sign'] * 30 + saturn_debil['degree'])
        assert FRIENDSHIP['Mercury']['friend'] == mercury_rel['friends']
        assert FRIENDSHIP['Mercury']['enemy'] == mercury_rel['enemies']
        assert FRIENDSHIP['Mercury']['neutral'] == mercury_rel['neutrals']

    def test_all_7_planets_calculated(self):
        result = calc_shadbala(_sample_planets(), 'Leo', 10.0, 70.0, 45.0)
        for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
            assert pname in result['planets']

    def test_total_rupas_positive(self):
        result = calc_shadbala(_sample_planets(), 'Leo', 10.0, 70.0, 45.0)
        for pname, data in result['planets'].items():
            assert data['total_rupas'] > 0

    def test_total_virupas_preserves_component_sum_without_global_normalization(self):
        result = calc_shadbala(_sample_planets(), 'Leo', 10.0, 70.0, 45.0)
        for pname, data in result['planets'].items():
            component_sum = (
                data['sthana_bala']['total']
                + data['dig_bala']
                + data['kala_bala']['total']
                + data['chesta_bala']
                + data['naisargika_bala']
                + data['drik_bala']
            )
            assert data['total_virupas'] == pytest.approx(component_sum, abs=0.08), pname

    def test_total_required_strength_is_not_halved_by_global_1200_invariant(self):
        result = calc_shadbala(_sample_planets(), 'Leo', 10.0, 70.0, 45.0)
        total_rupas = sum(data['total_rupas'] for data in result['planets'].values())
        assert total_rupas >= sum(MIN_REQUIRED.values())

    def test_ishta_bala_calculated(self):
        result = calc_shadbala(_sample_planets(), 'Leo', 10.0, 70.0, 45.0)
        for pname, data in result['planets'].items():
            assert data['ishta_bala_pct'] >= 0

    def test_strength_level_present(self):
        result = calc_shadbala(_sample_planets(), 'Leo', 10.0, 70.0, 45.0)
        for pname, data in result['planets'].items():
            assert data['strength_level'] in ('极强', '强', '充足', '略弱', '弱', '极弱')

    def test_ranking_present(self):
        result = calc_shadbala(_sample_planets(), 'Leo', 10.0, 70.0, 45.0)
        assert len(result['ranking']) == 7
        assert result['strongest'] is not None

    def test_naisargika_bala_standard(self):
        assert NAISARGIKA_BALA['Sun'] == 60.0
        assert NAISARGIKA_BALA['Saturn'] == 8.57


# ── Bhava Bala Tests ────────────────────────────────────────────────

class TestBhavaBala:
    def test_12_houses_calculated(self):
        result = calc_bhava_bala(_sample_planets(), 'Leo')
        for house in range(1, 13):
            assert house in result

    def test_benefic_in_house_positive(self):
        # Jupiter in house 5 = benefic
        result = calc_bhava_bala(_sample_planets(), 'Leo')
        assert result[5]['score'] > 0

    def test_strength_classification(self):
        result = calc_bhava_bala(_sample_planets(), 'Leo')
        for house, data in result.items():
            assert data['strength'] in ('Strong', 'Moderate', 'Weak')

    def test_lord_info_present(self):
        result = calc_bhava_bala(_sample_planets(), 'Leo')
        for house, data in result.items():
            assert 'lord' in data
            assert 'sign' in data

    def test_factors_list(self):
        result = calc_bhava_bala(_sample_planets(), 'Leo')
        for house, data in result.items():
            assert isinstance(data['factors'], list)
