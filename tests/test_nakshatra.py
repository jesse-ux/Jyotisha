#!/usr/bin/env python3
"""Tests for nakshatra_advanced.py — Nakshatra identification, Tara, Sub-Lord, Dasha."""

from __future__ import annotations
import sys, os, pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from nakshatra_advanced import (
    find_nakshatra, calc_tara_bala, calc_all_tara_balas,
    calc_vimshottari_start, calc_sub_lord, nakshatra_compatibility,
    calc_chandra_bala, calc_tara_chandra_combined,
    calc_nakshatra_transits_natal, nakshatra_full_report,
    NAK_NAMES, NAK_LORDS, NAK_YEARS, TARA_NAMES,
)

# ── Nakshatra Identification Tests ──────────────────────────────────

class TestFindNakshatra:
    def test_0_degrees_ashwini(self):
        result = find_nakshatra(0.0)
        assert result['nakshatra'] == 'Ashwini'
        assert result['nakshatra_idx'] == 0

    def test_13_33_degrees_bharani(self):
        result = find_nakshatra(13.34)
        assert result['nakshatra'] == 'Bharani'

    def test_360_degrees_wraps(self):
        result = find_nakshatra(360.0)
        # 360° = 0° → Ashwini
        assert result['nakshatra'] == 'Ashwini'

    @pytest.mark.parametrize("lon,expected_idx", [
        (0.0, 0), (6.0, 0), (13.34, 1),
        (26.67, 1), (26.68, 2),
        (40.0, 2), (53.34, 3),
        (180.0, 13), (240.0, 18), (320.0, 24), (346.67, 26),
    ])
    def test_nakshatra_indices(self, lon, expected_idx):
        result = find_nakshatra(lon)
        assert result['nakshatra_idx'] == expected_idx

    def test_pada_range_1_to_4(self):
        for lon in [0.0, 5.0, 10.0, 12.0]:
            result = find_nakshatra(lon)
            assert 1 <= result['pada'] <= 4

    def test_lord_correct(self):
        result = find_nakshatra(0.0)  # Ashwini
        assert result['nakshatra_lord'] == 'Ketu'

    def test_dasha_years_correct(self):
        result = find_nakshatra(0.0)  # Ashwini → Ketu → 7 years
        assert result['dasha_years'] == 7

    def test_gana_present(self):
        result = find_nakshatra(0.0)
        assert 'gana' in result

    def test_element_present(self):
        result = find_nakshatra(0.0)
        assert 'element' in result

    def test_all_27_nakshatras_accessible(self):
        for i in range(27):
            lon = i * (360.0 / 27) + 0.01
            result = find_nakshatra(lon)
            assert result['nakshatra_idx'] == i


# ── Tara Bala Tests ─────────────────────────────────────────────────

class TestTaraBala:
    def test_same_nakshatra_janma(self):
        result = calc_tara_bala(0, 0)
        assert result['tara_index'] == 0
        assert result['tara_name'] == 'Janma(生命)'

    def test_1_step_sampat(self):
        result = calc_tara_bala(0, 1)
        assert result['tara_index'] == 1
        assert result['is_auspicious'] == True

    def test_2_step_vipat(self):
        result = calc_tara_bala(0, 2)
        assert result['tara_index'] == 2
        assert result['is_dangerous'] == True

    def test_9_steps_cyclic(self):
        result = calc_tara_bala(0, 9)
        assert result['tara_index'] == 0  # 9 % 9 = 0

    def test_auspicious_taras(self):
        for d in [1, 3, 5, 7, 8]:
            result = calc_tara_bala(0, d)
            assert result['is_auspicious'] == True

    def test_dangerous_taras(self):
        for d in [2, 4, 6]:
            result = calc_tara_bala(0, d)
            assert result['is_dangerous'] == True

    def test_all_tara_balas(self):
        planet_lons = {'Sun': 45.0, 'Moon': 120.0, 'Mars': 200.0}
        result = calc_all_tara_balas(0, planet_lons)
        for pname in planet_lons:
            assert pname in result
            assert 'tara' in result[pname]


# ── Chandra Bala Tests ─────────────────────────────────────────────

class TestChandraBala:
    def test_same_sign_janma(self):
        result = calc_chandra_bala(0, 0)
        assert result['rashi_from_moon'] == 0
        assert result['chandra_cn'] == '生命位'

    def test_1_step_sampat(self):
        result = calc_chandra_bala(0, 1)
        assert result['is_auspicious'] == True

    def test_6_step_vadha(self):
        result = calc_chandra_bala(0, 6)
        assert result['is_dangerous'] == True

    def test_8_step_parama_mitra(self):
        result = calc_chandra_bala(0, 8)
        assert result['is_auspicious'] == True

    def test_quality_classification(self):
        for d in range(12):
            result = calc_chandra_bala(0, d)
            assert result['quality'] in ('auspicious', 'dangerous', 'neutral')


# ── Vimshottari Start Tests ────────────────────────────────────────

class TestVimshottariStart:
    def test_moon_nakshatra_correct(self):
        result = calc_vimshottari_start(0.0)  # Ashwini
        assert result['moon_nakshatra'] == 'Ashwini'
        assert result['first_mahadasha_lord'] == 'Ketu'

    def test_remaining_ratio_range(self):
        for lon in [0.01, 6.0, 10.0, 13.0, 350.0]:
            result = calc_vimshottari_start(lon)
            assert 0 <= result['remaining_ratio'] <= 1
            assert 0 <= result['used_ratio'] <= 1
            assert abs(result['remaining_ratio'] + result['used_ratio'] - 1.0) < 0.001

    def test_remaining_years_positive(self):
        result = calc_vimshottari_start(5.0)
        assert result['first_mahadasha_remaining_years'] > 0

    def test_pada_present(self):
        result = calc_vimshottari_start(5.0)
        assert 1 <= result['moon_pada'] <= 4


# ── Sub-Lord Tests ──────────────────────────────────────────────────

class TestSubLord:
    def test_sub_lord_calculated(self):
        result = calc_sub_lord(5.0)
        assert 'sub_lord' in result
        assert result['sub_lord'] in ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars',
                                       'Rahu', 'Jupiter', 'Saturn', 'Mercury']

    def test_sub_lord_index_range(self):
        result = calc_sub_lord(5.0)
        assert 0 <= result['sub_index'] < 9

    def test_different_lons_different_sub_lords(self):
        subs = set()
        for lon in [0.5, 2.0, 4.0, 7.0, 10.0]:
            result = calc_sub_lord(lon)
            subs.add(result['sub_lord'])
        assert len(subs) >= 2  # Different longitudes should yield different sub-lords

    def test_nakshatra_lord_matches(self):
        result = calc_sub_lord(0.01)
        assert result['nakshatra_lord'] == 'Ketu'  # Ashwini lord


# ── Nakshatra Compatibility Tests ───────────────────────────────────

class TestNakshatraCompatibility:
    def test_compatibility_result(self):
        result = nakshatra_compatibility(0, 3)  # Ashwini vs Rohini
        assert 'overall' in result
        assert result['overall'] in ('compatible', 'moderate', 'challenging')

    def test_same_nakshatra_compatible(self):
        result = nakshatra_compatibility(0, 0)
        assert result['tara_score'] >= 1.5

    def test_element_match(self):
        result = nakshatra_compatibility(0, 2)  # Ashwini(fire) vs Krittika(fire)
        assert result['element_match']['compatible'] == True

    def test_gana_match(self):
        result = nakshatra_compatibility(0, 6)  # Ashwini(Dev) vs Punarvasu(Dev)
        assert result['gana_match']['score'] >= 3


# ── Tara+Chandra Combined Tests ────────────────────────────────────

class TestTaraChandraCombined:
    def test_combined_analysis(self):
        planet_lons = {'Sun': 45.0, 'Mars': 200.0}
        result = calc_tara_chandra_combined(0, 0, planet_lons)
        for pname in planet_lons:
            assert 'tara' in result[pname]
            assert 'chandra' in result[pname]
            assert 'combined_score' in result[pname]

    def test_score_categories(self):
        planet_lons = {'Sun': 45.0}
        result = calc_tara_chandra_combined(0, 0, planet_lons)
        for pname in planet_lons:
            assert result[pname]['combined_score'] in (
                'double_auspicious', 'double_dangerous',
                'tara_good_chandra_bad', 'tara_bad_chandra_good',
                'mixed_favorable', 'mixed_unfavorable', 'neutral')


# ── Natal Nakshatra Transits Tests ─────────────────────────────────

class TestNakshatraTransitsNatal:
    def test_all_planets_analyzed(self):
        planet_lons = {'Sun': 45.0, 'Moon': 120.0, 'Mars': 200.0}
        result = calc_nakshatra_transits_natal(planet_lons)
        assert len(result) == 3
        for pname in planet_lons:
            assert result[pname]['nakshatra'] in NAK_NAMES

    def test_details_present(self):
        planet_lons = {'Sun': 45.0}
        result = calc_nakshatra_transits_natal(planet_lons)
        for key in ['nakshatra', 'pada', 'gana', 'element', 'dasha_years']:
            assert key in result['Sun']


# ── Full Report Tests ──────────────────────────────────────────────

class TestNakshatraFullReport:
    def test_full_report_structure(self):
        chart_data = {
            'planets': {
                'Sun': {'degree': 45.0},
                'Moon': {'degree': 120.0},
                'Mars': {'degree': 200.0},
            }
        }
        result = nakshatra_full_report(chart_data)
        assert 'natal_nakshatras' in result
        assert 'tara_bala' in result
        assert 'chandra_bala' in result
        assert 'sub_lords' in result

    def test_power_ranking_present(self):
        chart_data = {
            'planets': {
                'Sun': {'degree': 45.0},
                'Moon': {'degree': 120.0},
            }
        }
        result = nakshatra_full_report(chart_data)
        assert 'power_ranking' in result
        assert len(result['power_ranking']) >= 2
