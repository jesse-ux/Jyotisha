#!/usr/bin/env python3
"""Regression tests for Sapta Varga hotspot audit."""

from __future__ import annotations

from scripts.shadbala_sapta_layer_hotspots import build_report


def test_shadbala_sapta_layer_hotspots_surfaces_layer_ranking_and_driver_mix() -> None:
    report = build_report("references/oracle/dasha_shadbala_oracle_cases.json")

    assert report["scope"] == "shadbala_sapta_layer_hotspots"
    assert report["summary"]["case_count"] >= 4
    assert report["summary"]["row_count"] >= 20
    assert report["summary"]["global_closure_blocked"] is True
    assert report["layer_hotspots"]
    assert any(row["layer"] == "D1" for row in report["layer_hotspots"])
    assert any(row["layer"] == "D9" for row in report["layer_hotspots"])
    assert report["driver_mix"]
    assert any(key.startswith("friend_enemy") for key in report["driver_mix"])
    assert any(key.startswith("dignity") for key in report["driver_mix"])
