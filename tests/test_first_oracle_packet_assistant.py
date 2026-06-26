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
