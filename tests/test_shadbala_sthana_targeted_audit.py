#!/usr/bin/env python3
"""Regression tests for targeted Sthana Bala oracle audit."""

from __future__ import annotations

from scripts.shadbala_sthana_targeted_audit import build_report


def test_shadbala_sthana_targeted_audit_identifies_sapta_and_dignity_signals() -> None:
    report = build_report("references/oracle/dasha_shadbala_oracle_cases.json")

    assert report["scope"] == "shadbala_sthana_targeted_audit"
    assert report["summary"]["case_count"] >= 4
    assert report["summary"]["row_count"] >= 20
    assert report["summary"]["global_closure_blocked"] is True
    assert report["rows"]
    assert any("sapta" in row["suspected_driver"] for row in report["rows"])
    assert any(row["d1_dignity_bucket"] in {"own", "exalted", "debilitated", "friend", "enemy", "neutral"} for row in report["rows"])
    assert report["driver_counts"]
