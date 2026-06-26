#!/usr/bin/env python3
"""Tests for the first external-oracle packet assistant."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_assistant(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/first_oracle_packet_assistant.py",
            "--front",
            "dasha",
            *args,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )


def test_first_oracle_packet_assistant_reports_dasha_next_fields() -> None:
    completed = run_assistant("--format", "json")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "first_external_oracle_packet_assistant"
    assert report["front"] == "dasha"
    assert report["case_id"] == "template_steve_jobs_dasha_lahiri"
    assert report["operator_card"].endswith("dasha_steve_jobs_first_packet_operator_card.md")
    assert report["packet_template"].endswith("dasha_steve_jobs_lahiri_first_packet_only.json")
    assert report["missing_fields"] == [
        "metadata.tool_name",
        "metadata.tool_version_or_url",
        "metadata.capture_date",
        "metadata.operator_note",
        "metadata.source_artifact",
        "target.vimshottari_start_date",
    ]
    assert report["missing_groups"]["metadata"]["count"] == 5
    assert report["missing_groups"]["target"]["count"] == 1
    assert report["missing_groups"]["target"]["fields"] == ["target.vimshottari_start_date"]
    assert report["prefilled_fields"]["metadata"]["ayanamsa"] == "Lahiri"
    assert report["prefilled_fields"]["metadata"]["node_mode"] == "true node"
    assert report["prefilled_fields"]["metadata"]["timezone"] == "UTC-08:00"
    assert report["manual_fill_plan"]["status_value"] == "external_verified"
    assert report["manual_fill_plan"]["manual_entry_count"] == 6
    assert report["manual_fill_plan"]["remaining_manual_fields"][-1] == "target.vimshottari_start_date"
    assert report["ready_to_apply"] is False
    assert "JHora" in " ".join(report["external_sources"])


def test_first_oracle_packet_assistant_markdown_can_be_written(tmp_path: Path) -> None:
    output = tmp_path / "assistant.md"
    completed = run_assistant("--format", "markdown", "--output", str(output))

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert output.exists()
    markdown = output.read_text(encoding="utf-8")
    assert "# First External Oracle Packet Assistant" in markdown
    assert "template_steve_jobs_dasha_lahiri" in markdown
    assert "target.vimshottari_start_date" in markdown
    assert "ready_to_apply: `false`" in markdown


def test_first_oracle_packet_assistant_reports_tajika_front() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/first_oracle_packet_assistant.py",
            "--front",
            "tajika_sahams",
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
    assert report["front"] == "tajika_sahams"
    assert report["case_id"] == "template_steve_jobs_varshaphala_1984_lahiri"
    assert report["operator_card"].endswith("tajika_steve_jobs_1984_first_packet_operator_card.md")
    assert report["packet_template"].endswith("tajika_steve_jobs_1984_first_packet.json")
    assert report["missing_groups"]["metadata"]["count"] == 5
    assert report["missing_groups"]["target"]["count"] == 10
    assert report["manual_fill_plan"]["manual_entry_count"] == 15
    assert "target.solar_return_datetime" in report["missing_fields"]
    assert "target.sahams.punya_saham" in report["missing_fields"]


def test_first_oracle_packet_assistant_reports_shadbala_front() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/first_oracle_packet_assistant.py",
            "--front",
            "shadbala",
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
    assert report["front"] == "shadbala"
    assert report["case_id"] == "template_redacted_place_shadbala_raman"
    assert report["operator_card"].endswith("shadbala_redacted_place_raman_first_packet_operator_card.md")
    assert report["packet_template"].endswith("shadbala_redacted_place_raman_first_packet.json")
    assert report["missing_groups"]["metadata"]["count"] == 5
    assert report["missing_groups"]["target"]["count"] == 50
    assert report["missing_groups"]["bodies"]["Sun"]["count"] == 7
    assert report["missing_groups"]["bodies"]["Moon"]["count"] == 7
    assert report["missing_groups"]["bodies"]["Saturn"]["count"] == 7
    assert report["manual_fill_plan"]["manual_entry_count"] == 55
    assert "target.moon_sidereal_longitude_deg" in report["missing_fields"]
    assert "target.shadbala_components.Sun.sthana" in report["missing_fields"]


def test_first_oracle_packet_assistant_markdown_includes_group_summary() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/first_oracle_packet_assistant.py",
            "--front",
            "shadbala",
            "--format",
            "markdown",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    markdown = completed.stdout
    assert "## Missing Summary" in markdown
    assert "## Prefilled Fields" in markdown
    assert "## Manual Fill Plan" in markdown
    assert "- metadata: `5`" in markdown
    assert "- target: `50`" in markdown
    assert "- Sun: `7`" in markdown
    assert "- status_value: `external_verified`" in markdown
