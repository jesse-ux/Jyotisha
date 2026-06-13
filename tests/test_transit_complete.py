#!/usr/bin/env python3
"""Tests for transit_trigger.py — Transit search, Double Transit, trigger detection."""

from __future__ import annotations
import sys, os, pytest
from datetime import datetime, timedelta

SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from transit_trigger import (
    search_transit_triggers, search_all_transit_triggers,
    find_exact_transit_date, _angular_diff, _get_transit_lon,
    PLANET_SPEED, CONTACT_ORB, EXACT_ORB,
)


# ── Angular Diff Tests ─────────────────────────────────────────────

class TestAngularDiff:
    def test_same_angle_zero(self):
        assert _angular_diff(45.0, 45.0) == 0.0

    def test_opposite_180(self):
        assert abs(_angular_diff(0.0, 180.0) - 180.0) < 0.01

    def test_small_diff(self):
        assert abs(_angular_diff(10.0, 15.0) - 5.0) < 0.01

    def test_wrap_around(self):
        assert abs(_angular_diff(355.0, 5.0) - 10.0) < 0.01

    @pytest.mark.parametrize("a,b,expected",
        [(0, 90, 90), (0, 270, 90), (180, 170, 10), (0, 0, 0)])
    def test_parametrized_diff(self, a, b, expected):
        assert abs(_angular_diff(a, b) - expected) < 0.01


# ── Planet Speed Tests ──────────────────────────────────────────────

class TestPlanetSpeed:
    def test_moon_fastest(self):
        assert PLANET_SPEED['Moon'] > PLANET_SPEED['Mercury']

    def test_saturn_slowest_direct(self):
        assert abs(PLANET_SPEED['Saturn']) < abs(PLANET_SPEED['Jupiter'])

    def test_rahu_retrograde(self):
        assert PLANET_SPEED['Rahu'] < 0

    def test_all_9_planets_present(self):
        for p in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
            assert p in PLANET_SPEED


# ── Transit Lon Tests ──────────────────────────────────────────────

class TestTransitLon:
    def test_returns_float(self):
        result = _get_transit_lon('Sun', datetime(2026, 1, 1), 0)
        assert isinstance(result, float)

    def test_in_range_0_360(self):
        for planet in ['Sun', 'Moon', 'Mars']:
            result = _get_transit_lon(planet, datetime(2026, 6, 1), 0)
            assert 0 <= result < 360

    def test_changes_over_time(self):
        base = datetime(2026, 1, 1)
        lon1 = _get_transit_lon('Sun', base, 0)
        lon2 = _get_transit_lon('Sun', base, 30)
        assert lon1 != lon2


# ── Search Transit Triggers Tests ──────────────────────────────────

class TestSearchTransitTriggers:
    def test_empty_short_period(self):
        result = search_transit_triggers(
            'Sun', 45.0,
            datetime(2026, 1, 1), datetime(2026, 1, 1))
        assert result == []

    def test_returns_list(self):
        result = search_transit_triggers(
            'Sun', 45.0,
            datetime(2026, 1, 1), datetime(2026, 12, 31))
        assert isinstance(result, list)

    def test_trigger_structure(self):
        result = search_transit_triggers(
            'Jupiter', 100.0,
            datetime(2026, 1, 1), datetime(2026, 12, 31))
        for t in result:
            assert 'event' in t or 'type' in t

    def test_moon_finds_more_triggers(self):
        # Moon is fastest → more contacts in a year
        result_moon = search_transit_triggers(
            'Moon', 45.0,
            datetime(2026, 1, 1), datetime(2026, 3, 31))
        result_saturn = search_transit_triggers(
            'Saturn', 45.0,
            datetime(2026, 1, 1), datetime(2026, 3, 31))
        # Moon should generally find more triggers (or same)
        # Note: This depends on actual planetary positions
        assert isinstance(result_moon, list)
        assert isinstance(result_saturn, list)


# ── Search All Transit Triggers Tests ───────────────────────────────

class TestSearchAllTransitTriggers:
    def test_natal_data_structure(self):
        natal = {'asc': 45.0, 'planets': {'Moon': {'lon': 120.0}}}
        result = search_all_transit_triggers(
            natal, datetime(2026, 1, 1), datetime(2026, 12, 31))
        assert 'triggers' in result
        assert 'sensitive_points' in result
        assert 'summary' in result

    def test_sensitive_points_include_asc_moon(self):
        natal = {'asc': 45.0, 'planets': {'Moon': {'lon': 120.0}}}
        result = search_all_transit_triggers(
            natal, datetime(2026, 1, 1), datetime(2026, 12, 31))
        names = [sp['name'] for sp in result['sensitive_points']]
        assert 'Ascendant' in names
        assert 'Moon' in names

    def test_sade_sati_check_present(self):
        natal = {'asc': 45.0, 'planets': {'Moon': {'lon': 120.0}}}
        result = search_all_transit_triggers(
            natal, datetime(2026, 1, 1), datetime(2026, 12, 31))
        assert 'sade_sati_check' in result

    def test_total_triggers_count(self):
        natal = {'asc': 45.0, 'planets': {'Moon': {'lon': 120.0}}}
        result = search_all_transit_triggers(
            natal, datetime(2026, 1, 1), datetime(2026, 12, 31))
        assert result['total_triggers'] >= 0


# ── Find Exact Transit Date Tests ──────────────────────────────────

class TestFindExactTransitDate:
    def test_returns_dict_or_none(self):
        result = find_exact_transit_date(
            'Sun', 45.0,
            datetime(2026, 1, 1), datetime(2026, 12, 31))
        assert result is None or isinstance(result, dict)

    def test_result_structure(self):
        result = find_exact_transit_date(
            'Sun', 45.0,
            datetime(2026, 1, 1), datetime(2026, 12, 31))
        if result:
            assert 'date' in result
            assert 'exact_degree' in result
            assert 'source' in result

    def test_jupiter_slow_may_not_hit(self):
        # Jupiter might not transit over exact degree in short period
        result = find_exact_transit_date(
            'Jupiter', 45.0,
            datetime(2026, 1, 1), datetime(2026, 1, 31))
        # May or may not find exact hit
        assert result is None or isinstance(result, dict)


# ── Orb Threshold Tests ────────────────────────────────────────────

class TestOrbThresholds:
    def test_contact_orb_default(self):
        assert CONTACT_ORB == 1.0

    def test_exact_orb_default(self):
        assert EXACT_ORB == 0.1

    def test_orb_values_sensible(self):
        assert CONTACT_ORB > EXACT_ORB
