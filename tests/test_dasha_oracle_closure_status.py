#!/usr/bin/env python3
"""Tests for the shortest Dasha external-oracle closure status board."""

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
            "scripts/dasha_oracle_closure_status.py",
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


def test_dasha_oracle_closure_status_reports_current_dasha_closure() -> None:
    completed = run_status("--format", "json")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "dasha_external_oracle_closure_status"
    assert report["schema_version"] == 1
    assert report["summary"]["dasha_task_count"] == 2
    assert report["summary"]["external_verified_dasha_tasks"] == 2
    assert report["summary"]["can_claim_dasha_oracle_closure"] is True
    assert report["first_priority"] is None


def test_dasha_oracle_closure_status_markdown_can_be_written(tmp_path: Path) -> None:
    output = tmp_path / "dasha_status.md"
    completed = run_status("--format", "markdown", "--output", str(output))

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert output.exists()
    markdown = output.read_text(encoding="utf-8")
    assert "# Dasha External Oracle Closure Status" in markdown
    assert "can_claim_dasha_oracle_closure: `true`" in markdown
    assert "none: Dasha-only external oracle closure is complete" in markdown
    assert "Keep global calibration blocked" in markdown


def test_dasha_oracle_closure_status_advances_after_first_packet_is_filled(tmp_path: Path) -> None:
    queue_file = tmp_path / "queue.json"
    queue_completed = subprocess.run(
        [
            sys.executable,
            "scripts/oracle_collection_queue.py",
            "--oracle-file",
            "references/oracle/dasha_shadbala_oracle_cases.json",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert queue_completed.returncode == 0, queue_completed.stderr or queue_completed.stdout
    queue_file.write_text(queue_completed.stdout, encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/dasha_oracle_evidence_validator.py",
            "--queue-file",
            str(queue_file),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["summary"]["valid_dasha_packets"] == 2
    assert report["summary"]["all_dasha_packets_external_verified"] is True


def test_dasha_oracle_closure_status_has_no_first_priority_after_all_dasha_packets_are_filled() -> None:
    completed = run_status("--format", "json")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["summary"]["external_verified_dasha_tasks"] == 2
    assert report["summary"]["can_claim_dasha_oracle_closure"] is True
    assert report["first_priority"] is None
    assert report["next_actions"] == [
        "Dasha-only external oracle closure is complete for the current target set.",
        "Keep global calibration blocked until Shadbala and other non-Dasha oracle packets pass validation.",
    ]
