"""Readiness report for the experimental Rangacharya variant."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parent.parent
CARDS_PATH = ROOT / "references" / "rangacharya_source_cards.json"
MANIFEST_PATH = ROOT / "references" / "rangacharya_source_manifest.json"


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def build_report() -> Dict[str, Any]:
    cards_payload = _load_json(CARDS_PATH)
    manifest_payload = _load_json(MANIFEST_PATH)
    cards = {}
    blocked = []
    transcribed = []
    for card in cards_payload.get("cards", []):
        card_id = str(card.get("id") or "")
        if not card_id:
            continue
        status = str(card.get("status") or "blocked")
        adjudication_enabled = bool(card.get("adjudication_enabled"))
        cards[card_id] = {
            "status": status,
            "adjudication_enabled": adjudication_enabled,
            "blocked_reason": card.get("blocked_reason") or "",
        }
        if status == "blocked" or not adjudication_enabled:
            blocked.append(card_id)
        if status == "transcribed":
            transcribed.append(card_id)
    return {
        "scope": "rangacharya_readiness",
        "manifest_available": bool(manifest_payload),
        "source_cards_available": bool(cards_payload),
        "adjudication_enabled": bool(cards) and not blocked,
        "card_count": len(cards),
        "blocked_count": len(blocked),
        "transcribed_count": len(transcribed),
        "blocked_cards": blocked,
        "transcribed_cards": transcribed,
        "cards": cards,
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), ensure_ascii=False, indent=2, sort_keys=True))
