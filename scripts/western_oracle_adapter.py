#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Normalize external Western astrology oracle JSON into a western evidence packet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from western_evidence_packet import build_western_evidence_packet
except Exception:  # pragma: no cover - import path varies in tests/CLI
    from scripts.western_evidence_packet import build_western_evidence_packet


_ASPECT_ALIASES = {
    "conj": "conjunction",
    "conjunction": "conjunction",
    "trine": "trine",
    "sextile": "sextile",
    "square": "square",
    "opposition": "opposition",
    "opp": "opposition",
}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _aspect_label(item: dict[str, Any]) -> tuple[str, str, str]:
    planet = _norm(item.get("planet") or item.get("transit_planet"))
    aspect = _ASPECT_ALIASES.get(_norm(item.get("aspect")), _norm(item.get("aspect")))
    target = _norm(item.get("target") or item.get("point") or item.get("natal_point"))
    return planet, aspect, target


def _timing(item: dict[str, Any]) -> str:
    return str(item.get("timing") or item.get("date") or item.get("window") or "unspecified")


def _signals_from_aspects(aspects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for item in aspects:
        if not isinstance(item, dict):
            continue
        planet, aspect, target = _aspect_label(item)
        timing = _timing(item)
        source = str(item.get("source") or f"{planet} {aspect} {target}").replace("_", " ")
        if planet == "uranus" and aspect == "conjunction" and target in {"mc", "midheaven"}:
            signals.append(
                {
                    "theme": "career_relocation",
                    "claim": "career_triggered_relocation",
                    "timing": timing,
                    "source": source,
                }
            )
        if planet == "jupiter" and aspect in {"trine", "sextile"} and target in {"mercury", "venus", "mc", "midheaven"}:
            signals.append(
                {
                    "theme": "career",
                    "claim": "client_cooperation_opportunity",
                    "timing": timing,
                    "source": source,
                }
            )
        if planet == "saturn" and aspect == "conjunction" and target in {"sun", "mercury", "venus"}:
            signals.append(
                {
                    "theme": "career",
                    "claim": "career_responsibility_test",
                    "timing": timing,
                    "source": source,
                }
            )
    return signals


def build_packet_from_oracle_payload(
    payload: dict[str, Any],
    *,
    route_packet: dict[str, Any],
) -> dict[str, Any]:
    """Build a standard Western packet from an external-oracle JSON payload."""

    explicit_signals = payload.get("signals") if isinstance(payload.get("signals"), list) else []
    aspects = payload.get("aspects") if isinstance(payload.get("aspects"), list) else []
    signals = list(explicit_signals) or _signals_from_aspects(aspects)
    timing_techniques = payload.get("timing_techniques")
    if not isinstance(timing_techniques, dict):
        timing_techniques = {}
    if aspects and "aspects" not in timing_techniques:
        timing_techniques = {**timing_techniques, "aspects": aspects}
    packet = build_western_evidence_packet(
        route_packet=route_packet,
        natal=payload.get("natal") if isinstance(payload.get("natal"), dict) else {},
        timing_techniques=timing_techniques,
        signals=signals,
    )
    packet["source_engine"] = str(payload.get("source_engine") or payload.get("engine") or "external_western_oracle_json")
    packet["adapter_boundary"] = {
        "bundles_external_code": False,
        "accepted_input": "external_json_export",
        "role": "western_cross_validation_evidence",
    }
    return packet


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to external Western oracle JSON export.")
    parser.add_argument("--theme", default="general", help="Primary theme, e.g. career/marriage/wealth.")
    parser.add_argument("--question-type", default=None, help="Question type override.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(list(argv or sys.argv[1:]))
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    route_packet = {
        "question_type": args.question_type or args.theme,
        "primary_theme": args.theme,
    }
    packet = build_packet_from_oracle_payload(payload, route_packet=route_packet)
    print(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
