#!/usr/bin/env python3
"""Regression tests for external Dasha/Shadbala oracle boundary reporting."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_oracle_boundary_audit_reports_redacted_public_template_boundaries() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/oracle_boundary_audit.py",
            "--oracle-file",
            "references/oracle/dasha_shadbala_oracle_cases.json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "external_oracle_boundary_audit"
    assert report["summary"]["dasha_cases"] == 0
    assert report["summary"]["shadbala_cases"] == 0
    assert report["summary"]["longitude_cases"] == 0
    assert report["summary"]["template_cases"] >= 4
    assert report["summary"]["template_status_counts"]["template_only"] >= 1
    assert report["summary"]["template_status_counts"].get("external_verified", 0) >= 3
    assert report["summary"]["production_tuning_recommended"] is False
    assert any(row["case_id"] == "template_steve_jobs_dasha_lahiri" for row in report["template_cases"])
    assert not report["dasha_cases"]
    assert not report["shadbala_cases"]
    assert not report["longitude_cases"]

def test_oracle_boundary_audit_compares_external_verified_template_rows(tmp_path: Path) -> None:
    oracle = json.loads((ROOT / "references/oracle/dasha_shadbala_oracle_cases.json").read_text(encoding="utf-8"))
    case = oracle["template_cases"][0]
    case["status"] = "external_verified"
    case["target"]["vimshottari_start_date"] = "1939-03-22"
    case["target"]["shadbala_components"] = {
        planet: {
            "sthana": 1.0,
            "dig": 2.0,
            "kala": 3.0,
            "chesta": 4.0,
            "naisargika": 5.0,
            "drik": 6.0,
            "total_rupa": 21.0,
        }
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    }
    case["evidence_packet"] = {
        "capture_id": "external_template_steve_jobs_dasha_lahiri",
        "status": "external_verified",
        "metadata": {
            "tool_name": "JHora",
            "tool_version_or_url": "manual-jhora-8.0",
            "capture_date": "2026-06-26",
            "source_artifact": "references/oracle/artifacts/steve_jobs_jhora_redacted.png",
            "ayanamsa": "lahiri",
            "node_mode": "true",
            "timezone": "UTC-08:00",
            "operator_note": "Typed from redacted external JHora screenshot.",
        },
    }
    oracle_path = tmp_path / "oracle.json"
    oracle_path.write_text(json.dumps(oracle, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/oracle_boundary_audit.py",
            "--oracle-file",
            str(oracle_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["summary"]["external_verified_template_cases"] >= 3
    assert report["summary"]["production_tuning_recommended"] is False
    comparison = next(
        row for row in report["template_comparisons"]
        if row["case_id"] == "template_steve_jobs_dasha_lahiri"
    )
    assert comparison["case_id"] == "template_steve_jobs_dasha_lahiri"
    assert comparison["status"] == "external_verified"
    assert comparison["dasha"]["target_start_date"] == "1939-03-22"
    assert comparison["dasha"]["date_delta_days"] is not None
    assert comparison["shadbala"]["planets"]["Sun"]["external_total_rupa"] == 21.0
    assert comparison["shadbala"]["planets"]["Sun"]["total_rupa_delta"] is not None
    assert comparison["shadbala"]["unit"] == "rupa"
    assert comparison["shadbala"]["component_tolerances"]["sthana"] == 0.1
    assert comparison["shadbala"]["component_tolerances"]["drik"] == 1.5
    assert comparison["shadbala"]["planets"]["Sun"]["component_deltas"]["sthana"]["tolerance_rupa"] == 0.1
    assert comparison["shadbala"]["planets"]["Sun"]["component_deltas"]["drik"]["tolerance_rupa"] == 1.5
    assert comparison["shadbala"]["global_scaling_check"]["allowed"] is False
    assert comparison["shadbala"]["global_scaling_check"]["recommendation"] == "reject_global_scaling"
    assert comparison["calibration_decision"] == "do_not_tune_single_template"
