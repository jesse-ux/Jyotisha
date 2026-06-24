#!/usr/bin/env python3
"""KP SubLord oracle tests based on VedicAstro KP_SL_Divisions.csv.

These tests protect the most precision-sensitive part of KP timing: the
Nakshatra/SubLord degree partitions. A wrong boundary changes event houses and
therefore changes concrete predictions.
"""
import csv
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from kp_system import get_kp_lords

SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

CSV_PATH = os.path.join(
    os.path.dirname(__file__),
    '..',
    'references',
    'open_source_sources',
    'VedicAstro',
    'vedicastro',
    'data',
    'KP_SL_Divisions.csv',
)


def _dms_to_degree(value: str) -> float:
    """Convert DMS string like 03:40:00 into decimal degrees."""
    parts = [p for p in value.strip().split(':') if p != '']
    deg, minute, second = [float(x) for x in parts[:3]]
    return deg + minute / 60.0 + second / 3600.0


def _load_rows(limit=None):
    if not os.path.exists(CSV_PATH):
        pytest.skip(f"VedicAstro KP oracle fixture not available: {CSV_PATH}")
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    return rows if limit is None else rows[:limit]


def _absolute_midpoint(row):
    sign_offset = SIGNS.index(row['Sign']) * 30.0
    start = _dms_to_degree(row['From_DMS'])
    end = _dms_to_degree(row['To_DMS'])
    return sign_offset + (start + end) / 2.0


def test_kp_sublord_matches_vedicastro_csv_first_36_segments():
    """First 36 segments cover four complete Nakshatras across Aries/Taurus."""
    for row in _load_rows(limit=36):
        degree = _absolute_midpoint(row)
        actual = get_kp_lords(degree)
        assert actual['sign'] == row['Sign']
        assert actual['rasi_lord'] == row['RasiLord']
        assert actual['nakshatra_lord'] == row['NakshatraLord']
        assert actual['sub_lord'] == row['SubLord'], (
            f"degree={degree:.6f} expected SL={row['SubLord']} got {actual['sub_lord']} row={row}"
        )


def test_kp_sublord_near_internal_boundaries():
    """Boundary +/- epsilon should fall into adjacent CSV rows."""
    rows = _load_rows(limit=12)
    epsilon = 1e-6
    for i in range(1, len(rows)):
        prev_row = rows[i - 1]
        row = rows[i]
        if prev_row['Sign'] != row['Sign']:
            continue
        boundary = SIGNS.index(row['Sign']) * 30.0 + _dms_to_degree(row['From_DMS'])
        before = get_kp_lords(boundary - epsilon)
        after = get_kp_lords(boundary + epsilon)
        assert before['sub_lord'] == prev_row['SubLord']
        assert after['sub_lord'] == row['SubLord']


def test_kp_lords_wrap_at_360_degrees():
    """360° and 0° should both resolve to Aries/Ashvini/Ketu segment."""
    zero = get_kp_lords(0.0)
    wrapped = get_kp_lords(360.0)
    assert zero['sign'] == wrapped['sign'] == 'Aries'
    assert zero['nakshatra_lord'] == wrapped['nakshatra_lord'] == 'Ketu'
    assert zero['sub_lord'] == wrapped['sub_lord'] == 'Ketu'
