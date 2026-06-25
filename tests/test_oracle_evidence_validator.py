#!/usr/bin/env python3
"""Regression tests for external oracle evidence packet validation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def build_queue() -> dict:
    completed = subprocess.run(
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
        timeout=30,
        check=True,
    )
    return json.loads(completed.stdout)


def build_queue_from_file(oracle_file: Path) -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/oracle_collection_queue.py",
            "--oracle-file",
            str(oracle_file),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=True,
    )
    return json.loads(completed.stdout)


def run_validator(input_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/oracle_evidence_validator.py",
            "--queue-file",
            str(input_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def test_validator_rejects_draft_packets_without_external_artifacts(tmp_path: Path) -> None:
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(build_queue(), ensure_ascii=False), encoding="utf-8")

    completed = run_validator(queue_path)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "external_oracle_evidence_validation"
    assert report["summary"]["total_packets"] == 5
    assert report["summary"]["valid_packets"] == 0
    assert report["summary"]["ready_for_calibration"] == 0
    assert report["summary"]["all_packets_external_verified"] is False
    first = report["packets"][0]
    assert first["capture_id"] == "external_template_user_REDACTED_YEAR_moon_longitude_lahiri"
    assert first["valid"] is False
    assert "missing_metadata:tool_name" in first["problems"]
    assert "missing_external_artifact" in first["problems"]
    assert "placeholder_unfilled:target.moon_sidereal_longitude_deg" in first["problems"]


def test_validator_accepts_filled_external_packet_but_not_whole_queue(tmp_path: Path) -> None:
    queue = build_queue()
    packet = queue["tasks"][0]["evidence_packet"]
    metadata = {
        "tool_name": "JHora",
        "tool_version_or_url": "manual-screenshot-v1",
        "capture_date": "2026-06-25",
        "source_artifact": "docs/research/oracle_artifacts/manual_jhora_user_REDACTED_YEAR.png",
        "ayanamsa": "lahiri",
        "node_mode": "mean",
        "timezone": "UTC+08:00",
        "operator_note": "Manual external screenshot; values typed from JHora screen.",
    }
    packet["metadata"] = metadata
    packet["target_placeholders"] = {
        "target.moon_sidereal_longitude_deg": 311.7897,
        "target.vimshottari_start_date": "1986-05-18",
        "target.shadbala_components": {
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
    packet["status"] = "external_verified"
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")

    completed = run_validator(queue_path)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["summary"]["valid_packets"] == 1
    assert report["summary"]["ready_for_calibration"] == 1
    assert report["summary"]["all_packets_external_verified"] is False
    first = report["packets"][0]
    assert first["valid"] is True
    assert first["problems"] == []


def test_validator_rejects_local_engine_artifact(tmp_path: Path) -> None:
    queue = build_queue()
    packet = queue["tasks"][0]["evidence_packet"]
    packet["metadata"] = {
        "tool_name": "Local Engine",
        "tool_version_or_url": "this-repo",
        "capture_date": "2026-06-25",
        "source_artifact": "scripts/jyotish_engine.py output",
        "ayanamsa": "lahiri",
        "node_mode": "mean",
        "timezone": "UTC+08:00",
        "operator_note": "Local run",
    }
    packet["target_placeholders"] = {
        key: 1 for key in packet["target_placeholders"]
    }
    packet["status"] = "external_verified"
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")

    completed = run_validator(queue_path)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    first = report["packets"][0]
    assert first["valid"] is False
    assert "local_engine_artifact_rejected" in first["problems"]


def test_validator_accepts_external_verified_packet_generated_from_oracle_file(tmp_path: Path) -> None:
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
    queue = build_queue_from_file(oracle_path)
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")

    completed = run_validator(queue_path)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["summary"]["valid_packets"] == 1
    assert report["summary"]["ready_for_calibration"] == 1
    assert report["summary"]["production_tuning_allowed"] is False
    assert report["packets"][0]["valid"] is True
    assert report["packets"][0]["problems"] == []
