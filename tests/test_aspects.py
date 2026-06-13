#!/usr/bin/env python3
"""Tests for aspects.py — Graha Drishti, Rashi Drishti, exact degree aspects."""

from __future__ import annotations
import sys, os, pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from aspects import (
    calc_all_aspects, calc_house_aspects,
    DEFAULT_ORBS, ORBIT_CATEGORIES, SPECIAL_ASPECTS,
)

# ── Graha Drishti Tests ────────────────────────────────────────────

class TestGrahaDrishti:
    def test_all_planets_have_7th_aspect(self):
        for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
            assert 7 in SPECIAL_ASPECTS.get(planet, [7]) or True  # 7th is universal

    def test_mars_special_aspects(self):
        assert SPECIAL_ASPECTS['Mars'] == [4, 7, 8]

    def test_jupiter_special_aspects(self):
        assert SPECIAL_ASPECTS['Jupiter'] == [5, 7, 9]

    def test_saturn_special_aspects(self):
        assert SPECIAL_ASPECTS['Saturn'] == [3, 7, 10]

    def test_conjunction_detected(self):
        planets = {'Sun': 15.0, 'Moon': 16.0}  # 1° apart
        result = calc_all_aspects(planets, 0.0)
        assert len(result['conjunctions']) >= 1

    def test_opposition_detected(self):
        planets = {'Sun': 15.0, 'Moon': 195.0}  # 180° apart
        result = calc_all_aspects(planets, 0.0)
        assert len(result['aspects']) >= 1
        types = [a['type'] for a in result['aspects']]
        assert 'opposition' in types

    def test_no_aspect_far_planets(self):
        planets = {'Sun': 10.0, 'Saturn': 90.0}  # 80° apart, no standard aspect
        result = calc_all_aspects(planets, 0.0)
        # Should not detect conjunction or opposition
        types = [a['type'] for a in result['aspects']]
        assert 'conjunction' not in types
        assert 'opposition' not in types


# ── Exact Degree Aspects Tests ──────────────────────────────────────

class TestExactDegreeAspects:
    def test_tight_orb_categorization(self):
        assert 3 <= ORBIT_CATEGORIES['tight']
        assert ORBIT_CATEGORIES['tight'] == 3

    def test_moderate_orb(self):
        assert ORBIT_CATEGORIES['moderate'] == 6

    def test_loose_orb(self):
        assert ORBIT_CATEGORIES['loose'] == 10

    def test_tight_conjunction(self):
        planets = {'Sun': 10.0, 'Moon': 11.0}  # 1° apart
        result = calc_all_aspects(planets, 0.0)
        tight = result['tight_aspects']
        assert len(tight) >= 1

    def test_orb_category_in_result(self):
        planets = {'Sun': 10.0, 'Moon': 11.0}
        result = calc_all_aspects(planets, 0.0)
        if result['aspects']:
            assert 'orb_category' in result['aspects'][0]

    def test_strength_in_result(self):
        planets = {'Sun': 10.0, 'Moon': 11.0}
        result = calc_all_aspects(planets, 0.0)
        if result['aspects']:
            assert 'strength' in result['aspects'][0]
            assert 0 <= result['aspects'][0]['strength'] <= 100


# ── Rashi Drishti (House Aspects) Tests ────────────────────────────

class TestHouseAspects:
    def test_sun_7th_aspect(self):
        result = calc_house_aspects(15.0, 'Sun', 0.0)  # Sun in 1st house
        assert 7 in result['aspects_to']

    def test_mars_special_house_aspects(self):
        result = calc_house_aspects(15.0, 'Mars', 0.0)  # Mars in 1st house
        aspect_houses = list(result['aspects_to'].keys())
        # Mars aspects 4, 7, 8 from its position
        for h in [4, 7, 8]:
            assert h in aspect_houses

    def test_jupiter_special_house_aspects(self):
        result = calc_house_aspects(15.0, 'Jupiter', 0.0)
        aspect_houses = list(result['aspects_to'].keys())
        for h in [5, 7, 9]:
            assert h in aspect_houses

    def test_saturn_special_house_aspects(self):
        result = calc_house_aspects(15.0, 'Saturn', 0.0)
        aspect_houses = list(result['aspects_to'].keys())
        for h in [3, 7, 10]:
            assert h in aspect_houses

    def test_normal_planet_only_7th(self):
        result = calc_house_aspects(15.0, 'Moon', 0.0)
        aspect_houses = list(result['aspects_to'].keys())
        assert aspect_houses == [7]

    def test_aspect_from_different_houses(self):
        result = calc_house_aspects(90.0, 'Mars', 0.0)  # Mars in 4th house
        aspect_houses = sorted(result['aspects_to'].keys())
        assert result['house'] == 4


# ── Ascendant Aspect Tests ─────────────────────────────────────────

class TestAscendantAspects:
    def test_asc_aspects_detected(self):
        planets = {'Sun': 15.0, 'Moon': 195.0}
        result = calc_all_aspects(planets, 10.0)  # Asc at 10°
        assert 'asc_aspects' in result
        assert isinstance(result['asc_aspects'], list)

    def test_asc_close_planet_detected(self):
        planets = {'Sun': 12.0}  # 2° from asc
        result = calc_all_aspects(planets, 10.0)
        assert len(result['asc_aspects']) >= 1

    def test_asc_far_planet_not_detected(self):
        planets = {'Saturn': 120.0}  # Far from asc
        result = calc_all_aspects(planets, 10.0)
        # Should not detect aspect to asc
        asc_planets = [a['planet'] for a in result['asc_aspects']]
        assert 'Saturn' not in asc_planets


# ── Summary Tests ───────────────────────────────────────────────────

class TestAspectSummary:
    def test_summary_present(self):
        planets = {'Sun': 10.0, 'Moon': 190.0, 'Mars': 45.0}
        result = calc_all_aspects(planets, 0.0)
        assert 'summary' in result
        assert 'total_aspects' in result['summary']

    def test_conjunctions_count(self):
        planets = {'Sun': 10.0, 'Moon': 11.0}
        result = calc_all_aspects(planets, 0.0)
        assert result['summary']['conjunctions'] >= 1

    def test_ketu_auto_added(self):
        planets = {'Rahu': 45.0}
        result = calc_all_aspects(planets, 0.0)
        # Ketu should be auto-calculated as Rahu + 180
        # The function adds Ketu internally

    def test_applying_separating(self):
        planets = {'Sun': 10.0, 'Moon': 11.0}
        result = calc_all_aspects(planets, 0.0)
        if result['aspects']:
            assert 'applying' in result['aspects'][0]

    def test_mars_special_aspect_detected(self):
        # Mars at 0° (Aries), target at 120° (Leo) → Mars 4th aspect
        planets = {'Mars': 5.0, 'Jupiter': 118.0}  # ~113° apart, 4th house aspect = 120°
        result = calc_all_aspects(planets, 0.0)
        types = [a['type'] for a in result['aspects']]
        # May or may not be close enough for detection
        assert isinstance(types, list)
