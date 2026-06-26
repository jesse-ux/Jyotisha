#!/usr/bin/env python3
"""Regression tests for external Dasha/Shadbala oracle boundary reporting."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_oracle_boundary_audit_reports_dasha_and_shadbala_boundaries() -> None:
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
    assert report["summary"]["dasha_cases"] >= 1
    assert report["summary"]["shadbala_cases"] >= 1
    assert report["summary"]["longitude_cases"] >= 1
    assert report["summary"]["template_cases"] >= 5
    assert report["summary"]["template_status_counts"]["template_only"] >= 5
    assert report["summary"]["template_status_counts"].get("external_verified", 0) == 0
    assert report["summary"]["production_tuning_recommended"] is False
    assert "template cases" in " ".join(report["summary"]["open_items"])

    dasha = report["dasha_cases"][0]
    assert dasha["case_id"] == "pdf_user_REDACTED_YEAR_redacted_place_vimshottari_boundary"
    assert dasha["engine_start_datetime"].startswith("1986-05-23T22:45:10")
    assert dasha["target_start_date"] == "1986-05-18"
    assert dasha["date_delta_days"] == 5
    assert dasha["required_moon_delta_degrees"] > 0
    assert dasha["calibration_decision"] == "do_not_tune_single_reference"

    shadbala = report["shadbala_cases"][0]
    assert shadbala["case_id"] == "pdf_user_REDACTED_YEAR_redacted_place_shadbala_absolute_boundary"
    assert shadbala["engine_method"].startswith("Shadbala六重力量")
    assert shadbala["component_oracle_status"] == "component_targets_sample_only"
    assert shadbala["target_authority"] == "sample_only_not_external_oracle"
    assert shadbala["calibration_decision"] == "component_oracle_required"
    assert shadbala["engine_totals"]["Sun"]["total_rupas"] > 0
    assert shadbala["engine_totals"]["Sun"]["components"]["sthana_bala"] > 0

    longitude = report["longitude_cases"][0]
    assert longitude["case_id"] == "vedastro_user_REDACTED_YEAR_redacted_place_longitude_boundary"
    assert longitude["target_source"] == "vedastro_python_sdk_antigravity_2026_06_24"
    assert longitude["calibration_decision"] == "external_position_reference_only"
    assert longitude["comparisons"]["Moon"]["engine_sign"] == "Aquarius"
    assert longitude["comparisons"]["Moon"]["target_sign"] == "Aquarius"
    assert longitude["comparisons"]["Moon"]["abs_delta_arcsec"] > 0
    assert longitude["max_abs_delta_arcsec"] < 120
    assert longitude["within_threshold"] is True

    template = report["template_cases"][0]
    assert template["case_id"] == "template_user_REDACTED_YEAR_moon_longitude_lahiri"
    assert template["status"] == "template_only"
    assert template["ready_for_calibration"] is False
    assert template["missing_target_fields"]


def test_oracle_boundary_audit_compares_external_verified_template_rows(tmp_path: Path) -> None:
    oracle = json.loads((ROOT / "references/oracle/dasha_shadbala_oracle_cases.json").read_text(encoding="utf-8"))
    case = oracle["template_cases"][1]
    case["status"] = "external_verified"
    case["target"]["vimshottari_start_date"] = "1951-11-01"
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
    assert report["summary"]["external_verified_template_cases"] == 1
    assert report["summary"]["production_tuning_recommended"] is False
    comparison = report["template_comparisons"][0]
    assert comparison["case_id"] == "template_steve_jobs_dasha_lahiri"
    assert comparison["status"] == "external_verified"
    assert comparison["dasha"]["target_start_date"] == "1951-11-01"
    assert comparison["dasha"]["date_delta_days"] is not None
    assert comparison["shadbala"]["planets"]["Sun"]["external_total_rupa"] == 21.0
    assert comparison["shadbala"]["planets"]["Sun"]["total_rupa_delta"] is not None
    assert comparison["calibration_decision"] == "do_not_tune_single_template"
