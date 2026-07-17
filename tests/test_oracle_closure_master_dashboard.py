#!/usr/bin/env python3
"""Tests for the unified external-oracle closure master dashboard."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import scripts.oracle_closure_master_dashboard as dashboard


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "docs" / "research" / "oracle_closure_master_dashboard_latest.md"


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


def _without_generated_at(markdown: str) -> str:
    return re.sub(r"Generated: `[^`]+`", "Generated: `<timestamp>`", markdown)


def test_checked_in_dashboard_matches_current_render_except_timestamp() -> None:
    current = dashboard.render_markdown(
        dashboard.build_dashboard(
            "references/oracle/dasha_shadbala_oracle_cases.json",
            "references/oracle/tajika_annual_oracle_cases.json",
        )
    )
    assert _without_generated_at(DASHBOARD.read_text(encoding="utf-8")) == _without_generated_at(current)


def test_oracle_closure_master_dashboard_aggregates_all_hard_fronts() -> None:
    completed = run_dashboard("--format", "json")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "jyotish_external_oracle_closure_master_dashboard"
    assert report["schema_version"] == 1
    assert report["summary"]["total_tasks"] == 9
    assert report["summary"]["external_verified_tasks"] == 9
    assert report["summary"]["open_tasks"] == 0
    assert report["summary"]["can_claim_current_target_set_closure"] is True
    assert report["summary"]["can_claim_global_oracle_closure"] is False
    assert report["fronts"]["dasha"]["task_count"] == 2
    assert report["fronts"]["shadbala"]["task_count"] == 2
    assert report["fronts"]["tajika_sahams"]["task_count"] == 5
    assert report["fronts"]["dasha"]["external_verified_tasks"] == 2
    assert report["fronts"]["dasha"]["first_priority"] is None
    assert report["fronts"]["shadbala"]["external_verified_tasks"] == 2
    assert report["fronts"]["shadbala"]["open_tasks"] == 0
    assert report["fronts"]["shadbala"]["first_priority"] is None
    assert report["fronts"]["tajika_sahams"]["external_verified_tasks"] == 5
    assert report["fronts"]["tajika_sahams"]["open_tasks"] == 0
    assert report["fronts"]["tajika_sahams"]["first_priority"]["case_id"] == "template_einstein_varshaphala_1905_lahiri"
    assert report["fronts"]["tajika_sahams"]["first_priority"]["missing_groups"]["target"]["count"] == 0
    assert report["next_action_order"] == []


def test_oracle_closure_master_dashboard_markdown_can_be_written(tmp_path: Path) -> None:
    output = tmp_path / "oracle_master.md"
    completed = run_dashboard("--format", "markdown", "--output", str(output))

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert output.exists()
    markdown = output.read_text(encoding="utf-8")
    assert "# Jyotish External Oracle Closure Master Dashboard" in markdown
    assert "total_tasks: `9`" in markdown
    assert "can_claim_current_target_set_closure: `true`" in markdown
    assert "can_claim_global_oracle_closure: `false`" in markdown
    assert "`dasha` | 2 | 2 | `complete`" in markdown
    assert "`shadbala` | 2 | 2 | `complete`" in markdown
    assert "template_einstein_varshaphala_1905_lahiri" in markdown
    assert "manual entries" in markdown
    assert "metadata missing" in markdown
