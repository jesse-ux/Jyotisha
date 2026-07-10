#!/usr/bin/env python3
"""Western evidence packet contract tests."""

from __future__ import annotations

from scripts.western_evidence_packet import build_western_evidence_packet


def test_western_evidence_packet_materializes_auditable_sections() -> None:
    packet = build_western_evidence_packet(
        route_packet={"question_type": "career", "primary_theme": "career"},
        natal={"ascendant": "Virgo", "mc": "Gemini"},
        timing_techniques={
            "transits": [{"aspect": "Uranus conjunct MC"}],
            "solar_return": {"annual_focus": "career"},
        },
        signals=[
            {
                "theme": "career_relocation",
                "claim": "career_triggered_relocation",
                "timing": "2026-08-24..2026-09-28",
                "source": "Uranus conjunct MC opposite IC",
            }
        ],
    )

    assert packet["system"] == "western_astrology"
    assert packet["status"] == "complete"
    assert packet["sections"]["natal"]["status"] == "used"
    assert packet["sections"]["timing_techniques"]["status"] == "used"
    assert packet["sections"]["signals"]["status"] == "used"
    assert packet["signals"][0]["claim"] == "career_triggered_relocation"


def test_western_evidence_packet_marks_missing_timing_as_partial() -> None:
    packet = build_western_evidence_packet(
        route_packet={"question_type": "career", "primary_theme": "career"},
        natal={"ascendant": "Virgo"},
        timing_techniques=None,
        signals=[],
    )

    assert packet["status"] == "partial"
    assert "timing_techniques" in packet["missing_sections"]
    assert "signals" in packet["missing_sections"]
