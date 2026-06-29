#!/usr/bin/env python3
"""Regression tests for Shadbala component hotspot clustering."""

from __future__ import annotations

from scripts.shadbala_oracle_component_cluster_summary import build_report


def test_shadbala_component_cluster_summary_reuses_external_verified_cases() -> None:
    report = build_report("references/oracle/dasha_shadbala_oracle_cases.json")

    assert report["scope"] == "shadbala_oracle_component_cluster_summary"
    assert report["summary"]["case_count"] >= 4
    assert report["summary"]["planet_count"] >= 7
    assert report["summary"]["global_closure_blocked"] is True
    assert report["component_hotspots"]
    assert any(row["component"] == "sthana" for row in report["component_hotspots"])
    assert any(row["planet"] == "Sun" for row in report["planet_hotspots"])
    assert "targeted_fix_recommendation" in report["summary"]
