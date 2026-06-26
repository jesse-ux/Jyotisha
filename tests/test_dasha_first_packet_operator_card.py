#!/usr/bin/env python3
"""Tests for the first Dasha-only external oracle operator card."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "docs" / "benchmark" / "dasha_steve_jobs_first_packet_operator_card.md"
PACKET = ROOT / "references" / "oracle" / "evidence_packet_templates" / "dasha_steve_jobs_lahiri_first_packet_only.json"


def test_dasha_first_packet_operator_card_is_short_and_actionable() -> None:
    text = CARD.read_text(encoding="utf-8")

    assert "# First Dasha Oracle Packet Operator Card" in text
    assert "template_steve_jobs_dasha_lahiri" in text
    assert "target.vimshottari_start_date" in text
    assert "Shadbala" in text
    assert "do not fill" in text
    assert "--apply-packet" in text
    assert "oracle_evidence_validator.py" in text


def test_dasha_only_packet_template_excludes_shadbala_matrix() -> None:
    packet = json.loads(PACKET.read_text(encoding="utf-8"))

    assert packet["capture_id"] == "external_template_steve_jobs_dasha_lahiri"
    assert packet["status"] == "draft"
    assert packet["case_id"] == "template_steve_jobs_dasha_lahiri"
    assert packet["metadata"]["source_artifact"] == "references/oracle/artifacts/"
    assert packet["target_placeholders"] == {"target.vimshottari_start_date": None}
    assert "target.shadbala_components" not in packet["target_placeholders"]
    assert packet["integrity_checks"]["must_not_come_from_local_engine"] is True
    assert packet["operator_goal"] == "Fill one external Vimshottari start date only."
