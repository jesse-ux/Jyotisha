#!/usr/bin/env python3
"""Tests for the shortest Shadbala external absolute-value closure status board."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_status(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/shadbala_oracle_closure_status.py",
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


def test_shadbala_oracle_closure_status_identifies_first_absolute_value_packet() -> None:
    completed = run_status("--format", "json")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "shadbala_external_absolute_value_closure_status"
    assert report["schema_version"] == 1
    assert report["summary"]["shadbala_task_count"] == 2
    assert report["summary"]["external_verified_shadbala_tasks"] == 2
    assert report["summary"]["external_packet_fields_complete"] is True
    assert report["summary"]["same_chart_parity_status"] == "blocked"
    assert report["summary"]["can_claim_shadbala_absolute_closure"] is False
    assert report["summary"]["required_planets"] == ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    assert report["summary"]["required_components"] == ["sthana", "dig", "kala", "chesta", "naisargika", "drik", "total_rupa"]
    assert report["first_priority"] is None
    assert report["next_actions"][0] == "Reconcile Shadbala component-level formulas against PyJHora/JHora same-chart raw values."


def test_shadbala_oracle_closure_status_markdown_can_be_written(tmp_path: Path) -> None:
    output = tmp_path / "shadbala_status.md"
    completed = run_status("--format", "markdown", "--output", str(output))

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert output.exists()
    markdown = output.read_text(encoding="utf-8")
    assert "# Shadbala External Absolute-Value Closure Status" in markdown
    assert "same_chart_parity_status: `blocked`" in markdown
    assert "can_claim_shadbala_absolute_closure: `false`" in markdown
    assert "same-chart parity is still blocked" in markdown
