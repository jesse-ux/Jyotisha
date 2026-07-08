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
    assert report["summary"]["total_tasks"] == 4
    assert report["summary"]["ready_for_calibration"] == 3
    assert report["summary"]["ready_for_collection"] == 1
    assert report["summary"]["by_status"]["external_verified"] == 3
    assert report["summary"]["by_status"]["template_only"] == 1
    assert report["summary"]["production_tuning_allowed"] is False

    first = report["tasks"][0]
    assert first["case_id"] == "template_steve_jobs_dasha_lahiri"
    assert first["status"] == "external_verified"
    assert first["ready_for_collection"] is False
    assert first["ready_for_calibration"] is True
    assert first["missing_target_fields"] == []
    assert "dasha" in first["target_modules"]
    assert "shadbala" in first["target_modules"]
    assert any("JHora" in source for source in first["preferred_sources"])
    assert any("VedAstro" in source for source in first["preferred_sources"])
    assert first["promotion_criteria"]
    assert first["do_not_tune_production"] is False

    packet = first["evidence_packet"]
    assert packet["capture_id"] == "external_template_steve_jobs_dasha_lahiri"
    assert packet["status"] == "external_verified"
    assert packet["case_id"] == first["case_id"]
    assert packet["birth"] == first["birth"]
    assert packet["settings"] == first["settings"]
    assert "tool_name" in packet["required_metadata_fields"]
    assert "tool_version_or_url" in packet["required_metadata_fields"]
    assert "capture_date" in packet["required_metadata_fields"]
    assert "source_artifact" in packet["required_metadata_fields"]
    assert packet["integrity_checks"]["must_not_come_from_local_engine"] is True
    assert packet["integrity_checks"]["requires_external_artifact"] is True

    historical = next(task for task in report["tasks"] if task["case_id"] == "template_historical_epoch_lahiri")
    assert historical["status"] == "external_verified"
    assert historical["ready_for_collection"] is False
    assert historical["ready_for_calibration"] is True
    assert historical["do_not_tune_production"] is False
    assert historical["missing_target_fields"] == []
    assert historical["evidence_packet"]["target_placeholders"]["target.sun_sidereal_longitude_deg"] == 259.882698

    raman = next(task for task in report["tasks"] if task["case_id"] == "template_bv_raman_vimshottari_boundary_series")
    assert raman["status"] == "template_only"
    assert raman["ready_for_collection"] is True
    assert raman["ready_for_calibration"] is False
    assert raman["blocked_reason"] == ""
    assert raman["missing_target_fields"] == []
    assert raman["evidence_packet"]["status"] == "draft"


def test_oracle_collection_queue_outputs_markdown_table() -> None:
    completed = run_queue("--format", "markdown")
    assert completed.returncode == 0, completed.stderr or completed.stdout
    markdown = completed.stdout

    assert "# Dasha/Shadbala External Oracle Collection Queue" in markdown
    assert "| task_id | case_id | status | missing fields | preferred sources |" in markdown
    assert "collect_template_steve_jobs_dasha_lahiri" in markdown
    assert "`external_verified`" in markdown
    assert "collect_template_bv_raman_vimshottari_boundary_series" in markdown
    assert "template_only" in markdown
    assert "production_tuning_allowed: `false`" in markdown
    assert "Evidence Packet Fields" in markdown
    assert "tool_name" in markdown
    assert "capture_id" in markdown


def test_oracle_collection_queue_can_write_draft_evidence_packets(tmp_path: Path) -> None:
    completed = run_queue("--write-packet-dir", str(tmp_path))

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["summary"]["written_evidence_packets"] == 4

    packet_path = tmp_path / "external_template_steve_jobs_dasha_lahiri.json"
    assert packet_path.exists()
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet["capture_id"] == "external_template_steve_jobs_dasha_lahiri"
    assert packet["status"] == "external_verified"
    assert packet["case_id"] == "template_steve_jobs_dasha_lahiri"
    assert packet["metadata"]["source_artifact"].startswith("references/oracle/artifacts/")
    assert packet["metadata"]["tool_name"] == "PyJHora"
    assert packet["target_placeholders"]["target.vimshottari_start_date"] == "1939-03-22"
    shadbala = packet["target_placeholders"]["target.shadbala_components"]
    assert set(shadbala) == {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    assert set(shadbala["Sun"]) == {"sthana", "dig", "kala", "chesta", "naisargika", "drik", "total_rupa"}
    assert packet["integrity_checks"]["must_not_come_from_local_engine"] is True


def test_oracle_collection_queue_can_apply_filled_evidence_packet(tmp_path: Path) -> None:
    oracle = json.loads((ROOT / "references/oracle/dasha_shadbala_oracle_cases.json").read_text(encoding="utf-8"))
    oracle_path = tmp_path / "oracle.json"
    oracle_path.write_text(json.dumps(oracle, ensure_ascii=False), encoding="utf-8")

    packet_dir = tmp_path / "packets"
    generated = run_queue_for_file(oracle_path, "--write-packet-dir", str(packet_dir))
    assert generated.returncode == 0, generated.stderr or generated.stdout

    packet_path = packet_dir / "external_template_steve_jobs_dasha_lahiri.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet["status"] = "external_verified"
    packet["metadata"].update(
        {
            "tool_name": "JHora",
            "tool_version_or_url": "manual-jhora-8.0",
            "capture_date": "2026-06-26",
            "source_artifact": "references/oracle/artifacts/steve_jobs_jhora_redacted.png",
            "ayanamsa": "lahiri",
            "node_mode": "true",
            "timezone": "UTC-08:00",
            "operator_note": "Typed from redacted external JHora screenshot.",
        }
    )
    packet["target_placeholders"]["target.vimshottari_start_date"] = "1951-11-01"
    packet["target_placeholders"]["target.shadbala_components"] = {
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
    packet_path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")

    applied = run_queue_for_file(oracle_path, "--apply-packet", str(packet_path))

    assert applied.returncode == 0, applied.stderr or applied.stdout
    report = json.loads(applied.stdout)
    assert report["summary"]["applied_evidence_packets"] == 1

    updated = json.loads(oracle_path.read_text(encoding="utf-8"))
    case = next(row for row in updated["template_cases"] if row["id"] == "template_steve_jobs_dasha_lahiri")
    assert case["status"] == "external_verified"
    assert case["target"]["vimshottari_start_date"] == "1951-11-01"
    assert case["target"]["shadbala_components"]["Sun"]["total_rupa"] == 21.0
    assert case["evidence_packet"]["metadata"]["tool_name"] == "JHora"


def test_first_jhora_evidence_packet_template_is_safe_and_fillable() -> None:
    template = ROOT / "references" / "oracle" / "evidence_packet_templates" / "jhora_steve_jobs_lahiri_first_packet.json"
    assert template.exists()
    packet = json.loads(template.read_text(encoding="utf-8"))

    assert packet["capture_id"] == "external_template_steve_jobs_dasha_lahiri"
    assert packet["status"] == "draft"
    assert packet["case_id"] == "template_steve_jobs_dasha_lahiri"
    assert packet["metadata"]["tool_name"] == ""
    assert packet["metadata"]["source_artifact"] == "references/oracle/artifacts/"
    assert packet["metadata"]["ayanamsa"] == "Lahiri"
    assert packet["metadata"]["node_mode"] == "true node"
    assert packet["integrity_checks"]["must_not_come_from_local_engine"] is True
    assert packet["integrity_checks"]["requires_external_artifact"] is True
    assert packet["integrity_checks"]["reject_global_shadbala_scaling"] is True
    assert packet["target_placeholders"]["target.vimshottari_start_date"] is None

    shadbala = packet["target_placeholders"]["target.shadbala_components"]
    assert set(shadbala) == {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    for row in shadbala.values():
        assert set(row) == {"sthana", "dig", "kala", "chesta", "naisargika", "drik"}
        assert all(value is None for value in row.values())


def test_ashtakoot_oracle_cases_generate_collection_tasks() -> None:
    oracle_file = ROOT / "references" / "oracle" / "ashtakoot_oracle_cases.json"
    assert oracle_file.exists()

    completed = run_queue_for_file(oracle_file, "--format", "json")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "external_oracle_collection_queue"
    assert report["summary"]["total_tasks"] == 5
    assert report["summary"]["ready_for_calibration"] == 0
    assert report["summary"]["production_tuning_allowed"] is False

    first = report["tasks"][0]
    assert first["case_id"] == "ashtakoot_public_couple_lahiri_01"
    assert first["privacy"] == "public_or_synthetic_relationship_template"
    assert "ashtakoot" in first["target_modules"]
    assert any("JHora" in source for source in first["preferred_sources"])
    assert any("VedAstro" in source for source in first["preferred_sources"])
    for field in [
        "target.total_score",
        "target.varna",
        "target.vashya",
        "target.tara",
        "target.yoni",
        "target.graha_maitri",
        "target.gana",
        "target.bhakoot",
        "target.nadi",
        "target.kuja_status",
    ]:
        assert field in first["target_fields"]
        assert field in first["evidence_packet"]["target_placeholders"]
    assert first["evidence_packet"]["integrity_checks"]["must_not_come_from_local_engine"] is True
    assert first["do_not_tune_production"] is True


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
            "source_artifact": "references/oracle/artifacts/pyjhora_steve_jobs_shadbala_lahiri_stdout_20260627.txt",
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
    assert report["summary"]["ready_for_calibration"] == 3
    assert report["summary"]["production_tuning_allowed"] is False

    packet = first["evidence_packet"]
    assert packet["status"] == "external_verified"
    assert packet["metadata"]["tool_name"] == "JHora"
    assert packet["target_placeholders"]["target.moon_sidereal_longitude_deg"] == 311.7897
    assert packet["target_placeholders"]["target.vimshottari_start_date"] == "1986-05-18"
    assert packet["target_placeholders"]["target.shadbala_components"]["Sun"]["sthana"] == 100.0


def test_oracle_collection_queue_recognizes_vimshottari_boundary_series(tmp_path: Path) -> None:
    oracle = {
        "schema_version": 1,
        "scope": "external_dasha_boundary_series_oracle_cases",
        "template_cases": [
            {
                "id": "template_bv_raman_vimshottari_boundary_series",
                "status": "template_only",
                "source": "B.V. Raman Hindu Predictive Astrology published example",
                "privacy": "public_reference_chart",
                "birth": {
                    "year": 1912,
                    "month": 8,
                    "day": 8,
                    "hour": 19,
                    "minute": 43,
                    "second": 0,
                    "lat": 13.0,
                    "lon": 77.583333,
                    "tz": 5.5,
                },
                "settings": {
                    "ayanamsa": "raman",
                    "node_mode": "unspecified",
                    "year_length_policy": "source_boundary_dates",
                },
                "target": {
                    "vimshottari_mahadasa_boundaries": {
                        "Mars": "1912-08-08",
                        "Rahu": "1918-09-21",
                        "Jupiter": "1936-09-21",
                        "Saturn": "1952-09-21",
                        "Mercury": "1971-09-21",
                        "Ketu": "1988-09-21",
                    }
                },
            }
        ],
    }
    oracle_path = tmp_path / "raman_oracle.json"
    oracle_path.write_text(json.dumps(oracle, ensure_ascii=False), encoding="utf-8")

    completed = run_queue_for_file(oracle_path, "--format", "json")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    task = report["tasks"][0]
    assert task["case_id"] == "template_bv_raman_vimshottari_boundary_series"
    assert task["target_modules"] == ["dasha"]
    assert "target.vimshottari_mahadasa_boundaries" in task["target_fields"]
    assert any("boundary dates" in step for step in task["collection_steps"])
    assert task["evidence_packet"]["target_placeholders"]["target.vimshottari_mahadasa_boundaries"]["Rahu"] == "1918-09-21"
