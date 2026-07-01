#!/usr/bin/env python3
"""Standalone Swiss Ephemeris helpers must not inherit stale ayanamsa state."""

from __future__ import annotations

from datetime import datetime
import os
import sys

import pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import swisseph as swe

from cmd_muhurta import _get_sun_moon_lons
from jyotish_engine import _apply_ayanamsa
from muhurta import _swisseph_sun_moon_lon
from solar_return import _get_sun_lon_jd
from solar_return import _datetime_to_jd_ut, _jd_to_datetime
from transit_trigger import _datetime_to_jd, _get_planet_lon_swe


def _angular_diff(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def _sidereal_lon(jd: float, pid: int, sid_mode: int) -> float:
    swe.set_sid_mode(sid_mode)
    return swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0] % 360


def _first_lon(value) -> float:
    if isinstance(value, (tuple, list)):
        return float(value[0])
    return float(value)


@pytest.fixture(autouse=True)
def _reset_lahiri():
    yield
    _apply_ayanamsa('lahiri')


def test_transit_helper_defaults_to_lahiri_after_global_raman_switch():
    jd = _datetime_to_jd(datetime(2026, 1, 1, 0, 0))
    expected_lahiri = _sidereal_lon(jd, swe.SUN, swe.SIDM_LAHIRI)
    stale_raman = _sidereal_lon(jd, swe.SUN, swe.SIDM_RAMAN)
    assert _angular_diff(expected_lahiri, stale_raman) > 1.0

    _apply_ayanamsa('raman')
    actual = _get_planet_lon_swe('Sun', jd)

    assert _angular_diff(actual, expected_lahiri) < 1e-9


def test_solar_return_sun_helper_defaults_to_lahiri_after_global_raman_switch():
    jd = swe.julday(2026, 4, 17, 6.0)
    expected_lahiri = _sidereal_lon(jd, swe.SUN, swe.SIDM_LAHIRI)

    _apply_ayanamsa('raman')
    actual = _get_sun_lon_jd(jd)

    assert _angular_diff(actual, expected_lahiri) < 1e-9


def test_solar_return_julian_datetime_helpers_work_without_greg_flag_constant():
    dt = datetime(2026, 4, 17, 6, 30, 0)

    jd = _datetime_to_jd_ut(dt)
    roundtrip = _jd_to_datetime(jd)

    assert roundtrip.year == 2026
    assert roundtrip.month == 4
    assert roundtrip.day == 17
    assert roundtrip.hour == 6
    assert roundtrip.minute == 30


def test_muhurta_sun_moon_helper_defaults_to_lahiri_after_global_raman_switch():
    jd = swe.julday(2026, 6, 25, 4.0)
    expected_sun = _sidereal_lon(jd, swe.SUN, swe.SIDM_LAHIRI)
    expected_moon = _sidereal_lon(jd, swe.MOON, swe.SIDM_LAHIRI)

    _apply_ayanamsa('raman')
    actual = _swisseph_sun_moon_lon(jd)

    assert actual is not None
    assert _angular_diff(actual[0], expected_sun) < 1e-9
    assert _angular_diff(actual[1], expected_moon) < 1e-9


def test_cmd_muhurta_helper_defaults_to_lahiri_after_global_raman_switch():
    jd = swe.julday(2026, 6, 25, 4)
    expected_sun = _sidereal_lon(jd, swe.SUN, swe.SIDM_LAHIRI)
    expected_moon = _sidereal_lon(jd, swe.MOON, swe.SIDM_LAHIRI)

    _apply_ayanamsa('raman')
    sun, moon, has_swe = _get_sun_moon_lons(2026, 6, 25, hour=4)

    assert has_swe is True
    assert _angular_diff(_first_lon(sun), expected_sun) < 1e-9
    assert _angular_diff(_first_lon(moon), expected_moon) < 1e-9
