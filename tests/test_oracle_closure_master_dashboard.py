#!/usr/bin/env python3
"""Tests for the unified external-oracle closure master dashboard."""

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
            "scripts/oracle_closure_master_dashboard.py",
            "--dasha-oracle-file",
            "references/oracle/dasha_shadbala_oracle_cases.json",
            "--tajika-oracle-file",
            "references/oracle/tajika_annual_oracle_cases.json",
            *args,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )


def test_oracle_closure_master_dashboard_aggregates_all_hard_fronts() -> None:
    completed = run_dashboard("--format", "json")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "jyotish_external_oracle_closure_master_dashboard"
    assert report["schema_version"] == 1
    assert report["summary"]["total_tasks"] == 12
    assert report["summary"]["external_verified_tasks"] == 8
    assert report["summary"]["open_tasks"] == 4
    assert report["summary"]["can_claim_global_oracle_closure"] is False
    assert report["fronts"]["dasha"]["task_count"] == 3
    assert report["fronts"]["shadbala"]["task_count"] == 4
    assert report["fronts"]["tajika_sahams"]["task_count"] == 5
    assert report["fronts"]["dasha"]["external_verified_tasks"] == 3
    assert report["fronts"]["dasha"]["first_priority"] is None
    assert report["fronts"]["shadbala"]["external_verified_tasks"] == 4
    assert report["fronts"]["shadbala"]["open_tasks"] == 0
    assert report["fronts"]["shadbala"]["first_priority"] is None
    assert report["fronts"]["tajika_sahams"]["external_verified_tasks"] == 1
    assert report["fronts"]["tajika_sahams"]["open_tasks"] == 4
    assert report["fronts"]["tajika_sahams"]["first_priority"]["case_id"] == "template_einstein_varshaphala_1905_lahiri"
    assert report["fronts"]["tajika_sahams"]["first_priority"]["missing_groups"]["target"]["count"] == 10
    assert report["next_action_order"][0]["front"] == "tajika_sahams"
    assert len(report["next_action_order"]) == 1


def test_oracle_closure_master_dashboard_markdown_can_be_written(tmp_path: Path) -> None:
    output = tmp_path / "oracle_master.md"
    completed = run_dashboard("--format", "markdown", "--output", str(output))

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert output.exists()
    markdown = output.read_text(encoding="utf-8")
    assert "# Jyotish External Oracle Closure Master Dashboard" in markdown
    assert "total_tasks: `12`" in markdown
    assert "can_claim_global_oracle_closure: `false`" in markdown
    assert "`dasha` | 3 | 3 | `complete`" in markdown
    assert "`shadbala` | 4 | 4 | `complete`" in markdown
    assert "template_einstein_varshaphala_1905_lahiri" in markdown
    assert "manual entries" in markdown
    assert "metadata missing" in markdown
