#!/usr/bin/env python3
"""Tests for jaimini.py — Chara Karaka, Arudha Pada, Karakamsha, Special Lagnas."""

from __future__ import annotations
import sys, os, pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from jaimini import (
    calc_chara_karaka_7, calc_chara_karaka_8,
    calc_arudha_pada_for_house, calc_arudha_padas, calc_upapada,
    calc_graha_padas, calc_karakamsha, calc_special_lagnas, calc_special_lagnas_precise,
    calc_chara_dasha, calc_chara_dasha_with_antardasha,
    KARAKA_7, KARAKA_8, SIGNS, SIGN_LORDS,
)

# Sample planet degrees (degrees within sign, 0-30)
SAMPLE_DEGREES = {
    'Sun': 25.5, 'Moon': 12.3, 'Mars': 8.7,
    'Mercury': 20.1, 'Jupiter': 15.0, 'Venus': 3.5, 'Saturn': 28.9
}

# Sample planet longitudes (0-360)
SAMPLE_LONGS = {
    'Sun': 25.5, 'Moon': 42.3, 'Mars': 68.7,
    'Mercury': 80.1, 'Jupiter': 105.0, 'Venus': 153.5,
    'Saturn': 298.9, 'Rahu': 180.0, 'Ketu': 0.0,
}


# ── Chara Karaka 7 Tests ───────────────────────────────────────────

class TestCharaKaraka7:
    def test_highest_degree_is_ak(self):
        result = calc_chara_karaka_7(SAMPLE_DEGREES)
        ak = result['karaka_table']['Atmakaraka']
        assert ak['planet'] == 'Saturn'  # 28.9 is highest

    def test_lowest_degree_is_dk(self):
        result = calc_chara_karaka_7(SAMPLE_DEGREES)
        dk = result['karaka_table']['Darakaraka']
        assert dk['planet'] == 'Venus'  # 3.5 is lowest

    def test_7_karakas_assigned(self):
        result = calc_chara_karaka_7(SAMPLE_DEGREES)
        assert len(result['karaka_table']) == 7

    def test_karaka_names_correct(self):
        result = calc_chara_karaka_7(SAMPLE_DEGREES)
        expected = set(KARAKA_7.values())
        actual = set(result['karaka_table'].keys())
        assert actual == expected

    def test_rahu_excluded(self):
        degrees = {'Sun': 10.0, 'Moon': 20.0, 'Mars': 5.0,
                   'Mercury': 15.0, 'Jupiter': 25.0, 'Venus': 8.0,
                   'Saturn': 12.0, 'Rahu': 29.0}
        result = calc_chara_karaka_7(degrees)
        planets = [v['planet'] for v in result['karaka_table'].values()]
        assert 'Rahu' not in planets

    def test_summary_present(self):
        result = calc_chara_karaka_7(SAMPLE_DEGREES)
        assert 'summary' in result
        assert 'AK' in result['summary']


# ── Chara Karaka 8 Tests ───────────────────────────────────────────

class TestCharaKaraka8:
    def test_8_karakas_assigned(self):
        degrees = dict(SAMPLE_DEGREES)
        degrees['Rahu'] = 22.0
        result = calc_chara_karaka_8(degrees)
        assert len(result['karaka_table_8']) == 8

    def test_pitrukaraka_present(self):
        degrees = dict(SAMPLE_DEGREES)
        degrees['Rahu'] = 22.0
        result = calc_chara_karaka_8(degrees)
        assert 'Pitrukaraka' in result['karaka_table_8']

    def test_ketu_excluded(self):
        degrees = dict(SAMPLE_DEGREES)
        degrees['Ketu'] = 27.0
        result = calc_chara_karaka_8(degrees)
        planets = [v['planet'] for v in result['karaka_table_8'].values()]
        assert 'Ketu' not in planets


# ── Arudha Pada Tests ──────────────────────────────────────────────

class TestArudhaPada:
    def test_arudha_lagna_a1(self):
        result = calc_arudha_padas(0, SAMPLE_LONGS)  # Aries asc
        assert 'A1' in result['padas']
        assert 'sign' in result['padas']['A1']

    def test_upapada_ul(self):
        result = calc_arudha_padas(0, SAMPLE_LONGS)
        assert 'UL' in result['padas']

    def test_all_12_padas(self):
        result = calc_arudha_padas(0, SAMPLE_LONGS)
        assert len(result['padas']) == 12

    def test_exception_triggered(self):
        # If pada falls back in same sign or 7th, exception applies
        # This depends on planet positions
        result = calc_arudha_padas(0, SAMPLE_LONGS)
        for pada in result['padas'].values():
            assert 'exception_triggered' in pada

    def test_upapada_standalone(self):
        result = calc_upapada(0, SAMPLE_LONGS)
        if result:
            assert 'sign' in result
            assert 'second_from_ul' in result


# ── Karakamsha Tests ───────────────────────────────────────────────

class TestKarakamsha:
    def test_karakamsha_sign(self):
        result = calc_karakamsha('Leo', 15.0)
        assert result['karakamsha_sign'] == 'Leo'
        assert result['karakamsha_lord'] == 'Sun'

    def test_soul_direction(self):
        result = calc_karakamsha('Cancer', 10.0)
        assert 'soul_direction' in result
        assert 'sign_direction' in result['soul_direction']
        assert 'lord_method' in result['soul_direction']

    @pytest.mark.parametrize("sign,expected_lord",
        [('Aries', 'Mars'), ('Taurus', 'Venus'), ('Gemini', 'Mercury'),
         ('Cancer', 'Moon'), ('Leo', 'Sun'), ('Virgo', 'Mercury')])
    def test_karakamsha_lord(self, sign, expected_lord):
        result = calc_karakamsha(sign, 10.0)
        assert result['karakamsha_lord'] == expected_lord


# ── Special Lagnas Tests ───────────────────────────────────────────

class TestSpecialLagnas:
    def test_hl_gl_vl_present(self):
        result = calc_special_lagnas(0, 10, 30)  # Aries asc, 10:30
        assert 'HL' in result
        assert 'GL' in result
        assert 'VL' in result
        assert 'PP' in result
        assert 'ViL' in result

    def test_ghatis_calculated(self):
        result = calc_special_lagnas(0, 10, 30)
        assert 'ghatis_elapsed_from_midnight' in result
        assert result['ghatis_elapsed_from_midnight'] > 0

    def test_vl_based_on_asc(self):
        result = calc_special_lagnas(5, 10, 0)  # Virgo asc
        assert result['VL']['sign_idx'] == (5 * 3) % 12

    def test_each_sign_has_lord(self):
        result = calc_special_lagnas(0, 10, 30)
        for key in ['HL', 'GL', 'VL']:
            assert result[key]['lord'] in SIGN_LORDS.values()

    def test_note_about_sunrise(self):
        result = calc_special_lagnas(0, 10, 30)
        assert 'note' in result

    def test_precise_special_lagnas_use_sunrise_reference(self):
        result = calc_special_lagnas_precise(
            0, 1990, 6, 15, 10, 30, lat=28.6, lon=77.2, tz_offset=5.5
        )
        assert result['capability_status'] == 'covered'
        assert result['precision'] == 'sunrise_correct'
        assert 'sunrise_local_time' in result
        assert result['ghatis_elapsed_from_sunrise'] > 0
        for key in ['HL', 'GL', 'VL', 'PP', 'ViL']:
            assert result[key]['sign'] in SIGNS
            assert result[key]['lord'] in SIGN_LORDS.values()

    def test_precise_special_lagnas_include_varnada_crosscheck(self):
        result = calc_special_lagnas_precise(
            4, REDACTED_YEAR, 4, 17, 14, 45, lat=36.466667, lon=114.2, tz_offset=8
        )
        assert result['VL']['sign_idx'] == (4 * 3) % 12
        assert 'vl_from_hl' in result['VL']

    def test_precise_special_lagnas_expose_named_extended_payloads(self):
        result = calc_special_lagnas_precise(
            0, 1990, 6, 15, 10, 30, lat=28.6, lon=77.2, tz_offset=5.5
        )
        assert result['PP']['full_name'] == 'Pranapada Lagna'
        assert result['ViL']['full_name'] == 'Vighati Lagna'

    def test_precise_special_lagnas_are_time_sensitive(self):
        morning = calc_special_lagnas_precise(
            0, 1990, 6, 15, 10, 0, lat=28.6, lon=77.2, tz_offset=5.5
        )
        later = calc_special_lagnas_precise(
            0, 1990, 6, 15, 11, 0, lat=28.6, lon=77.2, tz_offset=5.5
        )
        assert later['ghatis_elapsed_from_sunrise'] > morning['ghatis_elapsed_from_sunrise']

    def test_precise_special_lagnas_preserve_fractional_minutes(self):
        minute_only = calc_special_lagnas_precise(
            4, REDACTED_YEAR, 4, 17, 14, 45, lat=36.466667, lon=114.2, tz_offset=8
        )
        with_seconds = calc_special_lagnas_precise(
            4, REDACTED_YEAR, 4, 17, 14, 45 + 20 / 60.0, lat=36.466667, lon=114.2, tz_offset=8
        )
        assert with_seconds['birth_utc_hours'] > minute_only['birth_utc_hours']
        assert with_seconds['ghatis_elapsed_from_sunrise'] > minute_only['ghatis_elapsed_from_sunrise']


# ── Graha Padas Tests ──────────────────────────────────────────────

class TestGrahaPadas:
    def test_graha_padas_calculated(self):
        result = calc_graha_padas(SAMPLE_LONGS)
        assert 'graha_padas' in result
        assert len(result['graha_padas']) > 0

    def test_rahu_ketu_excluded(self):
        result = calc_graha_padas(SAMPLE_LONGS)
        assert 'Rahu' not in result['graha_padas']
        assert 'Ketu' not in result['graha_padas']

    def test_graha_pada_structure(self):
        result = calc_graha_padas(SAMPLE_LONGS)
        for pname, pada in result['graha_padas'].items():
            assert 'graha_pada_sign' in pada
            assert 'lord' in pada


# ── Chara Dasha Tests ──────────────────────────────────────────────

class TestCharaDasha:
    def test_12_signs_in_sequence(self):
        result = calc_chara_dasha(0, SAMPLE_LONGS, 1990, 6)
        assert len(result['dasha_sequence']) == 12

    def test_total_cycle_years(self):
        result = calc_chara_dasha(0, SAMPLE_LONGS, 1990, 6)
        assert result['total_cycle_years'] > 0

    def test_ascendant_correct(self):
        result = calc_chara_dasha(0, SAMPLE_LONGS, 1990, 6)
        assert result['ascendant'] == 'Aries'

    def test_dignity_adjustment_present(self):
        result = calc_chara_dasha(0, SAMPLE_LONGS, 1990, 6)
        for d in result['dasha_sequence']:
            assert 'dignity_adjustment' in d

    def test_antardasha_calculated(self):
        result = calc_chara_dasha_with_antardasha(0, SAMPLE_LONGS, 1990, 6)
        assert result['has_antardasha'] == True
        for md in result['dasha_sequence']:
            assert len(md['antardashas']) > 0

    def test_pratyantar_calculated(self):
        result = calc_chara_dasha_with_antardasha(0, SAMPLE_LONGS, 1990, 6)
        assert result['has_pratyantar'] == True
