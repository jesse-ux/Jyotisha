#!/usr/bin/env python3
"""Tests for generating the unified first-packet oracle kit."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_generate_blank_oracle_writes_first_packet_kit(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/generate_blank_oracle.py",
            "--output-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "first_oracle_blank_kit"
    assert report["front_count"] == 3
    assert report["recommended_front_order"] == ["dasha", "tajika_sahams", "shadbala"]

    manifest = tmp_path / "blank_oracle_kit_manifest.json"
    checklist = tmp_path / "BLANK_ORACLE_KIT_NEXT_STEPS.md"
    assert manifest.exists()
    assert checklist.exists()

    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_data["scope"] == "first_oracle_blank_kit_manifest"
    assert manifest_data["front_count"] == 3
    assert manifest_data["fronts"]["dasha"]["missing_field_count"] == 0
    assert manifest_data["fronts"]["tajika_sahams"]["missing_field_count"] == 0
    assert manifest_data["fronts"]["shadbala"]["missing_field_count"] == 0

    dasha_packet = tmp_path / "dasha" / "external_template_steve_jobs_dasha_lahiri.json"
    tajika_packet = tmp_path / "tajika_sahams" / "external_template_einstein_varshaphala_1905_lahiri.json"
    shadbala_packet = tmp_path / "shadbala" / "external_template_synthetic_north_china_shadbala_raman.json"
    assert dasha_packet.exists()
    assert tajika_packet.exists()
    assert shadbala_packet.exists()

    dasha_data = json.loads(dasha_packet.read_text(encoding="utf-8"))
    assert dasha_data["status"] == "draft"
    assert dasha_data["target_placeholders"]["target.vimshottari_start_date"] is None

    guide = checklist.read_text(encoding="utf-8")
    assert "dasha" in guide
    assert "tajika_sahams" in guide
    assert "shadbala" in guide
    assert "不得把本仓库本地输出当作 external oracle" in guide
