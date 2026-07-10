#!/usr/bin/env python3
"""Cross-system Jyotish/Western arbitration contract tests."""

from __future__ import annotations

from scripts.cross_system_arbitrator import build_cross_system_arbitration


def test_cross_system_arbitrator_promotes_shared_timed_signal() -> None:
    packet = build_cross_system_arbitration(
        route_packet={"question_type": "career", "primary_theme": "career"},
        jyotish_evidence={
            "status": "complete",
            "signals": [
                {
                    "theme": "career_relocation",
                    "claim": "career_triggered_relocation",
                    "timing": "2026-08-24..2026-09-28",
                    "source": "Saturn/Ketu + Rahu 4H/10H axis",
                }
            ],
        },
        western_evidence={
            "status": "complete",
            "signals": [
                {
                    "theme": "career_relocation",
                    "claim": "career_triggered_relocation",
                    "timing": "2026-08-24..2026-09-28",
                    "source": "Uranus conjunct MC opposite IC",
                }
            ],
        },
    )

    assert packet["status"] == "used"
    assert packet["primary_theme"] == "career"
    assert packet["shared_signals"][0]["theme"] == "career_relocation"
    assert packet["shared_signals"][0]["claim"] == "career_triggered_relocation"
    assert packet["shared_signals"][0]["timing"] == "2026-08-24..2026-09-28"
    assert packet["shared_signals"][0]["confidence_effect"] == "raises_confidence"
    assert packet["conflicts"] == []


def test_cross_system_arbitrator_blocks_without_western_packet() -> None:
    packet = build_cross_system_arbitration(
        route_packet={"question_type": "career", "primary_theme": "career"},
        jyotish_evidence={"status": "partial", "signals": []},
        western_evidence=None,
    )

    assert packet["status"] == "blocked"
    assert packet["western_cross_validation"]["status"] == "blocked"
    assert "western_evidence_packet_missing" in packet["blocked_items"]


def test_cross_system_arbitrator_marks_conflicting_claims() -> None:
    packet = build_cross_system_arbitration(
        route_packet={"question_type": "career", "primary_theme": "career"},
        jyotish_evidence={
            "status": "complete",
            "signals": [{"theme": "career", "claim": "stable_internal_role", "timing": "2026-07"}],
        },
        western_evidence={
            "status": "complete",
            "signals": [{"theme": "career", "claim": "external_project_pivot", "timing": "2026-07"}],
        },
    )

    assert packet["status"] == "conflict"
    assert packet["conflicts"][0]["theme"] == "career"
    assert packet["conflicts"][0]["confidence_effect"] == "lowers_confidence"
