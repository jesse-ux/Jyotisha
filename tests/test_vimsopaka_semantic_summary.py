#!/usr/bin/env python3
"""Regression tests for user-visible Vimsopaka semantic summaries."""

from __future__ import annotations

from scripts.jyotish_engine import _build_vimsopaka_semantic_summary


def test_build_vimsopaka_semantic_summary_surfaces_high_value_dignity_terms() -> None:
    summary = _build_vimsopaka_semantic_summary({
        "Sun": {"dignity": "GREAT_FRIEND"},
        "Moon": {"dignity": "NEECHA_BHANGA"},
        "Mars": {"dignity": "GREAT_ENEMY"},
    })

    assert "Great Friend" in summary["highlights"][0] or "极友" in summary["highlights"][0]
    assert any("Neecha Bhanga" in item or "落陷取消" in item for item in summary["highlights"])
    assert any("Great Enemy" in item or "极敌" in item for item in summary["warnings"])
    assert summary["status"] == "used"
