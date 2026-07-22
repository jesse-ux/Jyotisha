#!/usr/bin/env python3
"""Regression tests for Dig Bala source-of-truth audit."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.shadbala_dig_source_of_truth_audit import build_report


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "references/oracle/shadbala_dig_source_of_truth_audit_2026_07_22.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_shadbala_dig_source_of_truth_audit_compares_three_candidate_models() -> None:
    report = build_report("references/oracle/dasha_shadbala_oracle_cases.json")

    assert report["scope"] == "shadbala_dig_source_of_truth_audit"
    assert report["summary"]["case_count"] >= 1
    assert set(report["candidate_models"]) == {
        "current_linear_house_model",
        "house_midpoint_angular_model",
        "bhava_madhya_angular_model",
    }
    assert report["summary"]["best_model_by_avg_abs_diff"] in report["candidate_models"]
    assert report["rows"]
    assert report["inputs"]["oracle_file_sha256"]
    assert report["inputs"]["external_case_count"] == 2
    assert {
        row["case_id"] for row in report["inputs"]["external_case_sources"]
    } == {"template_steve_jobs_dasha_lahiri", "template_extreme_latitude_kp"}
    assert all(row["source_artifact"] for row in report["inputs"]["external_case_sources"])


def test_shadbala_dig_source_of_truth_audit_writes_reproducible_snapshot(tmp_path: Path) -> None:
    output = tmp_path / "dig-audit.json"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/shadbala_dig_source_of_truth_audit.py",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8")) == json.loads(completed.stdout)


def test_checked_in_dig_audit_snapshot_matches_generator_and_is_indexed() -> None:
    assert json.loads(SNAPSHOT.read_text(encoding="utf-8")) == build_report(
        "references/oracle/dasha_shadbala_oracle_cases.json"
    )
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["shadbala_dig_source_of_truth_audit_2026_07_22"]
    assert packet["claim_status"] == "partial"
    assert packet["consumer_policy"] == "research_observation_only"
