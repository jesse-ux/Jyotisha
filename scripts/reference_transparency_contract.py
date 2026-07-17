#!/usr/bin/env python3
"""User-visible disclosure for timing, engine observations, and public case references."""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from scripts.domain_calculation_service import compute_chart
    from scripts.timing_precision_contract import build_timing_precision_contract
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from domain_calculation_service import compute_chart
    from timing_precision_contract import build_timing_precision_contract


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "references" / "real_case_calibration" / "replay_manifest.json"
DOMAIN_HOUSES = {
    "career": "house_10",
    "marriage": "house_7",
    "wealth": "house_2",
    "health": "house_6",
}
FEATURE_WEIGHTS = {
    "ascendant": 0.35,
    "moon_sign": 0.30,
    "domain_lord_sign": 0.25,
    "node_axis": 0.10,
}
HIGH_SIMILARITY_THRESHOLD = 0.75


def _sign(chart: dict[str, Any], planet: str) -> str | None:
    planets = chart.get("planets") if isinstance(chart, dict) else None
    value = planets.get(planet) if isinstance(planets, dict) else None
    return value.get("sign") if isinstance(value, dict) else None


def _domain_lord_sign(chart: dict[str, Any], domain: str) -> str | None:
    house = DOMAIN_HOUSES.get(domain)
    houses = chart.get("houses") if isinstance(chart, dict) else None
    house_value = houses.get(house) if house and isinstance(houses, dict) else None
    lord = house_value.get("lord") if isinstance(house_value, dict) else None
    return _sign(chart, lord) if isinstance(lord, str) else None


def _features(chart: dict[str, Any], domain: str) -> dict[str, Any]:
    ascendant = chart.get("ascendant") if isinstance(chart, dict) else None
    return {
        "ascendant": ascendant.get("sign") if isinstance(ascendant, dict) else None,
        "moon_sign": _sign(chart, "Moon"),
        "domain_lord_sign": _domain_lord_sign(chart, domain),
        "node_axis": (_sign(chart, "Rahu"), _sign(chart, "Ketu")),
    }


@lru_cache(maxsize=64)
def _case_chart(case_id: str, year: int, month: int, day: int, hour: int, minute: int,
                lat: float, lon: float, tz: float, node_mode: str) -> dict[str, Any] | None:
    try:
        return compute_chart({
            "year": year, "month": month, "day": day, "hour": hour, "minute": minute,
            "lat": lat, "lon": lon, "tz": tz, "ayanamsa": "lahiri", "node_mode": node_mode,
        })
    except Exception:
        return None


def _chart_for_case(case: dict[str, Any]) -> dict[str, Any] | None:
    provided = case.get("chart")
    if isinstance(provided, dict):
        return provided
    subject = case.get("subject")
    if not isinstance(subject, dict):
        return None
    required = ("year", "month", "day", "hour", "minute", "lat", "lon", "tz")
    if any(subject.get(field) is None for field in required):
        return None
    return _case_chart(
        str(case.get("case_id", "")), int(subject["year"]), int(subject["month"]), int(subject["day"]),
        int(subject["hour"]), int(subject["minute"]), float(subject["lat"]), float(subject["lon"]),
        float(subject["tz"]), str(subject.get("node_mode", "mean")),
    )


def _similarity(user_chart: dict[str, Any], case_chart: dict[str, Any], domain: str) -> dict[str, Any]:
    user = _features(user_chart, domain)
    candidate = _features(case_chart, domain)
    matching, dissimilar, total = [], [], 0.0
    for name, weight in FEATURE_WEIGHTS.items():
        if user[name] is None or candidate[name] is None:
            continue
        total += weight
        if user[name] == candidate[name]:
            matching.append(name)
        else:
            dissimilar.append(name)
    score = round(sum(FEATURE_WEIGHTS[name] for name in matching) / total, 3) if total else 0.0
    return {
        "score": score,
        "matching_factors": matching,
        "dissimilar_factors": dissimilar,
        "feature_scope": "D1 ascendant, Moon, theme-house lord, and Rahu/Ketu axis only",
        "uncompared_layers": ["D9", "D10", "dasha_event_state", "transit_event_state"],
    }


def _load_cases(manifest_path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    cases = payload.get("cases") if isinstance(payload, dict) else None
    return [case for case in cases if isinstance(case, dict)] if isinstance(cases, list) else []


def select_similar_public_cases(
    user_chart: dict[str, Any],
    themes: list[str],
    *,
    cases: list[dict[str, Any]] | None = None,
    threshold: float = HIGH_SIMILARITY_THRESHOLD,
    max_cases: int = 3,
) -> dict[str, Any]:
    candidates = cases if cases is not None else _load_cases(DEFAULT_MANIFEST)
    selected: list[dict[str, Any]] = []
    for case in candidates:
        replay = case.get("replay")
        if not isinstance(replay, dict) or replay.get("outcome_replay_status") != "replayed":
            continue
        if replay.get("do_not_use_for_prediction") is True:
            continue
        case_chart = _chart_for_case(case)
        if not isinstance(case_chart, dict):
            continue
        for event in case.get("event_outcomes", []):
            if not isinstance(event, dict) or event.get("domain") not in themes:
                continue
            similarity = _similarity(user_chart, case_chart, event["domain"])
            if similarity["score"] < threshold:
                continue
            source = case.get("source") if isinstance(case.get("source"), dict) else {}
            event_source = event.get("source") if isinstance(event.get("source"), dict) else {}
            subject = case.get("subject") if isinstance(case.get("subject"), dict) else {}
            selected.append({
                "case_id": case.get("case_id"),
                "subject": subject.get("name"),
                "domain": event.get("domain"),
                "event_type": event.get("event_type"),
                "event_date": event.get("event_date"),
                "outcome": event.get("outcome"),
                "case_source": {"url": source.get("url"), "source_grade": source.get("source_grade")},
                "event_source": {"url": event_source.get("url"), "source_grade": event_source.get("source_grade")},
                "similarity": similarity,
                "reference_only": True,
                "difference_notice": "相似仅限列出的 D1 特征；未比较层不得推断为相同。",
            })
    selected.sort(key=lambda item: (-item["similarity"]["score"], item["case_id"] or ""))
    selected = selected[:max_cases]
    return {
        "status": "high_similarity_public_references_available" if selected else "no_high_similarity_public_reference",
        "cases": selected,
        "threshold": threshold,
        "manifest": "references/real_case_calibration/replay_manifest.json",
        "public_figures_only": True,
        "does_not_predict_user_outcome": True,
        "boundary": "公开案例用于比较与理解，不表示用户会复现该事件。",
    }


def build_reference_transparency_contract(
    chart: dict[str, Any], themes: list[str], *, timing: dict[str, Any] | None = None,
    cases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    timing_contract = build_timing_precision_contract(timing)
    return {
        "version": "transparent_reference_v1",
        "timing_display": {
            "claim_status": timing_contract["claim_status"],
            "verified_window": "display_with_evidence_scope",
            "candidate_windows": "display_with_signals_and_confidence_cap",
            "exact_triggers": "display_as_technical_trigger_not_guarantee",
            "boundary": timing_contract["boundary"],
        },
        "external_engine_observations": {
            "Local native": {"role": "primary_calculation", "source": "current request calculation contract"},
            "VedAstro hosted": {
                "role": "external_observation", "deployment_identity": "not_publicly_proven",
                "source": "references/oracle/vedastro_contract_arbitration_2026_07_17.json",
            },
            "Xalen": {"role": "formula_isolation_observation", "source": "references/oracle/xalen_fourth_oracle_comparison_2026_07_17.json"},
            "jyotishyamitra": {"role": "independent_observation", "source": "references/oracle/jyotishyamitra_steve_jobs_probe_2026_07_18.json"},
        },
        "method_variants": {
            "display": "show_parallel_methods_with_sources",
            "source": "references/oracle/xalen_formula_unit_attribution_2026_07_17.json",
            "boundary": "流派/公式差异并列展示；不以单一引擎多数投票决定真值。",
        },
        "similar_public_cases": select_similar_public_cases(chart, themes, cases=cases),
    }
