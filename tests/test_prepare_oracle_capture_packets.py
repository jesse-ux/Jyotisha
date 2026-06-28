#!/usr/bin/env python3
"""Tests for preparing first external oracle capture packets."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_prepare_oracle_capture_packets_writes_packets_manifest_and_next_steps(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/prepare_oracle_capture_packets.py",
            "--oracle-file",
            "references/oracle/dasha_shadbala_oracle_cases.json",
            "--output-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "external_oracle_capture_packet_preparation"
    assert report["packet_count"] == 6
    assert report["validator_summary"]["valid_packets"] == 5
    assert report["validator_summary"]["ready_for_calibration"] == 5
    assert report["first_priority_packet"].endswith("external_template_bv_raman_vimshottari_boundary_series.json")

    packet = tmp_path / "external_template_bv_raman_vimshottari_boundary_series.json"
    manifest = tmp_path / "capture_manifest.json"
    next_steps = tmp_path / "OPERATOR_NEXT_STEPS.md"
    assert packet.exists()
    assert manifest.exists()
    assert next_steps.exists()

    packet_data = json.loads(packet.read_text(encoding="utf-8"))
    assert packet_data["status"] == "draft"
    assert packet_data["metadata"]["source_artifact"].startswith("references/oracle/artifacts/")
    boundaries = packet_data["target_placeholders"]["target.vimshottari_mahadasa_boundaries"]
    assert isinstance(boundaries, dict)
    assert boundaries["Mars"] == "1912-08-08"
    assert boundaries["Rahu"] == "1918-09-21"

    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_data["scope"] == "external_oracle_capture_packet_manifest"
    assert manifest_data["packet_count"] == 6
    assert packet.name in manifest_data["packets"]

    guide = next_steps.read_text(encoding="utf-8")
    assert "external_template_bv_raman_vimshottari_boundary_series.json" in guide
    assert "oracle_evidence_validator.py" in guide
    assert "--apply-packet" in guide
    assert "不得把本仓库本地输出当作 external oracle" in guide
