#!/usr/bin/env python3
"""Tests for Dasha-only external oracle evidence validation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYJHORA_PACKET = ROOT / "references/oracle/artifacts/pending_packets/external_template_steve_jobs_dasha_lahiri_pyjhora_20260627.json"


def _run_validator(queue_file: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
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


def _queue_from_packet(tmp_path: Path, packet: dict) -> Path:
    queue = {
        "tasks": [
            {
                "task_id": "collect_template_steve_jobs_dasha_lahiri",
                "case_id": "template_steve_jobs_dasha_lahiri",
                "status": packet.get("status", "draft"),
                "target_fields": ["target.vimshottari_start_date", "target.shadbala_components"],
                "evidence_packet": packet,
            }
        ]
    }
    queue_file = tmp_path / "queue.json"
    queue_file.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    return queue_file


def test_dasha_validator_accepts_dasha_only_external_pyjhora_packet(tmp_path: Path) -> None:
    packet = json.loads(PYJHORA_PACKET.read_text(encoding="utf-8"))
    queue_file = _queue_from_packet(tmp_path, packet)

    completed = _run_validator(queue_file)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "dasha_external_oracle_evidence_validation"
    assert report["summary"]["total_dasha_packets"] == 1
    assert report["summary"]["valid_dasha_packets"] == 1
    assert report["summary"]["ready_for_dasha_calibration"] == 1
    assert report["summary"]["all_dasha_packets_external_verified"] is True
    assert report["packets"][0]["valid"] is True
    assert report["packets"][0]["problems"] == []


def test_dasha_validator_rejects_local_engine_dasha_artifact(tmp_path: Path) -> None:
    packet = json.loads(PYJHORA_PACKET.read_text(encoding="utf-8"))
    packet["metadata"]["tool_name"] = "local engine"
    packet["metadata"]["operator_note"] = "Generated from scripts/jyotish_engine.py"
    queue_file = _queue_from_packet(tmp_path, packet)

    completed = _run_validator(queue_file)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["summary"]["valid_dasha_packets"] == 0
    assert report["summary"]["ready_for_dasha_calibration"] == 0
    assert report["packets"][0]["valid"] is False
    assert "local_engine_artifact_rejected" in report["packets"][0]["problems"]


def test_dasha_validator_rejects_missing_dasha_date(tmp_path: Path) -> None:
    packet = json.loads(PYJHORA_PACKET.read_text(encoding="utf-8"))
    packet["target_placeholders"]["target.vimshottari_start_date"] = ""
    queue_file = _queue_from_packet(tmp_path, packet)

    completed = _run_validator(queue_file)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["summary"]["valid_dasha_packets"] == 0
    assert "placeholder_unfilled:target.vimshottari_start_date" in report["packets"][0]["problems"]
