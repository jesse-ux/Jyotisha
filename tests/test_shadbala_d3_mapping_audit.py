#!/usr/bin/env python3
"""Regression tests for D3 mapping vs Shadbala dignity audit."""

from __future__ import annotations

from scripts.shadbala_d3_mapping_audit import build_report


def test_shadbala_d3_mapping_audit_distinguishes_mapping_vs_dignity_path() -> None:
    report = build_report("references/oracle/dasha_shadbala_oracle_cases.json")

    assert report["scope"] == "shadbala_d3_mapping_audit"
    assert report["summary"]["case_count"] >= 1
    assert report["summary"]["global_closure_blocked"] is True
    assert report["rows"]
    assert any(row["mapping_matches_engine_sign"] is True for row in report["rows"])
    assert any(row["d3_dignity_bucket"] == "own" for row in report["rows"])
    assert report["suspected_fault_split"]
