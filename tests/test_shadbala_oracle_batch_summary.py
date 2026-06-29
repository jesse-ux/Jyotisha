#!/usr/bin/env python3
"""Regression tests for batched Shadbala oracle summary."""

from __future__ import annotations

from scripts.shadbala_oracle_batch_summary import build_report


def test_shadbala_oracle_batch_summary_reuses_all_external_verified_cases() -> None:
    report = build_report("references/oracle/dasha_shadbala_oracle_cases.json")

    assert report["scope"] == "shadbala_oracle_batch_summary"
    assert report["summary"]["case_count"] >= 4
    assert report["summary"]["external_verified_case_count"] >= 4
    assert report["summary"]["fully_within_tolerance_case_count"] <= report["summary"]["external_verified_case_count"]
    assert any(row["case_id"] == "template_steve_jobs_dasha_lahiri" for row in report["rows"])
    assert any(row["case_id"] == "template_redacted_place_shadbala_raman" for row in report["rows"])
    assert report["summary"]["global_closure_blocked"] is True
