#!/usr/bin/env python3
"""Tests for the Tajika/Sahams annual benchmark dashboard."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORACLE_FILE = "references/oracle/tajika_annual_oracle_cases.json"


def run_dashboard(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/tajika_annual_benchmark_dashboard.py",
            "--oracle-file",
            ORACLE_FILE,
            *args,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )


def test_tajika_annual_dashboard_outputs_stable_json_summary() -> None:
    completed = run_dashboard("--format", "json")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "tajika_sahams_annual_benchmark_dashboard"
    assert report["schema_version"] == 1
    assert report["summary"]["total_tasks"] == 5
    assert report["summary"]["ready_for_calibration"] == 0
    assert report["summary"]["production_tuning_allowed"] is False
    assert report["annual_claim"]["can_claim_tajika_sahams_closure"] is False
    assert "Solar return" in report["remaining_gap"]
    assert "Sahams" in report["remaining_gap"]


def test_tajika_annual_dashboard_outputs_markdown_and_can_write_file(tmp_path: Path) -> None:
    output = tmp_path / "tajika_dashboard.md"
    completed = run_dashboard("--format", "markdown", "--output", str(output))

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert output.exists()
    markdown = output.read_text(encoding="utf-8")
    assert "# Tajika/Sahams Annual Benchmark Dashboard" in markdown
    assert "can_claim_tajika_sahams_closure: `false`" in markdown
    assert "production_tuning_allowed: `false`" in markdown
