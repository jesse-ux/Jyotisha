#!/usr/bin/env python3
"""Precision tests for Transit trigger search.

The previous implementation used a mean-speed placeholder. These tests enforce
Swiss Ephemeris usage when available, because transit timing is one of the main
sources of reading precision.
"""
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from transit_trigger import (
    _angular_diff,
    _datetime_to_jd,
    _get_planet_lon_swe,
    _get_transit_lon_precise,
    find_exact_transit_date,
    search_transit_triggers,
)


def test_precise_longitude_uses_swiss_ephemeris_when_available():
    dt = datetime(2026, 1, 1, 0, 0)
    lon, source = _get_transit_lon_precise('Jupiter', dt, dt)
    assert source == 'swiss_ephemeris_lahiri'
    assert 0.0 <= lon < 360.0


def test_ketu_is_180_degrees_from_rahu():
    jd = _datetime_to_jd(datetime(2026, 1, 1, 0, 0))
    rahu = _get_planet_lon_swe('Rahu', jd)
    ketu = _get_planet_lon_swe('Ketu', jd)
    assert _angular_diff((rahu + 180.0) % 360.0, ketu) < 1e-6


def test_search_transit_triggers_reports_swiss_ephemeris_source():
    start = datetime(2026, 1, 1, 0, 0)
    target, _ = _get_transit_lon_precise('Moon', start + timedelta(hours=12), start)
    hits = search_transit_triggers('Moon', target, start, start + timedelta(days=1), orb=0.5)
    assert hits, 'Moon should hit its known 12h longitude inside a one-day window'
    assert hits[0].get('source') == 'swiss_ephemeris_lahiri'


def test_find_exact_transit_date_uses_precise_source_for_sun():
    start = datetime(2026, 3, 1, 0, 0)
    end = datetime(2026, 3, 3, 0, 0)
    target, _ = _get_transit_lon_precise('Sun', start + timedelta(days=1), start)
    hit = find_exact_transit_date('Sun', target, start, end)
    assert hit is not None
    assert hit['source'] == 'swiss_ephemeris_lahiri'
    assert _angular_diff(hit['exact_degree'], target) < 0.2
