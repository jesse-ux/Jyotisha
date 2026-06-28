#!/usr/bin/env python3
"""Regression tests for the marriage timing benchmark summary helper."""

from __future__ import annotations

from pathlib import Path

from scripts.marriage_benchmark_summary import summarize_benchmark


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_FILE = ROOT / "tests" / "test-data" / "verify-results-v6.1.json"


def test_marriage_benchmark_summary_preserves_rao_v61_event_statistics() -> None:
    report = summarize_benchmark(str(BENCHMARK_FILE))

    assert report["scope"] == "marriage_timing_benchmark_summary"
    assert report["case_count"] == 18
    assert report["ascendant_match_count"] == 18
    assert report["marriage_event_count"] == 26
    assert report["divorce_event_count"] == 15
    assert report["rao_hit_distribution"] == {
        "2": 2,
        "3": 2,
        "4": 9,
        "5": 8,
        "6": 2,
        "7": 3,
    }
    assert report["rao_parameter_hits"]["P1"]["hit_count"] == 25
    assert report["rao_parameter_hits"]["P6"]["hit_rate_pct"] == 69.23


def test_marriage_benchmark_summary_exposes_label_lift_seed_cases() -> None:
    report = summarize_benchmark(str(BENCHMARK_FILE))
    seed_ids = {row["event_id"] for row in report["label_lift_seed_cases"]}

    assert "Britney Spears|Kevin Federline|2004-10-06" in seed_ids
    assert "Tom Cruise|Katie Holmes|2006-11-18" in seed_ids
    assert all(row["rao_hit_count"] >= 6 for row in report["label_lift_seed_cases"])
