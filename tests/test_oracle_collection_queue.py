#!/usr/bin/env python3
"""Regression tests for the Dasha/Shadbala external oracle collection queue."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_queue(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/oracle_collection_queue.py",
            "--oracle-file",
            "references/oracle/dasha_shadbala_oracle_cases.json",
            *args,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def run_queue_for_file(oracle_file: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/oracle_collection_queue.py",
            "--oracle-file",
            str(oracle_file),
            *args,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def test_oracle_collection_queue_outputs_executable_json_tasks() -> None:
    completed = run_queue("--format", "json")
    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)

    assert report["scope"] == "external_oracle_collection_queue"
    assert report["summary"]["total_tasks"] == 5
    assert report["summary"]["ready_for_calibration"] == 0
    assert report["summary"]["by_status"]["template_only"] == 5
    assert report["summary"]["production_tuning_allowed"] is False

    first = report["tasks"][0]
    assert first["case_id"] == "template_user_REDACTED_YEAR_moon_longitude_lahiri"
    assert first["status"] == "template_only"
    assert first["ready_for_collection"] is True
    assert first["ready_for_calibration"] is False
    assert "target.moon_sidereal_longitude_deg" in first["missing_target_fields"]
    assert "longitude" in first["target_modules"]
    assert "dasha" in first["target_modules"]
    assert "shadbala" in first["target_modules"]
    assert any("JHora" in source for source in first["preferred_sources"])
    assert any("VedAstro" in source for source in first["preferred_sources"])
    assert first["promotion_criteria"]
    assert first["do_not_tune_production"] is True

    packet = first["evidence_packet"]
    assert packet["capture_id"] == "external_template_user_REDACTED_YEAR_moon_longitude_lahiri"
    assert packet["status"] == "draft"
    assert packet["case_id"] == first["case_id"]
    assert packet["birth"] == first["birth"]
    assert packet["settings"] == first["settings"]
    assert "tool_name" in packet["required_metadata_fields"]
    assert "tool_version_or_url" in packet["required_metadata_fields"]
    assert "capture_date" in packet["required_metadata_fields"]
    assert "source_artifact" in packet["required_metadata_fields"]
    assert "target.moon_sidereal_longitude_deg" in packet["target_placeholders"]
    assert packet["target_placeholders"]["target.moon_sidereal_longitude_deg"] is None
    assert packet["integrity_checks"]["must_not_come_from_local_engine"] is True
    assert packet["integrity_checks"]["requires_external_artifact"] is True


def test_oracle_collection_queue_outputs_markdown_table() -> None:
    completed = run_queue("--format", "markdown")
    assert completed.returncode == 0, completed.stderr or completed.stdout
    markdown = completed.stdout

    assert "# Dasha/Shadbala External Oracle Collection Queue" in markdown
    assert "| task_id | case_id | status | missing fields | preferred sources |" in markdown
    assert "collect_template_user_REDACTED_YEAR_moon_longitude_lahiri" in markdown
    assert "`template_only`" in markdown
    assert "production_tuning_allowed: `false`" in markdown
    assert "Evidence Packet Fields" in markdown
    assert "tool_name" in markdown
    assert "capture_id" in markdown


def test_oracle_collection_queue_preserves_external_verified_evidence(tmp_path: Path) -> None:
    oracle = json.loads((ROOT / "references/oracle/dasha_shadbala_oracle_cases.json").read_text(encoding="utf-8"))
    case = oracle["template_cases"][0]
    case["status"] = "external_verified"
    case["target"] = {
        "moon_sidereal_longitude_deg": 311.7897,
        "vimshottari_start_date": "1986-05-18",
        "shadbala_components": {
            "Sun": {
                "sthana": 100.0,
                "dig": 50.0,
                "kala": 100.0,
                "chesta": 40.0,
                "naisargika": 60.0,
                "drik": 30.0,
            }
        },
    }
    case["evidence_packet"] = {
        "status": "external_verified",
        "metadata": {
            "tool_name": "JHora",
            "tool_version_or_url": "manual-screenshot-v1",
            "capture_date": "2026-06-25",
            "source_artifact": "docs/research/oracle_artifacts/manual_jhora_user_REDACTED_YEAR.png",
            "ayanamsa": "lahiri",
            "node_mode": "mean",
            "timezone": "UTC+08:00",
            "operator_note": "Manual external screenshot; values typed from JHora screen.",
        },
    }
    oracle_path = tmp_path / "oracle.json"
    oracle_path.write_text(json.dumps(oracle, ensure_ascii=False), encoding="utf-8")

    completed = run_queue_for_file(oracle_path, "--format", "json")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    first = report["tasks"][0]
    assert first["status"] == "external_verified"
    assert first["missing_target_fields"] == []
    assert first["ready_for_collection"] is False
    assert first["ready_for_calibration"] is True
    assert first["do_not_tune_production"] is False
    assert report["summary"]["ready_for_calibration"] == 1
    assert report["summary"]["production_tuning_allowed"] is False

    packet = first["evidence_packet"]
    assert packet["status"] == "external_verified"
    assert packet["metadata"]["tool_name"] == "JHora"
    assert packet["target_placeholders"]["target.moon_sidereal_longitude_deg"] == 311.7897
    assert packet["target_placeholders"]["target.vimshottari_start_date"] == "1986-05-18"
    assert packet["target_placeholders"]["target.shadbala_components"]["Sun"]["sthana"] == 100.0
