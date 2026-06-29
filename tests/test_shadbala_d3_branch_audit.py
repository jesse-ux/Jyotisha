#!/usr/bin/env python3
"""Regression tests for D3 branch-level audit."""

from __future__ import annotations

from scripts.shadbala_d3_branch_audit import build_report


def test_shadbala_d3_branch_audit_points_to_calc_sthana_bala_d3_branch() -> None:
    report = build_report("references/oracle/dasha_shadbala_oracle_cases.json")

    assert report["scope"] == "shadbala_d3_branch_audit"
    assert report["summary"]["row_count"] >= 4
    assert report["summary"]["global_closure_blocked"] is True
    assert report["branch_counts"]
    assert "direct_exaltation_branch" in report["branch_counts"] or "direct_own_sign_branch" in report["branch_counts"]
    assert all(row["suspected_function"] == "calc_sthana_bala" for row in report["rows"])


def test_shadbala_d3_branch_audit_splits_exaltation_vs_own_drift() -> None:
    report = build_report("references/oracle/dasha_shadbala_oracle_cases.json")

    assert report["branch_hotspots"]["direct_exaltation_branch"]["row_count"] >= 1
    assert report["branch_hotspots"]["direct_own_sign_branch"]["row_count"] >= 1
    assert report["branch_hotspots"]["direct_exaltation_branch"]["avg_abs_component_diff_rupa"] is not None
    assert report["branch_hotspots"]["direct_own_sign_branch"]["avg_abs_component_diff_rupa"] is not None
