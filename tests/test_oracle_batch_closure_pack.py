#!/usr/bin/env python3
"""Regression tests for the batched oracle closure pack."""

from __future__ import annotations

from scripts.oracle_batch_closure_pack import build_report


def test_oracle_batch_closure_pack_combines_dasha_and_shadbala_truth() -> None:
    report = build_report("references/oracle/dasha_shadbala_oracle_cases.json")

    assert report["scope"] == "oracle_batch_closure_pack"
    assert report["summary"]["dasha_can_claim_closure"] is True
    assert report["summary"]["shadbala_case_count"] >= 2
    assert report["summary"]["shadbala_within_tolerance_case_count"] <= report["summary"]["shadbala_case_count"]
    assert any(item["kind"] == "dasha" for item in report["rows"])
    assert any(item["kind"] == "shadbala" for item in report["rows"])
    assert report["summary"]["global_oracle_closure_blocked"] is True
