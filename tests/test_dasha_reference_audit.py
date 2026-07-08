#!/usr/bin/env python3
"""Regression tests for the Vimshottari Dasha reference-drift audit."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dasha_reference_audit_quantifies_pdf_boundary_gap() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/dasha_reference_audit.py",
            "--year",
            "REDACTED_YEAR",
            "--month",
            "4",
            "--day",
            "17",
            "--hour",
            "14",
            "--minute",
            "45",
            "--second",
            "20",
            "--lat",
            "36.466667",
            "--lon",
            "114.2",
            "--tz",
            "8",
            "--target-start-date",
            "1986-05-18",
            "--target-source",
            "private_chart_reference.pdf",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=45,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)

    assert report["scope"] == "vimshottari_dasha_reference_boundary_audit"
    assert report["case"]["birth_time"] == "14:45:20"
    assert report["engine"]["nakshatra"] == "Shatabhisha"
    assert report["engine"]["start_lord"] == "Rahu"
    assert report["engine"]["start_datetime"].startswith("1986-05-23T22:45:10")
    assert report["target_reference"]["source"] == "private_chart_reference.pdf"
    assert report["target_reference"]["date_delta_days"] == 5

    clock = report["clock_precision_sensitivity"]
    assert clock["with_seconds"]["birth_time"] == "14:45:20"
    assert clock["minute_only"]["birth_time"] == "14:45:00"
    assert clock["seconds_effect"]["clock_translation_seconds"] == 20
    assert clock["seconds_effect"]["start_delta_seconds"] < -100000
    assert clock["seconds_effect"]["moon_recalculation_seconds"] < -100000
    assert clock["seconds_effect"]["moon_delta_degrees"] > 0

    year_lengths = {row["year_length"]: row for row in report["year_length_sensitivity"]}
    assert 365.0 in year_lengths
    assert 365.2422 in year_lengths
    assert 365.25 in year_lengths
    assert year_lengths[365.25]["start_datetime"].startswith("1986-05-23T22:45:10")

    moon_gap = report["target_reference"]["required_moon_delta_arcmin_range"]
    assert moon_gap["min"] > 0
    assert moon_gap["max"] > moon_gap["min"]
    assert "无法由秒级输入或年长常数单独解释" in report["finding"]
