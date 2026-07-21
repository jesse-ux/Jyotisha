#!/usr/bin/env python3
"""Lossless categorical fact atoms for adjacent-minute rectification diagnostics.

This is a shadow-only feature contract.  It preserves the identities and
placements behind generic scoring rule names, but never changes candidate
scores or opens minute confirmation.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime
from typing import Any, Final

from scripts import active_rectification_event_engine as engine
from scripts.active_rectification_events import LifeEvent, RectificationEventRequest

FEATURE_CONTRACT_VERSION: Final = "minute-rectification-feature-facts-v4-shadow"


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _arudha_keys(domain: str) -> tuple[str, ...]:
    if domain == "relationship":
        return ("A7", "UL")
    if domain == "career":
        return ("A10",)
    return ()


def _candidate_facts(
    request: RectificationEventRequest,
    candidate_at: datetime,
) -> dict[str, Any]:
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
        planet_longitudes,
        ascendant_longitude,
        divisions=[2, 4, 9, 10, 24, 30],
    )
    d11 = engine._d11_chart(planet_longitudes, ascendant_longitude)
    arudha_result = engine.jaimini.calc_arudha_padas(ascendant_index, planet_longitudes)
    arudha = {
        **(arudha_result.get("padas") or {}),
        "UL": arudha_result.get("upapada") or {},
    }
    av = engine.ashtakavarga.calc_ashtakavarga(chart.get("planets", {}), ascendant_index)
    av_scores = av.get("house_scores_full") or {}
    event_facts: list[dict[str, Any]] = []
    missing_layers: set[str] = set()

    for event in request["events"]:
        prefixes, target_houses = engine.DOMAIN_CONFIG[event["domain"]]
        domain_vargas = [
            d11 if prefix == "D11" else engine._varga_chart(vargas, prefix)
            for prefix in prefixes
        ]
        if any(item is None for item in domain_vargas):
            missing_layers.update(prefixes)
            continue
        event_at = engine._event_datetime(event)
        try:
            vim = engine._active_vimshottari(
                candidate_at.date().isoformat(), planet_longitudes["Moon"], event_at,
            )
        except (KeyError, TypeError, ValueError):
            missing_layers.add("Vimshottari_MD_AD_PD")
            continue
        try:
            narayana = engine._active_narayana(
                ascendant_index, planet_longitudes, candidate_at, event_at,
            )
        except (KeyError, TypeError, ValueError):
            missing_layers.add("Narayana_MD_AD")
            continue
        if narayana[0] is None or narayana[1] is None:
            missing_layers.add("Narayana_MD_AD")
            continue

        active_lords = {"md": vim[0], "ad": vim[1], "pd": vim[2]}
        varga_facts = []
        for prefix, varga_chart in zip(prefixes, domain_vargas, strict=True):
            assert varga_chart is not None
            varga_facts.append({
                "chart": prefix,
                "ascendant_sign": (varga_chart.get("Ascendant") or {}).get("sign_idx"),
                "active_lord_houses": {
                    level: engine._varga_house(varga_chart, lord)
                    for level, lord in active_lords.items()
                },
            })
        relevant_arudha = {
            key: (arudha.get(key) or {}).get("sign_idx")
            for key in _arudha_keys(event["domain"])
        }
        shadbala_rules, _ = engine._shadbala_verified_components_auxiliary(
            chart,
            candidate_at.hour + candidate_at.minute / 60,
            vim,
        )
        event_facts.append({
            "event_id": event["id"],
            "domain": event["domain"],
            "vimshottari": active_lords,
            "narayana": {"md_sign": narayana[0], "ad_sign": narayana[1]},
            "d1": {
                "ascendant_sign": ascendant_index,
                "target_house_lords": sorted(engine._house_lords(ascendant_index, target_houses)),
                "active_lord_houses": {
                    level: engine._planet_house(chart, lord)
                    for level, lord in active_lords.items()
                },
            },
            "vargas": varga_facts,
            "arudha_signs": relevant_arudha,
            "ashtakavarga_target_house_scores": {
                str(house): (av_scores.get(f"house_{house}") or {}).get("sav_score")
                for house in target_houses
            },
            "verified_shadbala_state": sorted(shadbala_rules),
        })

    return {
        "time": candidate_at.strftime("%H:%M"),
        "feature_contract_version": FEATURE_CONTRACT_VERSION,
        "event_facts": event_facts,
        "missing_layers": sorted(missing_layers),
    }


def build_feature_fact_rows(
    request: RectificationEventRequest,
    *,
    candidates: Sequence[datetime] | None = None,
) -> list[dict[str, Any]]:
    candidate_datetimes = list(candidates) if candidates is not None else engine._candidate_datetimes(request)
    return [_candidate_facts(request, candidate) for candidate in candidate_datetimes]


def feature_fact_fingerprint(row: dict[str, Any]) -> str:
    """Hash facts only; candidate time and scorer output are deliberately excluded."""
    return _canonical_hash({
        "feature_contract_version": row["feature_contract_version"],
        "event_facts": row["event_facts"],
        "missing_layers": row["missing_layers"],
    })


def analyze_feature_fact_rows(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    candidates = list(rows)
    if not candidates:
        return {
            "scope": "minute_feature_fact_discriminability",
            "feature_contract_version": FEATURE_CONTRACT_VERSION,
            "candidate_count": 0,
            "unique_feature_fingerprint_count": 0,
            "indistinguishable_adjacent_pair_count": 0,
            "status": "blocked_no_candidates",
            "shadow_only": True,
        }
    fingerprints = {row["time"]: feature_fact_fingerprint(row) for row in candidates}
    classes: dict[str, list[str]] = defaultdict(list)
    for row in candidates:
        classes[fingerprints[row["time"]]].append(row["time"])
    transitions = []
    for previous, current in zip(candidates, candidates[1:]):
        previous_events = {item["event_id"]: item for item in previous["event_facts"]}
        current_events = {item["event_id"]: item for item in current["event_facts"]}
        changed = sorted(
            event_id
            for event_id in set(previous_events) | set(current_events)
            if previous_events.get(event_id) != current_events.get(event_id)
        )
        transitions.append({
            "between": [previous["time"], current["time"]],
            "feature_changed": fingerprints[previous["time"]] != fingerprints[current["time"]],
            "changed_event_ids": changed,
        })
    unique_count = len(classes)
    return {
        "scope": "minute_feature_fact_discriminability",
        "feature_contract_version": FEATURE_CONTRACT_VERSION,
        "candidate_count": len(candidates),
        "unique_feature_fingerprint_count": unique_count,
        "distinguishable_candidate_ratio": round(unique_count / len(candidates), 4),
        "equivalence_classes": [
            {"feature_fingerprint": fingerprint, "candidate_times": times, "size": len(times)}
            for fingerprint, times in sorted(classes.items(), key=lambda item: item[1][0])
        ],
        "adjacent_transitions": transitions,
        "indistinguishable_adjacent_pair_count": sum(
            not item["feature_changed"] for item in transitions
        ),
        "status": "facts_have_candidate_differences" if unique_count > 1 else "blocked_fact_equivalent_range",
        "shadow_only": True,
        "may_affect_candidate_score": False,
        "boundary": "Fact atoms may select a discriminating question, but cannot rank or confirm a minute without a separately frozen evidence rule.",
    }


def build_fact_difference_opportunities(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Partition candidates only where one event's actual fact atoms differ.

    The output deliberately contains no user-facing claim and no candidate
    scores.  It is an auditable input for a later question-planning layer.
    """
    candidates = list(rows)
    if not candidates:
        return []
    facts_by_event: dict[str, dict[str, tuple[str, dict[str, Any]]]] = defaultdict(dict)
    domains: dict[str, str] = {}
    for row in candidates:
        for fact in row["event_facts"]:
            event_id = fact["event_id"]
            domains[event_id] = fact["domain"]
            material = {
                key: value for key, value in fact.items()
                if key not in {"event_id", "domain"}
            }
            facts_by_event[event_id][row["time"]] = (_canonical_hash(material), material)
    opportunities = []
    for event_id, by_time in sorted(facts_by_event.items()):
        groups: dict[str, list[str]] = defaultdict(list)
        material_by_hash: dict[str, dict[str, Any]] = {}
        for candidate_time, (fingerprint, material) in by_time.items():
            groups[fingerprint].append(candidate_time)
            material_by_hash[fingerprint] = material
        if len(groups) < 2:
            continue
        probabilities = [len(times) / len(by_time) for times in groups.values()]
        information_gain = (
            -sum(value * math.log(value) for value in probabilities) / math.log(len(groups))
            if len(groups) > 1 else 0.0
        )
        ordered = sorted(groups.items(), key=lambda item: item[1][0])
        question_ready = 2 <= len(ordered) <= 4
        opportunities.append({
            "opportunity_id": _canonical_hash({
                "version": FEATURE_CONTRACT_VERSION,
                "event_id": event_id,
                "partitions": ordered,
            }),
            "event_id": event_id,
            "domain": domains[event_id],
            "estimated_information_gain": round(information_gain, 6),
            "partitions": [
                {
                    "fact_fingerprint": fingerprint,
                    "candidate_times": times,
                    "fact_atoms": material_by_hash[fingerprint],
                }
                for fingerprint, times in ordered
            ],
            "question_ready": question_ready,
            "requires_partition_coalescing": not question_ready,
            "shadow_only": True,
            "may_score_candidates": False,
        })
    return sorted(
        opportunities,
        key=lambda item: (-item["estimated_information_gain"], item["opportunity_id"]),
    )
