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
    assert report["missing_fields"] == []
    assert report["missing_groups"]["metadata"]["count"] == 0
    assert report["missing_groups"]["target"]["count"] == 0
    assert report["prefilled_fields"]["metadata"]["ayanamsa"] == "Lahiri"
    assert report["prefilled_fields"]["metadata"]["node_mode"] == "true node"
    assert report["prefilled_fields"]["metadata"]["timezone"] == "UTC-08:00"
    assert report["manual_fill_plan"]["status_value"] == "external_verified"
    assert report["manual_fill_plan"]["manual_entry_count"] == 0
    assert report["manual_fill_plan"]["remaining_manual_fields"] == []
    assert report["ready_to_apply"] is True
    assert "JHora" in " ".join(report["external_sources"])


def test_first_oracle_packet_assistant_markdown_can_be_written(tmp_path: Path) -> None:
    output = tmp_path / "assistant.md"
    completed = run_assistant("--format", "markdown", "--output", str(output))

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert output.exists()
    markdown = output.read_text(encoding="utf-8")
    assert "# First External Oracle Packet Assistant" in markdown
    assert "template_steve_jobs_dasha_lahiri" in markdown
    assert "ready_to_apply: `true`" in markdown


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
    assert report["case_id"] == "template_einstein_varshaphala_1905_lahiri"
    assert report["operator_card"].endswith("tajika_einstein_1905_first_packet_operator_card.md")
    assert report["packet_template"].endswith("external_template_einstein_varshaphala_1905_lahiri.json")
    assert report["missing_groups"]["metadata"]["count"] == 0
    assert report["missing_groups"]["target"]["count"] == 0
    assert report["manual_fill_plan"]["manual_entry_count"] == 0
    assert report["missing_fields"] == []
    assert report["ready_to_apply"] is True


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
    assert report["missing_groups"]["metadata"]["count"] == 0
    assert report["missing_groups"]["target"]["count"] == 0
    assert report["missing_groups"]["bodies"] == {}
    assert report["manual_fill_plan"]["manual_entry_count"] == 0
    assert report["missing_fields"] == []
    assert report["ready_to_apply"] is True


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
    assert "- metadata: `0`" in markdown
    assert "- target: `0`" in markdown
    assert "- status_value: `external_verified`" in markdown
