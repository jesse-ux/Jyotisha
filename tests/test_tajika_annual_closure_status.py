#!/usr/bin/env python3
"""Tests for the shortest Tajika/Sahams annual external closure status board."""

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
            "scripts/tajika_annual_closure_status.py",
            "--oracle-file",
            "references/oracle/tajika_annual_oracle_cases.json",
            *args,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )


def test_tajika_annual_closure_status_identifies_first_annual_packet() -> None:
    completed = run_status("--format", "json")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "tajika_sahams_annual_closure_status"
    assert report["schema_version"] == 1
    assert report["summary"]["annual_task_count"] == 5
    assert report["summary"]["external_verified_annual_tasks"] == 1
    assert report["summary"]["can_claim_tajika_sahams_closure"] is False
    from scripts import tajika_annual_closure_status as module
    assert module.FIRST_PRIORITY_CASE_ID == "template_einstein_varshaphala_1905_lahiri"
    assert module.FIRST_PRIORITY_TEMPLATE_PATH.endswith("external_template_einstein_varshaphala_1905_lahiri.json")
    assert report["first_priority"]["case_id"] == "template_einstein_varshaphala_1905_lahiri"
    assert report["first_priority"]["capture_id"] == "external_template_einstein_varshaphala_1905_lahiri"
    assert report["first_priority"]["required_target_fields"] == [
        "target.solar_return_datetime",
        "target.varsha_lagna_deg",
        "target.muntha_sign",
        "target.year_lord",
        "target.mudda_dasha_first_lord",
        "target.sahams.punya_saham",
        "target.sahams.rajya_saham",
        "target.sahams.vivah_saham",
        "target.tajika_yogas",
        "target.source_artifact",
    ]
    assert "metadata.tool_name" in report["first_priority"]["missing_fields"]
    assert "target.solar_return_datetime" in report["first_priority"]["missing_fields"]
    assert "target.sahams.punya_saham" in report["first_priority"]["missing_fields"]
    assert report["first_priority"]["missing_groups"]["metadata"]["count"] == 5
    assert report["first_priority"]["missing_groups"]["target"]["count"] == 10
    assert report["first_priority"]["prefilled_fields"]["metadata"]["annual_system"] == "varshaphala"
    assert report["first_priority"]["prefilled_fields"]["metadata"]["target_year"] == 1905
    assert report["first_priority"]["prefilled_fields"]["settings"]["node_mode"] == "mean"
    assert report["first_priority"]["manual_fill_plan"]["status_value"] == "external_verified"
    assert report["first_priority"]["manual_fill_plan"]["manual_entry_count"] == 15
    assert report["first_priority"]["validate_command"]
    packet_path = ROOT / report["first_priority"]["packet_path"]
    assert packet_path.exists(), report["first_priority"]["packet_path"]
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet["capture_id"] == "external_template_einstein_varshaphala_1905_lahiri"
    assert packet["status"] == "draft"
    assert packet["target_placeholders"]["target.solar_return_datetime"] is None


def test_tajika_annual_closure_status_markdown_can_be_written(tmp_path: Path) -> None:
    output = tmp_path / "tajika_status.md"
    completed = run_status("--format", "markdown", "--output", str(output))

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert output.exists()
    markdown = output.read_text(encoding="utf-8")
    assert "# Tajika/Sahams Annual Closure Status" in markdown
    assert "can_claim_tajika_sahams_closure: `false`" in markdown
    assert "external_template_einstein_varshaphala_1905_lahiri" in markdown
    assert "target.sahams.punya_saham" in markdown
    assert "## Missing Summary" in markdown
    assert "## Prefilled Fields" in markdown
    assert "## Manual Fill Plan" in markdown
