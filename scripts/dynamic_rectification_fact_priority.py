#!/usr/bin/env python3
"""Shadow-only categorical birth-minute differences for question selection."""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from typing import Any, Final

from scripts import active_rectification_event_engine as engine
from scripts.dynamic_rectification_copy import SUPPORTED_DIMENSIONS
from scripts.minute_rectification_feature_facts_v4 import (
    build_fact_difference_opportunities,
    build_feature_fact_rows,
)

FACT_PRIORITY_VERSION: Final = "birth-time-question-fact-priority-v1"
EVENT_FACT_PRIORITY_VERSION: Final = "birth-time-question-event-fact-priority-v1"


def _fingerprint(value: Any) -> str:
    canonical = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _arudha_keys(domain: str) -> tuple[str, ...]:
    if domain == "relationship":
        return ("A7", "UL")
    if domain == "career":
        return ("A10",)
    return ()


def build_domain_fact_priorities(request: dict) -> dict[str, dict[str, Any]]:
    """Measure categorical D-varga/Arudha/AV differences without scoring them."""
    candidates = engine._candidate_datetimes(request)
    signatures: dict[str, list[tuple[str, str]]] = {
        domain: [] for domain in SUPPORTED_DIMENSIONS
    }
    for candidate_at in candidates:
        chart = engine.domain_calculation_service.compute_chart({
            "year": candidate_at.year,
            "month": candidate_at.month,
            "day": candidate_at.day,
            "hour": candidate_at.hour,
            "minute": candidate_at.minute,
            "lat": request["lat"],
            "lon": request["lon"],
            "tz": request["tz"],
            "ayanamsa": engine.AYANAMSA,
            "node_mode": engine.NODE_MODE,
        })
        planet_longitudes = {
            name: float(value["lon"])
            for name, value in chart.get("planets", {}).items()
            if isinstance(value, dict) and isinstance(value.get("lon"), int | float)
        }
        ascendant_longitude = float(chart["ascendant"]["lon"])
        ascendant_index = int(ascendant_longitude // 30)
        vargas = engine.varga.calc_all_vargas(
            planet_longitudes, ascendant_longitude, divisions=[2, 4, 9, 10, 24, 30],
        )
        d11 = engine._d11_chart(planet_longitudes, ascendant_longitude)
        arudha_result = engine.jaimini.calc_arudha_padas(ascendant_index, planet_longitudes)
        arudha = {
            **(arudha_result.get("padas") or {}),
            "UL": arudha_result.get("upapada") or {},
        }
        av = engine.ashtakavarga.calc_ashtakavarga(chart.get("planets", {}), ascendant_index)
        av_scores = av.get("house_scores_full") or {}
        for domain in SUPPORTED_DIMENSIONS:
            prefixes, target_houses = engine.DOMAIN_CONFIG[domain]
            domain_vargas = [
                d11 if prefix == "D11" else engine._varga_chart(vargas, prefix)
                for prefix in prefixes
            ]
            facts = {
                "varga_ascendant_signs": {
                    prefix: (item.get("Ascendant") or {}).get("sign_idx") if item else None
                    for prefix, item in zip(prefixes, domain_vargas, strict=True)
                },
                "arudha_signs": {
                    key: (arudha.get(key) or {}).get("sign_idx")
                    for key in _arudha_keys(domain)
                },
                "ashtakavarga_target_house_scores": {
                    str(house): (av_scores.get(f"house_{house}") or {}).get("sav_score")
                    for house in target_houses
                },
            }
            signatures[domain].append((candidate_at.strftime("%H:%M"), _fingerprint(facts)))

    result = {}
    for domain, rows in signatures.items():
        groups: dict[str, list[str]] = defaultdict(list)
        for candidate_time, fingerprint in rows:
            groups[fingerprint].append(candidate_time)
        probabilities = [len(times) / len(rows) for times in groups.values()] if rows else []
        entropy = (
            -sum(value * math.log(value) for value in probabilities) / math.log(len(groups))
            if len(groups) > 1 else 0.0
        )
        adjacent_changes = sum(
            previous[1] != current[1] for previous, current in zip(rows, rows[1:])
        )
        result[domain] = {
            "fact_priority_version": FACT_PRIORITY_VERSION,
            "selection_priority": round(entropy, 6),
            "unique_signature_count": len(groups),
            "adjacent_change_count": adjacent_changes,
            "shadow_only": True,
            "may_affect_candidate_score": False,
        }
    return result


def build_historical_event_priorities(request: dict) -> dict[str, dict[str, Any]]:
    """Rank domains by real event-specific Dasha and placement differences."""
    events = list(request.get("historical_events") or [])
    empty = {
        domain: {
            "event_fact_priority_version": EVENT_FACT_PRIORITY_VERSION,
            "selection_priority": 0.0,
            "discriminating_event_ids": [],
            "shadow_only": True,
            "may_affect_candidate_score": False,
        }
        for domain in SUPPORTED_DIMENSIONS
    }
    if not events:
        return empty
    event_request = {
        key: request[key]
        for key in ("birth_date", "start_time", "end_time", "lat", "lon", "tz")
    } | {"events": events}
    candidates = engine._candidate_datetimes(event_request)
    opportunities = build_fact_difference_opportunities(build_feature_fact_rows(
        event_request,
        candidates=candidates,
    ))
    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for opportunity in opportunities:
        if opportunity["domain"] in SUPPORTED_DIMENSIONS:
            by_domain[opportunity["domain"]].append(opportunity)
    return {
        domain: {
            "event_fact_priority_version": EVENT_FACT_PRIORITY_VERSION,
            "selection_priority": round(max(
                (item["estimated_information_gain"] for item in by_domain[domain]),
                default=0.0,
            ), 6),
            "discriminating_event_ids": sorted({
                item["event_id"] for item in by_domain[domain]
            }),
            "shadow_only": True,
            "may_affect_candidate_score": False,
        }
        for domain in SUPPORTED_DIMENSIONS
    }
