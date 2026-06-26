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
    assert report["summary"]["shadbala_task_count"] == 4
    assert report["summary"]["external_verified_shadbala_tasks"] == 3
    assert report["summary"]["can_claim_shadbala_absolute_closure"] is False
    assert report["summary"]["required_planets"] == ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    assert report["summary"]["required_components"] == ["sthana", "dig", "kala", "chesta", "naisargika", "drik", "total_rupa"]
    assert report["first_priority"]["case_id"] == "template_extreme_latitude_kp"
    assert report["first_priority"]["capture_id"] == "external_template_extreme_latitude_kp"
    assert report["first_priority"]["required_target_fields"] == ["target.shadbala_components"]
    assert "metadata.tool_name" in report["first_priority"]["missing_fields"]
    assert "target.shadbala_components.Sun.sthana" in report["first_priority"]["missing_fields"]
    assert "target.shadbala_components.Saturn.total_rupa" in report["first_priority"]["missing_fields"]
    assert report["first_priority"]["missing_groups"]["metadata"]["count"] == 5
    assert report["first_priority"]["missing_groups"]["target"]["count"] == 49
    assert report["first_priority"]["missing_groups"]["bodies"]["Sun"]["count"] == 7
    assert report["first_priority"]["prefilled_fields"]["metadata"]["ayanamsa"] == "kp"
    assert report["first_priority"]["manual_fill_plan"]["status_value"] == "external_verified"
    assert report["first_priority"]["manual_fill_plan"]["manual_entry_count"] == 54
    assert report["first_priority"]["reject_global_scaling"] is True
    assert report["first_priority"]["validate_command"]


def test_shadbala_oracle_closure_status_markdown_can_be_written(tmp_path: Path) -> None:
    output = tmp_path / "shadbala_status.md"
    completed = run_status("--format", "markdown", "--output", str(output))

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert output.exists()
    markdown = output.read_text(encoding="utf-8")
    assert "# Shadbala External Absolute-Value Closure Status" in markdown
    assert "can_claim_shadbala_absolute_closure: `false`" in markdown
    assert "external_template_extreme_latitude_kp" in markdown
    assert "target.shadbala_components.Sun.sthana" in markdown
    assert "## Missing Summary" in markdown
    assert "## Prefilled Fields" in markdown
    assert "## Manual Fill Plan" in markdown
