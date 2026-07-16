"""Experimental Rangacharya/Jaimini variant.

All outputs are blocked from adjudication until formula-level validation passes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping


SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

SOURCE_CARDS_PATH = Path(__file__).resolve().parent.parent / "references" / "rangacharya_source_cards.json"


class RangacharyaValidationError(RuntimeError):
    pass


def _source_cards() -> Dict[str, Dict[str, Any]]:
    try:
        data = json.loads(SOURCE_CARDS_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {str(card.get("id")): dict(card) for card in data.get("cards", []) if card.get("id")}


def _card_meta(card_id: str) -> Dict[str, Any]:
    card = _source_cards().get(card_id, {})
    status = str(card.get("status") or "blocked")
    meta = {
        "source_card_id": card_id,
        "source_card_status": status,
        "validation_status": status,
        "adjudication_enabled": False,
    }
    if status != "source_verified":
        meta["blocked_reason"] = card.get("blocked_reason") or "source card is not verified for adjudication"
    return meta


def _sign_name(index: int) -> str:
    return SIGNS[index % 12]


def _placeholder_pada(label: str, asc_sign_idx: int, source_house: int) -> Dict[str, Any]:
    sign_idx = (asc_sign_idx + source_house - 1) % 12
    return {
        "label": label,
        "sign": _sign_name(sign_idx),
        "sign_index": sign_idx,
        "source_house": source_house,
        "note": "Rangacharya formula pending source-card implementation",
        **_card_meta("rangacharya_core_arudha"),
    }


def calc_rangacharya_variant(asc_sign_idx: int, planet_longitudes: Mapping[str, float]) -> Dict[str, Any]:
    asc_sign_idx %= 12
    arudha_padas = {
        "AL": _placeholder_pada("AL", asc_sign_idx, 1),
        "A7": _placeholder_pada("A7", asc_sign_idx, 7),
        "A10": _placeholder_pada("A10", asc_sign_idx, 10),
        "UL": _placeholder_pada("UL", asc_sign_idx, 12),
    }
    return {
        "variant": "rangacharya",
        "status": "experimental_not_for_adjudication",
        "adjudication_enabled": False,
        "source_status": "transcribed",
        "active_lagna": {
            "sign": _sign_name(asc_sign_idx),
            **_card_meta("active_effective_lagna"),
        },
        "effective_lagna": {
            "sign": _sign_name(asc_sign_idx),
            **_card_meta("active_effective_lagna"),
        },
        "arudha_padas": arudha_padas,
        "input_planets_present": sorted(planet_longitudes),
    }


def _flatten(prefix: str, value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {prefix: value}
    rows: Dict[str, Any] = {}
    for key, child in value.items():
        child_key = f"{prefix}.{key}" if prefix else str(key)
        rows.update(_flatten(child_key, child))
    return rows


def diff_current_vs_rangacharya(current: Mapping[str, Any], variant: Mapping[str, Any]) -> Dict[str, Any]:
    current_flat = _flatten("", dict(current))
    variant_flat = _flatten("", dict(variant.get("arudha_padas", variant)))
    differences = []
    for key in sorted(set(current_flat) | set(variant_flat)):
        current_value = current_flat.get(key)
        variant_value = variant_flat.get(key)
        if current_value != variant_value:
            differences.append({"key": key, "current": current_value, "rangacharya": variant_value})
    return {
        "current_algorithm": "current_jaimini",
        "variant_algorithm": "rangacharya",
        "adjudication_enabled": False,
        "differences": differences,
    }


def validation_summary(result: Mapping[str, Any]) -> Dict[str, Any]:
    statuses = []
    for key, value in _flatten("", dict(result)).items():
        if key.endswith("validation_status"):
            statuses.append(str(value))
    blocking = sorted({status for status in statuses if status != "adjudication_enabled"})
    return {
        "adjudication_enabled": bool(result.get("adjudication_enabled")) and not blocking,
        "blocking_statuses": blocking,
    }


def assert_adjudication_allowed(result: Mapping[str, Any]) -> None:
    summary = validation_summary(result)
    if not summary["adjudication_enabled"]:
        raise RangacharyaValidationError(
            "Rangacharya variant is not adjudication-enabled; validation gates are incomplete"
        )
