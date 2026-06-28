#!/usr/bin/env python3
"""Regression tests for external oracle evidence packet validation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHADBALA_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
SHADBALA_COMPONENTS = ["sthana", "dig", "kala", "chesta", "naisargika", "drik"]


def complete_shadbala_components() -> dict[str, dict[str, float]]:
    result = {}
    for planet_index, planet in enumerate(SHADBALA_PLANETS):
        row = {
            component: round(0.1 + planet_index * 0.01 + component_index * 0.02, 4)
            for component_index, component in enumerate(SHADBALA_COMPONENTS)
        }
        row["total_rupa"] = round(sum(row[component] for component in SHADBALA_COMPONENTS), 4)
        result[planet] = row
    return result


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


def test_validator_accepts_current_external_packets_but_rejects_remaining_drafts(tmp_path: Path) -> None:
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(build_queue(), ensure_ascii=False), encoding="utf-8")

    completed = run_validator(queue_path)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "external_oracle_evidence_validation"
    assert report["summary"]["total_packets"] == 6
    assert report["summary"]["valid_packets"] == 4
    assert report["summary"]["ready_for_calibration"] == 4
    assert report["summary"]["all_packets_external_verified"] is False
    first = report["packets"][0]
    assert first["capture_id"] == "external_template_user_REDACTED_YEAR_moon_longitude_lahiri"
    assert first["valid"] is True
    assert first["problems"] == []
    remaining_invalid = [packet for packet in report["packets"] if not packet["valid"]]
    assert remaining_invalid
    assert any("placeholder_unfilled:" in problem for packet in remaining_invalid for problem in packet["problems"])
    assert any(
        packet["capture_id"] == "external_template_historical_epoch_lahiri"
        and "placeholder_unfilled:target.sun_sidereal_longitude_deg" in packet["problems"]
        for packet in remaining_invalid
    )


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
        "target.shadbala_components": complete_shadbala_components(),
    }
    packet["status"] = "external_verified"
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")

    completed = run_validator(queue_path)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["summary"]["valid_packets"] == 4
    assert report["summary"]["ready_for_calibration"] == 4
    assert report["summary"]["all_packets_external_verified"] is False
    first = report["packets"][0]
    assert first["valid"] is True
    assert first["problems"] == []


def test_validator_rejects_incomplete_shadbala_component_rows(tmp_path: Path) -> None:
    queue = build_queue()
    packet = queue["tasks"][0]["evidence_packet"]
    packet["metadata"] = {
        "tool_name": "JHora",
        "tool_version_or_url": "manual-screenshot-v1",
        "capture_date": "2026-06-25",
        "source_artifact": "references/oracle/artifacts/manual_jhora_user_REDACTED_YEAR.png",
        "ayanamsa": "lahiri",
        "node_mode": "mean",
        "timezone": "UTC+08:00",
        "operator_note": "Manual external screenshot; values typed from JHora screen.",
    }
    packet["target_placeholders"] = {
        "target.moon_sidereal_longitude_deg": 311.7897,
        "target.vimshottari_start_date": "1986-05-18",
        "target.shadbala_components": {
            "Sun": {
                "sthana": 100.0,
                "dig": 50.0,
            }
        },
    }
    packet["status"] = "external_verified"
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")

    completed = run_validator(queue_path)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    first = report["packets"][0]
    assert first["valid"] is False
    assert "missing_shadbala_component:Sun.kala" in first["problems"]
    assert "missing_shadbala_component:Sun.chesta" in first["problems"]
    assert "missing_shadbala_component:Sun.naisargika" in first["problems"]
    assert "missing_shadbala_component:Sun.drik" in first["problems"]
    assert "missing_shadbala_component:Moon" in first["problems"]


def test_validator_rejects_non_numeric_or_negative_shadbala_components(tmp_path: Path) -> None:
    queue = build_queue()
    packet = queue["tasks"][0]["evidence_packet"]
    shadbala = complete_shadbala_components()
    shadbala["Sun"]["sthana"] = "100"
    shadbala["Moon"]["kala"] = -1.0
    packet["metadata"] = {
        "tool_name": "JHora",
        "tool_version_or_url": "manual-screenshot-v1",
        "capture_date": "2026-06-25",
        "source_artifact": "references/oracle/artifacts/manual_jhora_user_REDACTED_YEAR.png",
        "ayanamsa": "lahiri",
        "node_mode": "mean",
        "timezone": "UTC+08:00",
        "operator_note": "Manual external screenshot; values typed from JHora screen.",
    }
    packet["target_placeholders"] = {
        "target.moon_sidereal_longitude_deg": 311.7897,
        "target.vimshottari_start_date": "1986-05-18",
        "target.shadbala_components": shadbala,
    }
    packet["status"] = "external_verified"
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")

    completed = run_validator(queue_path)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    first = report["packets"][0]
    assert first["valid"] is False
    assert "invalid_shadbala_component_type:Sun.sthana" in first["problems"]
    assert "invalid_shadbala_component_negative:Moon.kala" in first["problems"]


def test_validator_accepts_negative_drik_bala_when_component_sum_matches(tmp_path: Path) -> None:
    queue = build_queue()
    packet = queue["tasks"][0]["evidence_packet"]
    shadbala = complete_shadbala_components()
    shadbala["Sun"]["drik"] = -0.25
    shadbala["Sun"]["total_rupa"] = round(sum(shadbala["Sun"][component] for component in SHADBALA_COMPONENTS), 4)
    packet["metadata"] = {
        "tool_name": "PyJHora",
        "tool_version_or_url": "PyJHora 4.8.7 isolated /tmp black-box run",
        "capture_date": "2026-06-27",
        "source_artifact": "references/oracle/artifacts/pyjhora_shadbala_stdout.txt",
        "ayanamsa": "raman",
        "node_mode": "PyJHora default",
        "timezone": "UTC+08:00",
        "operator_note": "Black-box external stdout; Drik Bala can be negative.",
    }
    packet["target_placeholders"] = {
        "target.moon_sidereal_longitude_deg": 311.7897,
        "target.vimshottari_start_date": "1986-05-18",
        "target.shadbala_components": shadbala,
    }
    packet["status"] = "external_verified"
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")

    completed = run_validator(queue_path)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    first = report["packets"][0]
    assert first["valid"] is True
    assert first["problems"] == []


def test_validator_accepts_pyjhora_negative_dig_and_drik_values(tmp_path: Path) -> None:
    queue = build_queue()
    packet = queue["tasks"][0]["evidence_packet"]
    shadbala = complete_shadbala_components()
    for component in SHADBALA_COMPONENTS:
        shadbala["Moon"][component] = 1.0
    shadbala["Moon"]["dig"] = -0.5255
    shadbala["Moon"]["drik"] = -0.0947
    shadbala["Moon"]["total_rupa"] = round(sum(shadbala["Moon"][component] for component in SHADBALA_COMPONENTS), 4)
    shadbala["Jupiter"]["drik"] = -0.0692
    shadbala["Jupiter"]["total_rupa"] = round(sum(shadbala["Jupiter"][component] for component in SHADBALA_COMPONENTS), 4)
    packet["metadata"] = {
        "tool_name": "PyJHora",
        "tool_version_or_url": "PyJHora 4.8.7 isolated /tmp black-box run",
        "capture_date": "2026-06-27",
        "source_artifact": "references/oracle/artifacts/pyjhora_user_REDACTED_YEAR_shadbala_lahiri_stdout_20260627.txt",
        "ayanamsa": "lahiri",
        "node_mode": "PyJHora default",
        "timezone": "UTC+08:00",
        "operator_note": "Black-box external stdout; PyJHora can emit negative Dig and Drik Bala values.",
    }
    packet["target_placeholders"] = {
        "target.moon_sidereal_longitude_deg": 311.774424,
        "target.vimshottari_start_date": "1986-05-25",
        "target.shadbala_components": shadbala,
    }
    packet["status"] = "external_verified"
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")

    completed = run_validator(queue_path)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    first = report["packets"][0]
    assert first["valid"] is True
    assert first["problems"] == []


def test_validator_rejects_missing_shadbala_total_rupa(tmp_path: Path) -> None:
    queue = build_queue()
    packet = queue["tasks"][0]["evidence_packet"]
    shadbala = complete_shadbala_components()
    del shadbala["Sun"]["total_rupa"]
    packet["metadata"] = {
        "tool_name": "JHora",
        "tool_version_or_url": "manual-screenshot-v1",
        "capture_date": "2026-06-25",
        "source_artifact": "references/oracle/artifacts/manual_jhora_user_REDACTED_YEAR.png",
        "ayanamsa": "lahiri",
        "node_mode": "mean",
        "timezone": "UTC+08:00",
        "operator_note": "Manual external screenshot; values typed from JHora screen.",
    }
    packet["target_placeholders"] = {
        "target.moon_sidereal_longitude_deg": 311.7897,
        "target.vimshottari_start_date": "1986-05-18",
        "target.shadbala_components": shadbala,
    }
    packet["status"] = "external_verified"
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")

    completed = run_validator(queue_path)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    first = report["packets"][0]
    assert first["valid"] is False
    assert "missing_shadbala_total_rupa:Sun" in first["problems"]


def test_validator_rejects_shadbala_component_values_above_20_rupas(tmp_path: Path) -> None:
    queue = build_queue()
    packet = queue["tasks"][0]["evidence_packet"]
    shadbala = complete_shadbala_components()
    shadbala["Sun"]["sthana"] = 20.01
    shadbala["Sun"]["total_rupa"] = round(sum(shadbala["Sun"][component] for component in SHADBALA_COMPONENTS), 4)
    packet["metadata"] = {
        "tool_name": "JHora",
        "tool_version_or_url": "manual-screenshot-v1",
        "capture_date": "2026-06-25",
        "source_artifact": "references/oracle/artifacts/manual_jhora_user_REDACTED_YEAR.png",
        "ayanamsa": "lahiri",
        "node_mode": "mean",
        "timezone": "UTC+08:00",
        "operator_note": "Manual external screenshot; values typed from JHora screen.",
    }
    packet["target_placeholders"] = {
        "target.moon_sidereal_longitude_deg": 311.7897,
        "target.vimshottari_start_date": "1986-05-18",
        "target.shadbala_components": shadbala,
    }
    packet["status"] = "external_verified"
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")

    completed = run_validator(queue_path)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    first = report["packets"][0]
    assert first["valid"] is False
    assert "invalid_shadbala_component_range:Sun.sthana" in first["problems"]


def test_validator_rejects_shadbala_total_rupa_sum_mismatch(tmp_path: Path) -> None:
    queue = build_queue()
    packet = queue["tasks"][0]["evidence_packet"]
    shadbala = complete_shadbala_components()
    shadbala["Sun"]["total_rupa"] = round(shadbala["Sun"]["total_rupa"] + 0.06, 4)
    packet["metadata"] = {
        "tool_name": "JHora",
        "tool_version_or_url": "manual-screenshot-v1",
        "capture_date": "2026-06-25",
        "source_artifact": "references/oracle/artifacts/manual_jhora_user_REDACTED_YEAR.png",
        "ayanamsa": "lahiri",
        "node_mode": "mean",
        "timezone": "UTC+08:00",
        "operator_note": "Manual external screenshot; values typed from JHora screen.",
    }
    packet["target_placeholders"] = {
        "target.moon_sidereal_longitude_deg": 311.7897,
        "target.vimshottari_start_date": "1986-05-18",
        "target.shadbala_components": shadbala,
    }
    packet["status"] = "external_verified"
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")

    completed = run_validator(queue_path)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    first = report["packets"][0]
    assert first["valid"] is False
    assert "shadbala_total_rupa_sum_mismatch:Sun" in first["problems"]


def test_validator_rejects_invalid_ashtakoot_score_ranges(tmp_path: Path) -> None:
    queue = build_queue_from_file(ROOT / "references/oracle/ashtakoot_oracle_cases.json")
    packet = queue["tasks"][0]["evidence_packet"]
    packet["metadata"] = {
        "tool_name": "VedAstro",
        "tool_version_or_url": "https://vedastro.org/API",
        "capture_date": "2026-06-25",
        "source_artifact": "references/oracle/artifacts/manual_ashtakoot_case_01.png",
        "ayanamsa": "lahiri",
        "node_mode": "true",
        "timezone": "UTC-08:00",
        "operator_note": "External compatibility calculator screenshot.",
    }
    packet["target_placeholders"] = {
        "target.total_score": 99.0,
        "target.varna": 1.0,
        "target.vashya": 2.0,
        "target.tara": 3.0,
        "target.yoni": 4.0,
        "target.graha_maitri": 5.0,
        "target.gana": 6.0,
        "target.bhakoot": 7.0,
        "target.nadi": 99.0,
        "target.kuja_status": "",
    }
    packet["status"] = "external_verified"
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")

    completed = run_validator(queue_path)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    first = report["packets"][0]
    assert first["valid"] is False
    assert "invalid_ashtakoot_score_range:target.total_score" in first["problems"]
    assert "invalid_ashtakoot_score_range:target.nadi" in first["problems"]
    assert "placeholder_unfilled:target.kuja_status" in first["problems"]


def test_validator_rejects_ashtakoot_score_sum_mismatch(tmp_path: Path) -> None:
    queue = build_queue_from_file(ROOT / "references/oracle/ashtakoot_oracle_cases.json")
    packet = queue["tasks"][0]["evidence_packet"]
    packet["metadata"] = {
        "tool_name": "VedAstro",
        "tool_version_or_url": "https://vedastro.org/API",
        "capture_date": "2026-06-25",
        "source_artifact": "references/oracle/artifacts/manual_ashtakoot_case_01.png",
        "ayanamsa": "lahiri",
        "node_mode": "true",
        "timezone": "UTC-08:00",
        "operator_note": "External compatibility calculator screenshot.",
    }
    packet["target_placeholders"] = {
        "target.total_score": 20.0,
        "target.varna": 1.0,
        "target.vashya": 2.0,
        "target.tara": 3.0,
        "target.yoni": 4.0,
        "target.graha_maitri": 5.0,
        "target.gana": 6.0,
        "target.bhakoot": 7.0,
        "target.nadi": 8.0,
        "target.kuja_status": "no_dosha",
    }
    packet["status"] = "external_verified"
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")

    completed = run_validator(queue_path)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    first = report["packets"][0]
    assert first["valid"] is False
    assert "ashtakoot_score_sum_mismatch" in first["problems"]


def test_validator_accepts_valid_ashtakoot_external_packet(tmp_path: Path) -> None:
    queue = build_queue_from_file(ROOT / "references/oracle/ashtakoot_oracle_cases.json")
    packet = queue["tasks"][0]["evidence_packet"]
    packet["metadata"] = {
        "tool_name": "VedAstro",
        "tool_version_or_url": "https://vedastro.org/API",
        "capture_date": "2026-06-25",
        "source_artifact": "references/oracle/artifacts/manual_ashtakoot_case_01.png",
        "ayanamsa": "lahiri",
        "node_mode": "true",
        "timezone": "UTC-08:00",
        "operator_note": "External compatibility calculator screenshot.",
    }
    packet["target_placeholders"] = {
        "target.total_score": 18.0,
        "target.varna": 1.0,
        "target.vashya": 1.0,
        "target.tara": 2.0,
        "target.yoni": 3.0,
        "target.graha_maitri": 4.0,
        "target.gana": 2.0,
        "target.bhakoot": 3.0,
        "target.nadi": 2.0,
        "target.kuja_status": "no_dosha",
    }
    packet["status"] = "external_verified"
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")

    completed = run_validator(queue_path)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
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
        "shadbala_components": complete_shadbala_components(),
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
    assert report["summary"]["valid_packets"] == 4
    assert report["summary"]["ready_for_calibration"] == 4
    assert report["summary"]["production_tuning_allowed"] is False
    assert report["packets"][0]["valid"] is True
    assert report["packets"][0]["problems"] == []
