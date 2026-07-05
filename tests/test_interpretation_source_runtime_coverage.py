#!/usr/bin/env python3
"""Regression tests for interpretation source runtime coverage report."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_interpretation_source_runtime_coverage_reports_machine_checkable_gap() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/interpretation_source_runtime_coverage.py",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "interpretation_source_runtime_coverage"
    assert report["status"] == "partial"
    assert report["source_pack_status"] == "used"
    assert "dasha_timing_layer_used" in report["proven_runtime_markers"]
    assert "references/open_source_sources/jyotishganit" in report["not_fully_closed"]
    assert report["inventory_gate"]["status"] == "pass"
