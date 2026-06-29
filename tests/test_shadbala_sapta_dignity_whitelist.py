#!/usr/bin/env python3
"""Regression tests for Sapta dignity whitelist audit."""

from __future__ import annotations

from scripts.shadbala_sapta_dignity_whitelist import build_report


def test_shadbala_sapta_dignity_whitelist_surfaces_d7_d12_d3_d4_exalted_own_flags() -> None:
    report = build_report("references/oracle/dasha_shadbala_oracle_cases.json")

    assert report["scope"] == "shadbala_sapta_dignity_whitelist"
    assert report["summary"]["case_count"] >= 4
    assert report["summary"]["global_closure_blocked"] is True
    assert report["whitelist_rows"]
    assert any(row["layer"] in {"D7", "D12", "D3", "D4"} for row in report["whitelist_rows"])
    assert any(row["dignity_type"] in {"exalted", "own"} for row in report["whitelist_rows"])
    assert report["layer_counts"]
