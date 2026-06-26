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


def test_tajika_annual_queue_can_write_and_apply_evidence_packet(tmp_path: Path) -> None:
    oracle = json.loads((ROOT / ORACLE_FILE).read_text(encoding="utf-8"))
    oracle_path = tmp_path / "tajika_oracle.json"
    oracle_path.write_text(json.dumps(oracle, ensure_ascii=False), encoding="utf-8")
    packet_dir = tmp_path / "packets"

    generated = subprocess.run(
        [
            sys.executable,
            "scripts/tajika_annual_oracle_queue.py",
            "--oracle-file",
            str(oracle_path),
            "--write-packet-dir",
            str(packet_dir),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert generated.returncode == 0, generated.stderr or generated.stdout
    queue = json.loads(generated.stdout)
    assert queue["summary"]["written_evidence_packets"] == 5

    packet_path = packet_dir / "external_template_steve_jobs_varshaphala_1984_lahiri.json"
    assert packet_path.exists()
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet["status"] = "external_verified"
    packet["metadata"].update(
        {
            "tool_name": "JHora",
            "tool_version_or_url": "manual-jhora-varshaphala",
            "capture_date": "2026-06-26",
            "source_artifact": "references/oracle/artifacts/steve_jobs_1984_varshaphala_redacted.png",
            "operator_note": "Typed from redacted external annual chart screenshot.",
        }
    )
    packet["target_placeholders"].update(
        {
            "target.solar_return_datetime": "1984-02-24T21:04:00-08:00",
            "target.varsha_lagna_deg": 123.45,
            "target.muntha_sign": "Cancer",
            "target.year_lord": "Moon",
            "target.mudda_dasha_first_lord": "Moon",
            "target.sahams.punya_saham": 210.1,
            "target.sahams.rajya_saham": 88.2,
            "target.sahams.vivah_saham": 301.3,
            "target.tajika_yogas": ["Ithasala"],
            "target.source_artifact": "references/oracle/artifacts/steve_jobs_1984_varshaphala_redacted.png",
        }
    )
    packet_path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")

    applied = subprocess.run(
        [
            sys.executable,
            "scripts/tajika_annual_oracle_queue.py",
            "--oracle-file",
            str(oracle_path),
            "--apply-packet",
            str(packet_path),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert applied.returncode == 0, applied.stderr or applied.stdout
    report = json.loads(applied.stdout)
    assert report["summary"]["applied_evidence_packets"] == 1

    updated = json.loads(oracle_path.read_text(encoding="utf-8"))
    case = next(row for row in updated["template_cases"] if row["id"] == "template_steve_jobs_varshaphala_1984_lahiri")
    assert case["status"] == "external_verified"
    assert case["target"]["solar_return_datetime"] == "1984-02-24T21:04:00-08:00"
    assert case["target"]["sahams"]["punya_saham"] == 210.1
    assert case["evidence_packet"]["metadata"]["tool_name"] == "JHora"
