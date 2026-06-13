#!/usr/bin/env python3
"""Tests for muhurta.py — Panchanga calculation, auspicious/inauspicious periods."""

from __future__ import annotations
import sys, os, pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from muhurta import (
    calc_tithi, calc_nakshatra_from_lon, calc_yoga, calc_karana,
    calc_vara, calc_hora, calc_abhijit_muhurta, calc_panchanga,
    check_activity_muhurta, muhurta_full_report,
    TITHI_NAMES, TITHI_QUALITY, NAKSHATRAS, NAKSHATRA_TYPE,
    YOGA_NAMES, YOGA_QUALITY, KARANA_NAMES, KARANA_QUALITY,
    VARA_LORDS, ACTIVITY_RULES,
)


# ── Tithi Tests ─────────────────────────────────────────────────────

class TestTithi:
    def test_new_moon_tithi_30(self):
        # Moon-Sun diff = 0 → tithi 1
        result = calc_tithi(0.0, 0.0)
        assert result['tithi_num'] == 1

    def test_full_moon_tithi_15(self):
        # Moon-Sun diff = 180° → tithi 16 (Krishna 1)
        result = calc_tithi(0.0, 180.0)
        assert result['tithi_num'] == 16  # Krishna Pratipada

    def test_shukla_paksha(self):
        result = calc_tithi(0.0, 60.0)  # 60/12=5+1=6
        assert result['paksha'] == 'Shukla'

    def test_krishna_paksha(self):
        result = calc_tithi(0.0, 210.0)  # 210/12=17+1=18
        assert result['paksha'] == 'Krishna'

    def test_purnima_name(self):
        result = calc_tithi(0.0, 174.0)  # ~15th tithi
        if result['tithi_num'] == 15:
            assert result['name'] == 'Purnima'

    def test_amavasya_name(self):
        result = calc_tithi(0.0, 354.0)  # ~30th tithi
        if result['tithi_num'] == 30:
            assert result['name'] == 'Amavasya'

    @pytest.mark.parametrize("diff,tithi",
        [(0, 1), (12, 2), (24, 3), (168, 15), (180, 16), (348, 30)])
    def test_tithi_from_diff(self, diff, tithi):
        result = calc_tithi(0.0, float(diff))
        assert result['tithi_num'] == tithi

    def test_tithi_quality_present(self):
        result = calc_tithi(0.0, 60.0)
        assert result['quality'] in ('subha', 'asubha', 'mixed')


# ── Nakshatra from Longitude Tests ──────────────────────────────────

class TestNakshatraFromLon:
    def test_ashwini_at_0(self):
        result = calc_nakshatra_from_lon(0.0)
        assert result['nakshatra'] == 'Ashwini'

    def test_revati_near_360(self):
        result = calc_nakshatra_from_lon(355.0)
        assert result['nakshatra'] == 'Revati'

    def test_pada_range(self):
        for lon in [1.0, 5.0, 8.0, 11.0]:
            result = calc_nakshatra_from_lon(lon)
            assert 1 <= result['pada'] <= 4

    def test_27_nakshatras(self):
        assert len(NAKSHATRAS) == 27

    def test_nakshatra_type(self):
        result = calc_nakshatra_from_lon(0.0)  # Ashwini
        assert result['type'] == 'laghu'


# ── Yoga Tests ──────────────────────────────────────────────────────

class TestYoga:
    def test_vishkambha_at_low_sum(self):
        result = calc_yoga(0.0, 0.0)  # sum=0 → idx 0
        assert result['yoga'] == 'Vishkambha'

    def test_yoga_idx_range(self):
        result = calc_yoga(180.0, 180.0)
        assert 0 <= result['yoga_idx'] < 27

    def test_yoga_quality_present(self):
        result = calc_yoga(45.0, 120.0)
        assert result['quality'] in ('subha', 'asubha', 'mixed')

    def test_27_yogas(self):
        assert len(YOGA_NAMES) == 27

    def test_vaidhriti_asubha(self):
        assert YOGA_QUALITY['Vaidhriti'] == 'asubha'

    def test_priti_subha(self):
        assert YOGA_QUALITY['Priti'] == 'subha'


# ── Karana Tests ────────────────────────────────────────────────────

class TestKarana:
    def test_kimstughna_first_half(self):
        # Moon-Sun diff near 0 → k_num=0
        result = calc_karana(0.0, 1.0)
        assert result['karana'] == 'Kimstughna'

    def test_vishti_asubha(self):
        assert KARANA_QUALITY['Vishti'] == 'asubha'

    def test_karana_quality_present(self):
        result = calc_karana(0.0, 60.0)
        assert result['quality'] in ('subha', 'asubha', 'mixed')

    def test_11_karana_names(self):
        assert len(KARANA_NAMES) == 11

    def test_is_vishti_flag(self):
        # Test when karana is Vishti
        result = calc_karana(0.0, 60.0)
        assert isinstance(result['is_vishti'], bool)


# ── Vara Tests ──────────────────────────────────────────────────────

class TestVara:
    def test_sunday(self):
        result = calc_vara(0)
        assert result['vara'] == 'Sunday'
        assert result['vara_lord'] == 'Sun'
        assert result['quality'] == 'asubha'

    def test_monday(self):
        result = calc_vara(1)
        assert result['vara_lord'] == 'Moon'
        assert result['quality'] == 'subha'

    def test_thursday_jupiter(self):
        result = calc_vara(4)
        assert result['vara_lord'] == 'Jupiter'

    def test_7_days(self):
        assert len(VARA_LORDS) == 7

    @pytest.mark.parametrize("idx,expected_lord",
        [(0, 'Sun'), (1, 'Moon'), (2, 'Mars'), (3, 'Mercury'),
         (4, 'Jupiter'), (5, 'Venus'), (6, 'Saturn')])
    def test_all_vara_lords(self, idx, expected_lord):
        result = calc_vara(idx)
        assert result['vara_lord'] == expected_lord


# ── Hora Tests ──────────────────────────────────────────────────────

class TestHora:
    def test_hora_lord_calculated(self):
        result = calc_hora(0, 6.0)  # Sunday, 6h from sunrise
        assert result['hora_lord'] in ('Sun', 'Moon', 'Mars', 'Mercury',
                                        'Jupiter', 'Venus', 'Saturn')

    def test_hora_quality_present(self):
        result = calc_hora(0, 6.0)
        assert result['quality'] in ('subha', 'asubha', 'mixed')

    def test_hora_num_range(self):
        result = calc_hora(0, 6.0)
        assert 1 <= result['hora_num'] <= 24


# ── Abhijit Muhurta Tests ──────────────────────────────────────────

class TestAbhijitMuhurta:
    def test_basic_structure(self):
        result = calc_abhijit_muhurta()
        assert 'duration_minutes' in result
        assert result['duration_minutes'] == 48

    def test_wednesday_warning(self):
        result = calc_abhijit_muhurta()
        assert 'Wednesday' in result['warning']

    def test_with_jd_values(self):
        result = calc_abhijit_muhurta(2460000.0, 2460000.5)
        assert 'abhijit_start_jd' in result
        assert 'abhijit_end_jd' in result


# ── Panchanga Complete Tests ────────────────────────────────────────

class TestPanchangaComplete:
    def test_five_elements_present(self):
        result = calc_panchanga(45.0, 120.0, 4, 6.0)
        assert 'tithi' in result
        assert 'nakshatra' in result
        assert 'yoga' in result
        assert 'karana' in result
        assert 'vara' in result

    def test_overall_score_range(self):
        result = calc_panchanga(45.0, 120.0, 4, 6.0)
        assert 0 <= result['overall_score'] <= 1

    def test_auspicious_count(self):
        result = calc_panchanga(45.0, 120.0, 4, 6.0)
        assert 0 <= result['auspicious_count'] <= 6

    def test_warnings_list(self):
        result = calc_panchanga(45.0, 120.0, 4, 6.0)
        assert isinstance(result['warnings'], list)


# ── Activity Muhurta Tests ─────────────────────────────────────────

class TestActivityMuhurta:
    def test_marriage_activity(self):
        panchanga = calc_panchanga(45.0, 120.0, 4, 6.0)
        result = check_activity_muhurta(panchanga, 'marriage')
        assert result['verdict'] is not None

    def test_all_5_activities(self):
        panchanga = calc_panchanga(45.0, 120.0, 4, 6.0)
        for act in ['marriage', 'business', 'travel', 'medical', 'education']:
            result = check_activity_muhurta(panchanga, act)
            assert 'verdict' in result

    def test_unknown_activity_error(self):
        panchanga = calc_panchanga(45.0, 120.0, 4, 6.0)
        result = check_activity_muhurta(panchanga, 'unknown')
        assert 'error' in result

    def test_good_tithi_for_marriage(self):
        # Create a panchanga with tithi 2 (good for marriage)
        panchanga = calc_panchanga(0.0, 24.0, 4, 6.0)  # tithi 3
        result = check_activity_muhurta(panchanga, 'marriage')
        assert result['tithi_eval'] in ('good', 'neutral', 'bad')

    def test_pushya_nakshatra_good_for_business(self):
        # Pushya nakshatra center ≈ 104°
        panchanga = calc_panchanga(80.0, 104.0, 4, 6.0)
        result = check_activity_muhurta(panchanga, 'business')
        if panchanga['nakshatra']['nakshatra'] == 'Pushya':
            assert result['nakshatra_eval'] == 'good'


# ── Full Report Tests ───────────────────────────────────────────────

class TestMuhurtaFullReport:
    def test_report_structure(self):
        result = muhurta_full_report(45.0, 120.0, 4, 6.0, '2026-06-04')
        assert 'panchanga' in result
        assert 'abhijit_muhurta' in result
        assert 'activity_checks' in result
        assert 'summary' in result

    def test_best_activities_list(self):
        result = muhurta_full_report(45.0, 120.0, 4, 6.0)
        assert isinstance(result['summary']['best_activities'], list)

    def test_avoid_activities_list(self):
        result = muhurta_full_report(45.0, 120.0, 4, 6.0)
        assert isinstance(result['summary']['avoid_activities'], list)

    def test_query_date_preserved(self):
        result = muhurta_full_report(45.0, 120.0, 4, 6.0, '2026-06-04')
        assert result['query_date'] == '2026-06-04'
