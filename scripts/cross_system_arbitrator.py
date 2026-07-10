#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cross-system Jyotish/Western evidence arbitration."""

from __future__ import annotations

from typing import Any


def _packet_status(packet: dict[str, Any] | None) -> str:
    if not isinstance(packet, dict) or not packet:
        return "blocked"
    return str(packet.get("status") or "partial")


def _signals(packet: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(packet, dict):
        return []
    raw = packet.get("signals")
    if not isinstance(raw, list):
        raw = packet.get("cross_system_signals")
    if not isinstance(raw, list):
        return []
    signals: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict) and item.get("theme") and item.get("claim"):
            signals.append(
                {
                    "theme": str(item.get("theme")),
                    "claim": str(item.get("claim")),
                    "timing": str(item.get("timing") or "unspecified"),
                    "source": str(item.get("source") or "unspecified"),
                }
            )
    return signals


def _audit_row(name: str, status: str, used: bool, effect: str) -> dict[str, Any]:
    return {
        "technique": name,
        "status": status,
        "used": used,
        "effect_on_confidence": effect,
    }


def build_cross_system_arbitration(
    *,
    route_packet: dict[str, Any],
    jyotish_evidence: dict[str, Any] | None,
    western_evidence: dict[str, Any] | None,
) -> dict[str, Any]:
    """Compare materialized Jyotish and Western evidence packets."""

    primary_theme = str(route_packet.get("primary_theme") or route_packet.get("question_type") or "general")
    jyotish_status = _packet_status(jyotish_evidence)
    western_status = _packet_status(western_evidence)
    blocked_items: list[str] = []
    if jyotish_status == "blocked":
        blocked_items.append("jyotish_evidence_packet_missing")
    if western_status == "blocked":
        blocked_items.append("western_evidence_packet_missing")

    jyotish_signals = _signals(jyotish_evidence)
    western_signals = _signals(western_evidence)
    shared: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []

    for jyotish_signal in jyotish_signals:
        for western_signal in western_signals:
            if jyotish_signal["theme"] != western_signal["theme"]:
                continue
            if jyotish_signal["claim"] == western_signal["claim"]:
                shared.append(
                    {
                        "theme": jyotish_signal["theme"],
                        "claim": jyotish_signal["claim"],
                        "timing": (
                            jyotish_signal["timing"]
                            if jyotish_signal["timing"] == western_signal["timing"]
                            else f"{jyotish_signal['timing']} | western:{western_signal['timing']}"
                        ),
                        "jyotish_source": jyotish_signal["source"],
                        "western_source": western_signal["source"],
                        "confidence_effect": "raises_confidence",
                    }
                )
            else:
                conflicts.append(
                    {
                        "theme": jyotish_signal["theme"],
                        "jyotish_claim": jyotish_signal["claim"],
                        "western_claim": western_signal["claim"],
                        "jyotish_timing": jyotish_signal["timing"],
                        "western_timing": western_signal["timing"],
                        "confidence_effect": "lowers_confidence",
                    }
                )

    if blocked_items:
        status = "blocked"
    elif conflicts and not shared:
        status = "conflict"
    elif shared:
        status = "used"
    else:
        status = "partial"

    return {
        "status": status,
        "primary_theme": primary_theme,
        "jyotish_cross_validation": {"status": jyotish_status, "signal_count": len(jyotish_signals)},
        "western_cross_validation": {"status": western_status, "signal_count": len(western_signals)},
        "shared_signals": shared,
        "conflicts": conflicts,
        "blocked_items": blocked_items,
        "technique_audit_rows": [
            _audit_row(
                "Western Cross-Validation",
                western_status,
                western_status in {"complete", "used"} or bool(western_signals),
                "western_oracle_available_for_trigger_refinement"
                if western_status != "blocked"
                else "blocked_until_western_evidence_packet_is_materialized",
            ),
            _audit_row(
                "Cross-System Arbitration",
                status,
                status == "used",
                "shared_signals_raise_confidence"
                if status == "used"
                else "confidence_capped_until_systems_share_a_theme_signal",
            ),
        ],
        "boundary": (
            "Arbitration compares materialized evidence only; it does not replace Jyotish adjudication or "
            "claim Western calculations were run when the western packet is missing."
        ),
    }
