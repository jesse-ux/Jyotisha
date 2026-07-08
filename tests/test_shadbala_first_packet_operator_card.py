#!/usr/bin/env python3
"""Tests for the first Shadbala external absolute-value operator card."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "docs" / "benchmark" / "shadbala_synthetic_north_china_raman_first_packet_operator_card.md"
PACKET = ROOT / "references" / "oracle" / "evidence_packet_templates" / "shadbala_synthetic_north_china_raman_first_packet.json"


def test_shadbala_first_packet_operator_card_is_actionable() -> None:
    text = CARD.read_text(encoding="utf-8")

    assert "# First Shadbala Absolute-Value Oracle Packet Operator Card" in text
    assert "template_synthetic_north_china_shadbala_raman" in text
    assert "target.shadbala_components.Sun.sthana" in text
    assert "target.shadbala_components.Saturn.total_rupa" in text
    assert "target.moon_sidereal_longitude_deg" in text
    assert "reject_global_scaling" in text
    assert "Do not use a global multiplier" in text
    assert "--apply-packet" in text
    assert "oracle_evidence_validator.py" in text


def test_shadbala_first_packet_template_contains_complete_component_matrix() -> None:
    packet = json.loads(PACKET.read_text(encoding="utf-8"))

    assert packet["capture_id"] == "external_template_synthetic_north_china_shadbala_raman"
    assert packet["status"] == "draft"
    assert packet["case_id"] == "template_synthetic_north_china_shadbala_raman"
    assert packet["metadata"]["source_artifact"] == "references/oracle/artifacts/"
    assert packet["settings"]["ayanamsa"] == "raman"
    assert packet["target_placeholders"]["target.moon_sidereal_longitude_deg"] is None
    shadbala = packet["target_placeholders"]["target.shadbala_components"]
    assert set(shadbala) == {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    for row in shadbala.values():
        assert set(row) == {"sthana", "dig", "kala", "chesta", "naisargika", "drik", "total_rupa"}
        assert all(value is None for value in row.values())
    assert packet["operator_goal"] == "Fill one external Shadbala absolute-value component matrix."
    assert packet["integrity_checks"]["reject_global_scaling"] is True
