#!/usr/bin/env python3
"""Regression tests for Dig Bala source-of-truth audit."""

from __future__ import annotations

from scripts.shadbala_dig_source_of_truth_audit import build_report


def test_shadbala_dig_source_of_truth_audit_compares_three_candidate_models() -> None:
    report = build_report("references/oracle/dasha_shadbala_oracle_cases.json")

    assert report["scope"] == "shadbala_dig_source_of_truth_audit"
    assert report["summary"]["case_count"] >= 1
    assert set(report["candidate_models"]) == {
        "current_linear_house_model",
        "house_midpoint_angular_model",
        "bhava_madhya_angular_model",
    }
    assert report["summary"]["best_model_by_avg_abs_diff"] in report["candidate_models"]
    assert report["rows"]

