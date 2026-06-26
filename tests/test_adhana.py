#!/usr/bin/env python3
"""Regression tests for the first Adhana / conception workflow scaffold."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)

from adhana import analyze_adhana_candidates


def sample_birth_payload():
    return {
        "asc_lon": 132.355025,
        "sun_lon": 3.5226611111111112,
        "moon_lon": 311.78995555555554,
        "gulika_lon": 256.581676,
        "weekday": 6,
        "year": REDACTED_YEAR,
        "month": 4,
        "day": 17,
        "hour": 14,
        "minute": 45,
        "second": 20,
        "lat": 36.466667,
        "lon": 114.2,
        "tz": 8,
    }


def test_adhana_scaffold_exposes_reusable_inputs_and_trace():
    result = analyze_adhana_candidates(sample_birth_payload())

    assert result["system"] == "adhana_scaffold"
    assert result["status"] == "partial_scaffold"
    assert "rule_trace" in result
    assert len(result["rule_trace"]) >= 3


def test_adhana_scaffold_reuses_d12_gulika_and_special_lagnas():
    result = analyze_adhana_candidates(sample_birth_payload())

    assert result["inputs"]["gulika_lon"] == 256.581676
    assert result["birth_d12"]["Moon"]["sign"]
    assert result["special_lagnas"]["GL"]["sign"]
    assert result["special_lagnas"]["HL"]["sign"]


def test_adhana_scaffold_surfaces_candidate_layers_without_claiming_finality():
    result = analyze_adhana_candidates(sample_birth_payload())

    assert "candidate_adhana_lagna" in result
    assert "candidate_adhana_moon" in result
    assert result["candidate_adhana_lagna"]["source"] in {"special_lagnas.GL", "special_lagnas.HL"}
    assert result["candidate_adhana_moon"]["source"] == "D12_moon_plus_gulika_arc"
    assert "not a final classical closure" in result["boundary"]
