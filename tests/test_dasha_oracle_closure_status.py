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


def test_dasha_oracle_closure_status_identifies_first_shortest_packet() -> None:
    completed = run_status("--format", "json")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "dasha_external_oracle_closure_status"
    assert report["schema_version"] == 1
    assert report["summary"]["dasha_task_count"] == 3
    assert report["summary"]["external_verified_dasha_tasks"] == 1
    assert report["summary"]["can_claim_dasha_oracle_closure"] is False
    assert report["first_priority"]["case_id"] == "template_user_REDACTED_YEAR_moon_longitude_lahiri"
    assert report["first_priority"]["capture_id"] == "external_template_user_REDACTED_YEAR_moon_longitude_lahiri"
    assert report["first_priority"]["required_target_fields"] == ["target.vimshottari_start_date"]
    assert "metadata.tool_name" in report["first_priority"]["missing_fields"]
    assert "target.vimshottari_start_date" in report["first_priority"]["missing_fields"]
    assert report["first_priority"]["missing_groups"]["metadata"]["count"] == 5
    assert report["first_priority"]["missing_groups"]["target"]["count"] == 1
    assert report["first_priority"]["prefilled_fields"]["metadata"]["ayanamsa"] == "lahiri"
    assert report["first_priority"]["prefilled_fields"]["metadata"]["timezone"] == 8
    assert report["first_priority"]["manual_fill_plan"]["status_value"] == "external_verified"
    assert report["first_priority"]["manual_fill_plan"]["manual_entry_count"] == 6
    assert report["first_priority"]["apply_command"]
    assert report["first_priority"]["validate_command"]


def test_dasha_oracle_closure_status_markdown_can_be_written(tmp_path: Path) -> None:
    output = tmp_path / "dasha_status.md"
    completed = run_status("--format", "markdown", "--output", str(output))

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert output.exists()
    markdown = output.read_text(encoding="utf-8")
    assert "# Dasha External Oracle Closure Status" in markdown
    assert "can_claim_dasha_oracle_closure: `false`" in markdown
    assert "external_template_user_REDACTED_YEAR_moon_longitude_lahiri" in markdown
    assert "target.vimshottari_start_date" in markdown
    assert "## Missing Summary" in markdown
    assert "## Prefilled Fields" in markdown
    assert "## Manual Fill Plan" in markdown


def test_dasha_oracle_closure_status_advances_after_first_packet_is_filled(tmp_path: Path) -> None:
    oracle_file = tmp_path / "oracle_cases.json"
    oracle_file.write_text(
        (ROOT / "references/oracle/dasha_shadbala_oracle_cases.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    packet = ROOT / "references/oracle/artifacts/pending_packets/external_template_steve_jobs_dasha_lahiri_pyjhora_20260627.json"
    apply_completed = subprocess.run(
        [
            sys.executable,
            "scripts/oracle_collection_queue.py",
            "--oracle-file",
            str(oracle_file),
            "--apply-packet",
            str(packet),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert apply_completed.returncode == 0, apply_completed.stderr or apply_completed.stdout

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/dasha_oracle_closure_status.py",
            "--oracle-file",
            str(oracle_file),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["summary"]["external_verified_dasha_tasks"] == 1
    assert report["first_priority"]["case_id"] != "template_steve_jobs_dasha_lahiri"
    assert report["first_priority"]["missing_fields"]
