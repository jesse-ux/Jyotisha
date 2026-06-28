#!/usr/bin/env python3
"""Regression tests for Shadbala absolute oracle comparison entrypoint."""

from __future__ import annotations

from pathlib import Path

from scripts.shadbala_oracle_comparison import compare_case


ROOT = Path(__file__).resolve().parents[1]
ORACLE_FILE = ROOT / "references" / "oracle" / "dasha_shadbala_oracle_cases.json"


def test_compare_case_returns_absolute_rupa_diffs_for_external_verified_case() -> None:
    report = compare_case(
        oracle_file=str(ORACLE_FILE),
        case_id="template_steve_jobs_dasha_lahiri",
    )

    assert report["scope"] == "shadbala_absolute_oracle_comparison"
    assert report["case_id"] == "template_steve_jobs_dasha_lahiri"
    assert report["status"] == "external_verified"
    assert report["settings"]["ayanamsa"] == "lahiri"
    assert report["summary"]["planet_count"] == 7
    assert "Sun" in report["comparison"]
    assert "oracle_total_rupa" in report["comparison"]["Sun"]
    assert "local_total_rupa" in report["comparison"]["Sun"]
    assert "diff_total_rupa" in report["comparison"]["Sun"]

