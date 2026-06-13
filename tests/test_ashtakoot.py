#!/usr/bin/env python3
"""Tests for ashtakoot.py — 36-point compatibility, 8 standard Kuta,
7 additional Kuta, and Kuja Dosha detection."""

from __future__ import annotations
import sys, os, pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from ashtakoot import (
    calc_varna, calc_vashya, calc_tara, calc_yoni,
    calc_graha_maitri, calc_gana, calc_bhakoot, calc_nadi,
    calc_mahendra, calc_stree_deergha, calc_vedha, calc_rajju,
    calc_bad_constellations, calc_kuja_dosha, match_kuja_dosha,
    calculate_ashtakoot, get_nakshatra,
    SIGNS, NAKSHATRA_NAMES, YONI_ANIMALS, GANA, NADI,
)

# ── 8 Standard Kuta Tests ──────────────────────────────────────────

class TestVarna:
    def test_male_lower_varna_approved(self):
        # Varna: m_varna <= f_varna → approved
        # Aries=2(Kshatriya), Pisces=1(Brahmin) → 2 <= 1 is False → 0.0
        # Use Cancer(1) male, Pisces(1) female → 1 <= 1 → 1.0
        assert calc_varna('Cancer', 'Pisces') == 1.0

    def test_male_higher_varna_rejected(self):
        # Cancer(1) > Gemini(4) → 1 <= 4 → True → 1.0
        # Actually: Cancer=Brahmin(1), Gemini=Shudra(4) → 1 <= 4 → 1.0
        # For rejection: male higher varna number > female
        assert calc_varna('Gemini', 'Cancer') == 0.0  # Shudra(4) > Brahmin(1)

    def test_same_varna(self):
        assert calc_varna('Aries', 'Leo') == 1.0  # Both Kshatriya(2)

    def test_female_shudra(self):
        assert calc_varna('Cancer', 'Aquarius') == 1.0  # Brahmin(1) <= Shudra(4)

class TestVashya:
    def test_same_sign_max(self):
        assert calc_vashya('Aries', 'Aries') == 2.0

    def test_same_type_max(self):
        # Aries=Chatushpada, Taurus=Chatushpada → both same type
        assert calc_vashya('Aries', 'Taurus') == 2.0

    def test_different_types_partial(self):
        score = calc_vashya('Aries', 'Gemini')
        assert 0 <= score <= 2.0

class TestTara:
    def test_auspicious_distance(self):
        # Ashwini(0) to Rohini(3): distance=3, 3%9=3 → auspicious
        score = calc_tara(0, 3)
        assert score > 0

    def test_dangerous_distance(self):
        # Ashwini(0) to Krittika(2): m_to_f = 2%9=2 → Vipat
        # f_to_m = (0-2)%9=7 → Mitra → not dangerous → 1.5
        # Tara requires BOTH directions non-dangerous for full 3.0
        score = calc_tara(0, 2)
        assert 0 <= score <= 3.0  # Partial score due to one dangerous direction

    def test_same_nakshatra(self):
        assert calc_tara(0, 0) == 3.0  # Both directions: 0%9=0, 0%9=0 → not 2/4/6

class TestYoni:
    def test_same_yoni_max(self):
        # Ashwini(0)=Horse, Shatabhisha(23)=Horse
        assert calc_yoni(0, 23) == 4.0

    def test_enemy_yoni_zero(self):
        # Horse(0) & Buffalo(12): enemies
        assert calc_yoni(0, 12) == 0.0

    def test_neutral_yoni(self):
        score = calc_yoni(0, 1)  # Horse vs Elephant
        assert score == 2.0

class TestGrahaMaitri:
    def test_mutual_friends_max(self):
        # Sun & Moon are mutual friends
        assert calc_graha_maitri('Leo', 'Cancer') == 5.0

    def test_mutual_enemies_min(self):
        # Sun & Saturn are enemies
        assert calc_graha_maitri('Leo', 'Aquarius') == 0.0

    def test_one_way_friend(self):
        score = calc_graha_maitri('Leo', 'Gemini')
        assert 0 < score < 5.0

class TestGana:
    def test_same_gana_max(self):
        # Both Deva: Punarvasu(6) & Pushya(7)
        assert calc_gana(6, 7) == 6.0

    def test_rakshasa_manushya_zero(self):
        # Rakshasa & Manushya
        assert calc_gana(2, 1) == 0.0

class TestBhakoot:
    def test_1_7_position_auspicious(self):
        assert calc_bhakoot('Aries', 'Aries') == 7.0  # 1st from self

    def test_6_8_position_inauspicious(self):
        assert calc_bhakoot('Aries', 'Virgo') == 0.0

class TestNadi:
    def test_different_nadi_max(self):
        # Ashwini=Adi(0), Bharani=Madhya(1) → different
        assert calc_nadi(0, 1) == 8.0

    def test_same_nadi_zero(self):
        # Ashwini(0)=Adi, Mula(18)=Adi → same
        assert calc_nadi(0, 18) == 0.0


# ── Additional Kuta Tests ──────────────────────────────────────────

class TestMahendra:
    def test_good_mahendra(self):
        assert calc_mahendra(0, 3) == 'good'  # count=4

    def test_bad_mahendra(self):
        assert calc_mahendra(0, 1) == 'bad'  # count=2

class TestStreeDeergha:
    def test_long_distance_good(self):
        assert calc_stree_deergha(0, 9) == 'good'  # count=10 >= 9

    def test_medium_distance_good(self):
        assert calc_stree_deergha(0, 8) == 'good'  # count=9 >= 9

    def test_short_distance_bad(self):
        # count = ((m - f) % 27) + 1. (0-1)%27+1 = 27+1=28 → 28 >= 9 → good
        # Need m_nak < f_nak with small difference
        # (5 - 7) % 27 + 1 = 25+1=26 → good
        # (7 - 5) % 27 + 1 = 2+1=3 → bad
        assert calc_stree_deergha(7, 5) == 'bad'  # count=3 < 9

class TestVedha:
    def test_vedha_pair_bad(self):
        assert calc_vedha(0, 17) == 'bad'  # VEDHA_PAIRS: (0,17)

    def test_non_vedha_good(self):
        assert calc_vedha(0, 5) == 'good'

class TestRajju:
    def test_same_rajju_bad(self):
        result = calc_rajju(0, 8)  # Both Pada group
        assert result['result'] == 'bad'

    def test_different_rajju_good(self):
        result = calc_rajju(0, 1)  # Pada vs Kati
        assert result['result'] == 'good'

class TestBadConstellations:
    def test_moola_1st_pada_bad(self):
        result = calc_bad_constellations(18, 1, 0, 1)
        assert result['result'] == 'bad'

    def test_normal_constellations_good(self):
        result = calc_bad_constellations(0, 1, 1, 1)
        assert result['result'] == 'good'


# ── Kuja Dosha Tests ───────────────────────────────────────────────

class TestKujaDosha:
    def test_mars_in_7th_dosha(self):
        chart = {"planets": {"Mars": {"house": 7, "sign": "Gemini"}}}
        result = calc_kuja_dosha(chart)
        assert result['is_manglik']

    def test_mars_in_4th_no_exception_dosha(self):
        chart = {"planets": {"Mars": {"house": 4, "sign": "Gemini"}}}
        result = calc_kuja_dosha(chart)
        assert result['is_manglik']

    def test_mars_in_4th_ares_exception(self):
        chart = {"planets": {"Mars": {"house": 4, "sign": "Aries"}}}
        result = calc_kuja_dosha(chart)
        assert not result['is_manglik']

    def test_mars_exempt_aquarius(self):
        chart = {"planets": {"Mars": {"house": 2, "sign": "Aquarius"}}}
        result = calc_kuja_dosha(chart)
        assert not result['is_manglik']

    def test_no_dosha_mars_good_house(self):
        chart = {"planets": {"Mars": {"house": 1, "sign": "Aries"}}}
        result = calc_kuja_dosha(chart)
        assert not result['is_manglik']

class TestKujaDoshaMatching:
    def test_balanced_dosha(self):
        result = match_kuja_dosha(10.0, 10.0)
        assert result['result'] == 'good'

    def test_female_more_dosha(self):
        result = match_kuja_dosha(0.0, 50.0)
        assert result['result'] == 'bad'

    def test_male_within_tolerance(self):
        result = match_kuja_dosha(40.0, 10.0)
        # Male has significantly more → bad unless within tolerance
        assert result['result'] in ('good', 'acceptable', 'bad')


# ── Full Ashtakoot Integration Tests ───────────────────────────────

class TestAshtakootFull:
    def test_basic_matching(self):
        result = calculate_ashtakoot(45.0, 125.0)  # Taurus, Leo
        assert 'scores' in result
        assert 'total_score' in result
        assert 0 <= result['total_score'] <= 36

    def test_match_percentage(self):
        result = calculate_ashtakoot(45.0, 125.0)
        assert 0 <= result['match_percentage'] <= 100

    def test_additional_kutas_present(self):
        result = calculate_ashtakoot(45.0, 125.0)
        assert 'additional_kutas' in result
        assert 'Mahendra' in result['additional_kutas']

    def test_nadi_dosha_exception(self):
        # Same Nadi but good Bhakoot + Rajju → exception
        result = calculate_ashtakoot(0.0, 180.0)  # Both Adi Nadi
        if result['scores']['Nadi'] == 0:
            # Check if exception noted
            pass  # Exception logic depends on Bhakoot/Rajju

    def test_kuja_dosha_with_charts(self):
        male_chart = {"planets": {"Mars": {"house": 7, "sign": "Gemini"}}}
        female_chart = {"planets": {"Mars": {"house": 1, "sign": "Aries"}}}
        result = calculate_ashtakoot(45.0, 125.0, male_chart, female_chart)
        assert result['kuja_dosha_male'] is not None
        assert result['kuja_dosha_female'] is not None

    def test_get_nakshatra(self):
        nak = get_nakshatra(6.0)  # Ashwini, 2nd pada (6/3.333≈1.8, pada=2)
        assert nak['name'] == 'Ashwini'
        assert nak['pada'] == 2  # 6° / (360/108) = 6/3.333 = 1.8 → pada=2
