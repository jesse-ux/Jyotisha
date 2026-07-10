#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Western astrology evidence packet contract."""

from __future__ import annotations

from typing import Any


REQUIRED_SECTIONS = [
    "natal",
    "timing_techniques",
    "signals",
]


def _section(value: Any, source_path: str) -> dict[str, Any]:
    present = bool(value)
    return {
        "status": "used" if present else "missing",
        "source_path": source_path,
    }


def _normalize_signals(signals: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in signals or []:
        if not isinstance(item, dict) or not item.get("theme") or not item.get("claim"):
            continue
        normalized.append(
            {
                "theme": str(item.get("theme")),
                "claim": str(item.get("claim")),
                "timing": str(item.get("timing") or "unspecified"),
                "source": str(item.get("source") or "western_evidence_packet"),
            }
        )
    return normalized


def build_western_evidence_packet(
    *,
    route_packet: dict[str, Any],
    natal: dict[str, Any] | None,
    timing_techniques: dict[str, Any] | None,
    signals: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Materialize a small auditable Western evidence packet."""

    normalized_signals = _normalize_signals(signals)
    sections = {
        "natal": _section(natal, "western.natal"),
        "timing_techniques": _section(timing_techniques, "western.timing_techniques"),
        "signals": _section(normalized_signals, "western.signals"),
    }
    missing = [name for name in REQUIRED_SECTIONS if sections[name]["status"] == "missing"]
    return {
        "system": "western_astrology",
        "status": "complete" if not missing else "partial",
        "route": dict(route_packet),
        "required_sections": list(REQUIRED_SECTIONS),
        "sections": sections,
        "natal": natal or {},
        "timing_techniques": timing_techniques or {},
        "signals": normalized_signals,
        "missing_sections": missing,
        "license_boundary": (
            "This packet stores derived evidence only. Kerykeion, pyswisseph, Flatlib, Immanuel, or desktop "
            "software outputs must remain external oracle inputs unless their licenses permit bundling."
        ),
    }
