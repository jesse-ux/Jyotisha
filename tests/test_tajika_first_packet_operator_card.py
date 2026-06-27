#!/usr/bin/env python3
"""Tests for the first Tajika/Sahams annual oracle operator card."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "docs" / "benchmark" / "tajika_einstein_1905_first_packet_operator_card.md"
PACKET = ROOT / "references" / "oracle" / "artifacts" / "pending_packets" / "external_template_einstein_varshaphala_1905_lahiri.json"


def test_tajika_first_packet_operator_card_is_actionable() -> None:
    text = CARD.read_text(encoding="utf-8")

    assert "# First Tajika/Sahams Annual Oracle Packet Operator Card" in text
    assert "template_einstein_varshaphala_1905_lahiri" in text
    assert "target.solar_return_datetime" in text
    assert "target.sahams.punya_saham" in text
    assert "target.tajika_yogas" in text
    assert "solar-return convention" in text
    assert "--apply-packet" in text
    assert "tajika_annual_benchmark_dashboard.py" in text
    assert "target.year_lord" in text
    assert "target.mudda_dasha_first_lord" in text


def test_tajika_first_packet_template_contains_only_annual_targets() -> None:
    packet = json.loads(PACKET.read_text(encoding="utf-8"))

    assert packet["capture_id"] == "external_template_einstein_varshaphala_1905_lahiri"
    assert packet["status"] == "draft"
    assert packet["case_id"] == "template_einstein_varshaphala_1905_lahiri"
    assert packet["metadata"]["source_artifact"] == "references/oracle/artifacts/"
    assert packet["settings"]["target_year"] == 1905
    assert set(packet["target_placeholders"]) == {
        "target.solar_return_datetime",
        "target.varsha_lagna_deg",
        "target.muntha_sign",
        "target.year_lord",
        "target.mudda_dasha_first_lord",
        "target.sahams.punya_saham",
        "target.sahams.rajya_saham",
        "target.sahams.vivah_saham",
        "target.tajika_yogas",
        "target.source_artifact",
    }
    assert packet["integrity_checks"]["must_not_come_from_local_engine"] is True
