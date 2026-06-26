#!/usr/bin/env python3
"""Tests for the Tajika/Sahams annual external-oracle collection queue."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORACLE_FILE = "references/oracle/tajika_annual_oracle_cases.json"


def run_queue(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/tajika_annual_oracle_queue.py", "--oracle-file", ORACLE_FILE, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )


def test_tajika_annual_queue_outputs_collection_tasks() -> None:
    completed = run_queue("--format", "json")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    queue = json.loads(completed.stdout)
    assert queue["scope"] == "tajika_sahams_annual_oracle_collection_queue"
    assert queue["schema_version"] == 1
    assert queue["summary"]["total_tasks"] == 5
    assert queue["summary"]["ready_for_calibration"] == 0
    assert queue["summary"]["production_tuning_allowed"] is False
    assert "solar return" in queue["boundary"].lower()

    first = queue["tasks"][0]
    assert first["task_id"].startswith("collect_")
    assert first["status"] == "template_only"
    assert first["ready_for_collection"] is True
    assert first["ready_for_calibration"] is False
    assert "target.solar_return_datetime" in first["target_fields"]
    assert "target.sahams.punya_saham" in first["missing_target_fields"]
    assert "JHora Varshaphala screenshot" in first["preferred_sources"]
    assert first["evidence_packet"]["integrity_checks"]["requires_external_artifact"] is True


def test_tajika_annual_queue_markdown_lists_sahams_and_yogas() -> None:
    completed = run_queue("--format", "markdown")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    markdown = completed.stdout
    assert "# Tajika/Sahams Annual External Oracle Collection Queue" in markdown
    assert "Punya Saham" in markdown
    assert "Tajika Yogas" in markdown
    assert "production_tuning_allowed: `false`" in markdown
