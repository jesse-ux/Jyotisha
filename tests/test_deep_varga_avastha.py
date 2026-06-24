#!/usr/bin/env python3
"""Tests for deep_varga_avastha.py — Sayanadi/Shayanadi + D24/D30/D60 templates."""

from __future__ import annotations
import os
import sys

SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from deep_varga_avastha import build_deep_varga_avastha_report


def _sample_lons() -> dict:
    return {
        'Sun': 80.0,
        'Moon': 123.0,
        'Mars': 210.0,
        'Mercury': 75.0,
        'Jupiter': 15.0,
        'Venus': 102.0,
        'Saturn': 330.0,
    }


def test_deep_varga_avastha_report_exposes_avastha_and_deep_templates() -> None:
    result = build_deep_varga_avastha_report(_sample_lons(), asc_lon=92.0)

    assert result['method'] == 'Sayanadi/Shayanadi Avastha + D24/D30/D60 Deep Templates'
    assert result['summary']['headline']
    assert result['avastha_summary']['dominant_states']
    assert result['avastha_summary']['planet_states']['Moon']['Shayanadi']['state']
    assert {'D24', 'D30', 'D60'} <= set(result['deep_varga_templates'])

    d24 = result['deep_varga_templates']['D24']
    assert d24['theme'] == 'education_learning'
    assert d24['template_cards']
    assert d24['next_action']

    d30 = result['deep_varga_templates']['D30']
    assert d30['theme'] == 'risk_crisis'
    assert 'risk_flags' in d30

    d60 = result['deep_varga_templates']['D60']
    assert d60['theme'] == 'karma_root'
    assert d60['template_cards']
