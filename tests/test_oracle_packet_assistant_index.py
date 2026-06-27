#!/usr/bin/env python3
"""Tests for the unified first-oracle packet assistant index."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_index(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/oracle_packet_assistant_index.py",
            *args,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )


def test_oracle_packet_assistant_index_aggregates_three_fronts() -> None:
    completed = run_index("--format", "json")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "first_oracle_packet_assistant_index"
    assert report["schema_version"] == 1
    assert report["summary"]["front_count"] == 3
    assert report["summary"]["all_ready_to_apply"] is False
    assert report["fronts"]["dasha"]["missing_field_count"] == 6
    assert report["fronts"]["tajika_sahams"]["missing_field_count"] == 15
    assert report["fronts"]["shadbala"]["missing_field_count"] == 55
    assert report["fronts"]["tajika_sahams"]["case_id"] == "template_einstein_varshaphala_1905_lahiri"
    assert report["fronts"]["tajika_sahams"]["operator_card"].endswith("tajika_einstein_1905_first_packet_operator_card.md")
    assert report["fronts"]["tajika_sahams"]["packet_template"].endswith("external_template_einstein_varshaphala_1905_lahiri.json")
    assert report["recommended_order"][0]["front"] == "dasha"
    assert report["recommended_order"][1]["front"] == "tajika_sahams"
    assert report["recommended_order"][2]["front"] == "shadbala"


def test_oracle_packet_assistant_index_markdown_can_be_written(tmp_path: Path) -> None:
    output = tmp_path / "assistant_index.md"
    completed = run_index("--format", "markdown", "--output", str(output))

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert output.exists()
    markdown = output.read_text(encoding="utf-8")
    assert "# First Oracle Packet Assistant Index" in markdown
    assert "dasha" in markdown
    assert "tajika_sahams" in markdown
    assert "shadbala" in markdown
    assert "6" in markdown
    assert "15" in markdown
    assert "55" in markdown
