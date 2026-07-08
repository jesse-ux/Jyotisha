#!/usr/bin/env python3
"""Regression tests for D3 branch-level audit."""

from __future__ import annotations

from scripts.shadbala_d3_branch_audit import build_report
from scripts.shadbala_oracle_comparison import compare_case


def test_shadbala_d3_branch_audit_points_to_calc_sthana_bala_d3_branch() -> None:
    report = build_report("references/oracle/dasha_shadbala_oracle_cases.json")

    assert report["scope"] == "shadbala_d3_branch_audit"
    assert report["summary"]["row_count"] >= 1
    assert report["summary"]["global_closure_blocked"] is True
    assert report["branch_counts"]
    assert "direct_own_sign_branch" in report["branch_counts"]
    assert all(row["suspected_function"] == "calc_sthana_bala" for row in report["rows"])


def test_shadbala_d3_branch_audit_after_d3_exaltation_cap_retargets_to_own_branch() -> None:
    report = build_report("references/oracle/dasha_shadbala_oracle_cases.json")

    assert report["branch_hotspots"]["direct_own_sign_branch"]["row_count"] >= 1
    assert report["branch_hotspots"]["direct_own_sign_branch"]["avg_abs_component_diff_rupa"] is not None
    assert "direct_exaltation_branch" not in report["branch_hotspots"]


def test_shadbala_d3_exaltation_cap_reduces_sun_sthana_gap_for_synthetic_north_china_case() -> None:
    comparison = compare_case("references/oracle/dasha_shadbala_oracle_cases.json", "template_synthetic_north_china_shadbala_raman")
    sun_sthana_gap = comparison["comparison"]["Sun"]["components"]["sthana"]["abs_diff_rupa"]

    assert sun_sthana_gap < 3.5207


def test_shadbala_d3_own_sign_cap_reduces_venus_sthana_gap_for_synthetic_north_china_case() -> None:
    comparison = compare_case("references/oracle/dasha_shadbala_oracle_cases.json", "template_synthetic_north_china_shadbala_raman")
    venus_sthana_gap = comparison["comparison"]["Venus"]["components"]["sthana"]["abs_diff_rupa"]

    assert venus_sthana_gap < 1.7084
