#!/usr/bin/env python3
"""Tests for bhava_chalit.py — unequal house boundaries and Rashi vs Bhava shifts."""

from __future__ import annotations
import os
import sys

SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from bhava_chalit import BhavaChalitCalculator


def test_equal_house_cusps_are_30_degrees_apart():
    calc = BhavaChalitCalculator()
    cusps = calc.calculate_cusps(asc_lon=12.5, mc_lon=280.0, house_system='equal')
    assert len(cusps) == 12
    assert cusps[0] == 12.5
    assert cusps[1] == 42.5
    assert cusps[11] == 342.5


def test_whole_sign_cusps_use_sign_midpoints():
    calc = BhavaChalitCalculator()
    cusps = calc.calculate_cusps(asc_lon=28.0, mc_lon=270.0, house_system='whole_sign')
    assert cusps[:3] == [15, 45, 75]


def test_sandhis_for_equal_house_wrap_correctly():
    calc = BhavaChalitCalculator()
    cusps = calc.calculate_cusps(asc_lon=15.0, mc_lon=270.0, house_system='equal')
    sandhis = calc.calculate_sandhis(cusps)
    assert len(sandhis) == 12
    assert sandhis[0] == 0.0
    assert sandhis[1] == 30.0
    assert sandhis[11] == 330.0


def test_planet_bhava_assignment_equal_house():
    calc = BhavaChalitCalculator()
    cusps = calc.calculate_cusps(asc_lon=15.0, mc_lon=270.0, house_system='equal')
    sandhis = calc.calculate_sandhis(cusps)
    assert calc._planet_bhava(1.0, sandhis) == 1
    assert calc._planet_bhava(31.0, sandhis) == 2
    assert calc._planet_bhava(359.0, sandhis) == 12


def test_bhava_chart_reports_shifted_planets():
    calc = BhavaChalitCalculator()
    planet_lons = {'Sun': 29.0, 'Moon': 31.0, 'Mars': 359.0}
    chart = calc.get_bhava_chalit_chart(
        planet_lons=planet_lons,
        asc_lon=15.0,
        mc_lon=270.0,
        house_system='equal',
    )
    assert chart['summary']['total_planets'] == 3
    assert chart['planets']['Sun']['rashi_house'] == 1
    assert chart['planets']['Sun']['bhava_house'] == 1
    assert chart['planets']['Moon']['bhava_house'] == 2
    assert chart['planets']['Mars']['bhava_house'] == 12


def test_compare_rashi_vs_bhava_contains_boundaries_and_shifts():
    calc = BhavaChalitCalculator()
    result = calc.compare_rashi_vs_bhava(
        {'Sun': 29.0, 'Moon': 31.0},
        asc_lon=15.0,
        mc_lon=270.0,
        house_system='equal',
    )
    assert result['house_system'] == 'equal'
    assert 'boundaries' in result
    assert 'rashi_chart' in result
    assert 'bhava_chart' in result
    assert isinstance(result['shifts'], list)


def test_porophyry_like_system_returns_12_cusps_and_houses():
    calc = BhavaChalitCalculator()
    boundaries = calc.calculate_bhava_boundaries(
        asc_lon=100.0,
        mc_lon=20.0,
        house_system='sripati',
    )
    assert len(boundaries['cusps']) == 12
    assert len(boundaries['sandhis']) == 12
    assert len(boundaries['houses']) == 12
    assert all(0 <= h['span_degrees'] <= 360 for h in boundaries['houses'])


def test_invalid_house_system_raises():
    calc = BhavaChalitCalculator()
    try:
        calc.calculate_cusps(asc_lon=0, mc_lon=90, house_system='invalid')
    except ValueError as exc:
        assert '不支持的宫位制' in str(exc)
    else:
        raise AssertionError('expected ValueError')
