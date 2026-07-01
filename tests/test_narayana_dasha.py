#!/usr/bin/env python3
"""Narayana Dasha regression tests."""

import os
import sys

SCRIPT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, SCRIPT_DIR)

from narayana_dasha import calc_narayana_antardasha, get_current_narayana_dasha


def _sample_mahadashas():
    return [
        {"sign": "Aries", "sign_idx": 0, "lord": "Mars", "years": 4, "start_age": 0.0, "end_age": 4.0},
        {"sign": "Taurus", "sign_idx": 1, "lord": "Venus", "years": 8, "start_age": 4.0, "end_age": 12.0},
        {"sign": "Gemini", "sign_idx": 2, "lord": "Mercury", "years": 12, "start_age": 12.0, "end_age": 24.0},
    ]


def test_narayana_antardasha_uses_parent_absolute_age_axis():
    ads = calc_narayana_antardasha(_sample_mahadashas(), 1)

    assert ads[0]["sign"] == "Taurus"
    assert ads[0]["start_age"] == 4.0
    assert ads[-1]["end_age"] == 12.0
    assert round(sum(ad["years"] for ad in ads), 6) == 8.0


def test_current_narayana_dasha_finds_ad_and_pd_inside_md():
    current = get_current_narayana_dasha(_sample_mahadashas(), 5.0)

    assert current["md"]["sign"] == "Taurus"
    assert current["ad"] is not None
    assert current["ad"]["start_age"] <= 5.0 < current["ad"]["end_age"]
    assert current["pd"] is not None
    assert current["pd"]["start_age"] <= 5.0 < current["pd"]["end_age"]
