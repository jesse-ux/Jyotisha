#!/usr/bin/env python3
"""Tests for the public Jyotish benchmark dashboard."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_dashboard(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/public_benchmark_dashboard.py",
            "--oracle-file",
            "references/oracle/dasha_shadbala_oracle_cases.json",
            *args,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )


def test_public_benchmark_dashboard_outputs_stable_json_summary() -> None:
    completed = run_dashboard("--format", "json")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "public_jyotish_benchmark_dashboard"
    assert report["schema_version"] == 1
    assert report["summary"]["technique_count"] >= 60
    assert report["summary"]["capability_valid"] is True
    assert report["oracle_readiness"]["total_packets"] == 5
    assert report["oracle_readiness"]["valid_packets"] == 0
    assert report["oracle_readiness"]["ready_for_calibration"] == 0
    assert report["oracle_readiness"]["production_tuning_allowed"] is False
    assert report["boundary_audit"]["production_tuning_recommended"] is False
    assert "Dasha/Shadbala" in report["global_first_gap"]
    assert report["public_claim"]["can_claim_global_first"] is False
    assert report["public_claim"]["reason"]


def test_public_benchmark_dashboard_outputs_markdown_and_can_write_file(tmp_path: Path) -> None:
    output = tmp_path / "benchmark.md"
    completed = run_dashboard("--format", "markdown", "--output", str(output))

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert output.exists()
    markdown = output.read_text(encoding="utf-8")
    assert "# Public Jyotish Benchmark Dashboard" in markdown
    assert "Dasha/Shadbala Oracle Readiness" in markdown
    assert "Global First Claim" in markdown
    assert "can_claim_global_first: `false`" in markdown
    assert "production_tuning_allowed: `false`" in markdown
