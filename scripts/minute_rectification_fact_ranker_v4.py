#!/usr/bin/env python3
"""Event-specific fact ranker for minute rectification development.

The ranker consumes the lossless v4 fact contract.  It is deliberately shadow
only: it can be evaluated and frozen, but it cannot apply a birth minute until
an independent public-AA holdout passes the release gates.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final
from uuid import NAMESPACE_URL, uuid5

from scripts.active_rectification_event_engine import DOMAIN_CONFIG
from scripts.active_rectification_events import (
    CandidateScoreRow,
    LifeEvent,
    build_stability_diagnostics,
    precision_weight,
)
from scripts.minute_candidate_discriminability import analyze_candidate_rows

ALGORITHM_VERSION: Final = "birth-time-event-fact-ranker-v4-shadow"
LAYER_FAMILIES: Final = (
    "vimshottari_d1",
    "varga",
    "narayana",
    "arudha",
    "ashtakavarga",
    "shadbala",
)
VIM_WEIGHTS: Final = {"md": 2.0, "ad": 1.5, "pd": 0.75}
LAYER_WEIGHTS: Final = {
    "vimshottari_d1": 0.20,
    "varga": 0.30,
    "narayana": 0.25,
    "arudha": 0.10,
    "ashtakavarga": 0.075,
    "shadbala": 0.075,
}


def _relative_house(sign_index: int, ascendant_index: int) -> int:
    return (sign_index - ascendant_index) % 12 + 1


def _event_layer_points(fact: Mapping[str, Any]) -> dict[str, float]:
    domain = str(fact["domain"])
    target_houses = set(DOMAIN_CONFIG[domain][1])
    d1 = fact["d1"]
    active_lords = fact["vimshottari"]
    target_lords = set(d1["target_house_lords"])

    vimshottari_d1 = 0.0
    for level, weight in VIM_WEIGHTS.items():
        lord = active_lords[level]
        if d1["active_lord_houses"].get(level) in target_houses:
            vimshottari_d1 += weight
        if lord in target_lords:
            vimshottari_d1 += weight

    vargas = list(fact["vargas"])
    varga_points = 0.0
    if vargas:
        for level, weight in VIM_WEIGHTS.items():
            matches = sum(
                chart["active_lord_houses"].get(level) in target_houses
                for chart in vargas
            )
            varga_points += weight * matches / len(vargas)

    ascendant = int(d1["ascendant_sign"])
    narayana = fact["narayana"]
    narayana_points = 0.0
    for key, weight in (("md_sign", 2.0), ("ad_sign", 1.0)):
        sign = narayana.get(key)
        if isinstance(sign, int) and _relative_house(sign, ascendant) in target_houses:
            narayana_points += weight

    arudha_signs = {
        value for value in fact["arudha_signs"].values() if isinstance(value, int)
    }
    arudha_points = 0.0
    if arudha_signs:
        if narayana.get("md_sign") in arudha_signs:
            arudha_points += 1.5
        if narayana.get("ad_sign") in arudha_signs:
            arudha_points += 0.75

    av_values = [
        float(value)
        for value in fact["ashtakavarga_target_house_scores"].values()
        if isinstance(value, int | float)
    ]
    av_points = sum(av_values) / len(av_values) / 40 if av_values else 0.0

    shadbala_points = 0.0
    shadbala_states = set(fact["verified_shadbala_state"])
    if "shadbala_sthana_drik_naisargika_support_auxiliary" in shadbala_states:
        shadbala_points = 0.25
    elif "shadbala_sthana_drik_naisargika_pressure_auxiliary" in shadbala_states:
        shadbala_points = -0.125

    return {
        "vimshottari_d1": vimshottari_d1,
        "varga": varga_points,
        "narayana": narayana_points,
        "arudha": arudha_points,
        "ashtakavarga": av_points,
        "shadbala": shadbala_points,
    }


def _percentile_ranks(values: Mapping[str, float]) -> dict[str, float]:
    if not values or len(set(values.values())) == 1:
        return {candidate: 0.0 for candidate in values}
    count = len(values)
    return {
        candidate: round((
            sum(other < value for other in values.values())
            + 0.5 * (sum(other == value for other in values.values()) - 1)
        ) / (count - 1), 6)
        for candidate, value in values.items()
    }


def rank_fact_rows(
    fact_rows: Sequence[dict[str, Any]],
    events: Sequence[LifeEvent],
    *,
    excluded_layers: Iterable[str] = (),
) -> tuple[list[CandidateScoreRow], dict[str, Any]]:
    rows = list(fact_rows)
    event_list = list(events)
    excluded = set(excluded_layers)
    unknown = excluded - set(LAYER_FAMILIES)
    if unknown:
        raise ValueError(f"unsupported fact layer: {sorted(unknown)[0]}")
    times = [row["time"] for row in rows]
    by_time = {
        row["time"]: {fact["event_id"]: fact for fact in row["event_facts"]}
        for row in rows
    }
    raw_event_scores: dict[str, dict[str, float]] = {}
    event_layer_ranks: dict[str, dict[str, dict[str, float]]] = {}
    event_layer_points: dict[str, dict[str, dict[str, float]]] = {}
    for event in event_list:
        event_id = event["id"]
        event_layer_points[event_id] = {}
        for candidate_time in times:
            fact = by_time[candidate_time].get(event_id)
            layers = _event_layer_points(fact) if fact else {key: 0.0 for key in LAYER_FAMILIES}
            event_layer_points[event_id][candidate_time] = layers
        event_layer_ranks[event_id] = {
            layer: _percentile_ranks({
                candidate_time: event_layer_points[event_id][candidate_time][layer]
                for candidate_time in times
            })
            for layer in LAYER_FAMILIES if layer not in excluded
        }
        active_weight = sum(
            weight for layer, weight in LAYER_WEIGHTS.items()
            if layer not in excluded
            and any(event_layer_ranks[event_id][layer].values())
        )
        raw_event_scores[event_id] = {
            candidate_time: round(
                sum(
                    LAYER_WEIGHTS[layer] * ranks[candidate_time]
                    for layer, ranks in event_layer_ranks[event_id].items()
                ) / active_weight if active_weight else 0.0,
                6,
            )
            for candidate_time in times
        }
    event_ranks = raw_event_scores
    event_ids_by_domain: dict[str, list[str]] = defaultdict(list)
    for event in event_list:
        event_ids_by_domain[event["domain"]].append(event["id"])

    ranked: list[CandidateScoreRow] = []
    domain_scores_by_time: dict[str, dict[str, float]] = {}
    for candidate_time in times:
        domain_scores = {
            domain: round(
                sum(
                    event_ranks[event_id][candidate_time]
                    * precision_weight(next(
                        event["precision"] for event in event_list if event["id"] == event_id
                    ))
                    for event_id in event_ids
                ) / sum(
                    precision_weight(next(
                        event["precision"] for event in event_list if event["id"] == event_id
                    ))
                    for event_id in event_ids
                ),
                6,
            )
            for domain, event_ids in event_ids_by_domain.items()
        }
        domain_scores_by_time[candidate_time] = domain_scores
        overall = sum(domain_scores.values()) / len(domain_scores) if domain_scores else 0.0
        evidence = [{
            "event_id": event["id"],
            "domain": event["domain"],
            "candidate_time": candidate_time,
            "rule_ids": [
                f"fact_v4_{layer}"
                for layer, points in event_layer_points[event["id"]][candidate_time].items()
                if layer not in excluded and points != 0
            ] or ["fact_v4_no_candidate_relative_support"],
            "points": event_ranks[event["id"]][candidate_time],
        } for event in event_list]
        ranked.append({
            "time": candidate_time,
            "score": round(overall * 100, 6),
            "evidence": evidence,
            "missing_layers": list(next(
                (row["missing_layers"] for row in rows if row["time"] == candidate_time),
                [],
            )),
        })
    return ranked, {
        "schema_version": "minute-event-fact-ranker-v4",
        "algorithm_version": ALGORITHM_VERSION,
        "excluded_layers": sorted(excluded),
        "event_raw_scores": raw_event_scores,
        "event_layer_ranks": event_layer_ranks,
        "layer_weights": LAYER_WEIGHTS,
        "event_percentile_ranks": event_ranks,
        "candidate_domain_scores": domain_scores_by_time,
        "aggregation": "fixed_fact_rules_then_tie_aware_event_percentile_then_equal_domain_mean",
        "shadow_only": True,
    }


def _winning_segment(rows: Sequence[CandidateScoreRow]) -> dict[str, Any] | None:
    if not rows:
        return None
    top = max(row["score"] for row in rows)
    leaders = [row for row in rows if row["score"] == top]
    segments: list[list[CandidateScoreRow]] = []
    for row in leaders:
        if segments:
            previous = segments[-1][-1]["time"]
            previous_minute = int(previous[:2]) * 60 + int(previous[3:])
            current_minute = int(row["time"][:2]) * 60 + int(row["time"][3:])
            if (current_minute - previous_minute) % 1_440 == 1:
                segments[-1].append(row)
                continue
        segments.append([row])
    if len(segments) != 1:
        return None
    winner = segments[0]
    return {
        "start_time": winner[0]["time"],
        "end_time": winner[-1]["time"],
        "representative_time": winner[(len(winner) - 1) // 2]["time"],
        "width_minutes": len(winner),
    }


def _leave_one_event_out(
    fact_rows: Sequence[dict[str, Any]], events: Sequence[LifeEvent], full_leader: str | None,
) -> dict[str, Any]:
    runs = []
    passed = full_leader is not None and len(events) >= 2
    for removed in events:
        remaining = [event for event in events if event["id"] != removed["id"]]
        rescored, _ = rank_fact_rows(fact_rows, remaining)
        segment = _winning_segment(rescored)
        retained = bool(
            full_leader and segment and segment["width_minutes"] == 1
            and segment["representative_time"] == full_leader
        )
        passed = passed and retained
        runs.append({
            "removed_event_id": removed["id"],
            "winning_segment": segment,
            "original_unique_leader_retained": retained,
        })
    return {"status": "pass" if passed else "fail", "runs": runs}


def _ablation_report(
    fact_rows: Sequence[dict[str, Any]], events: Sequence[LifeEvent], full_leader: str | None,
) -> dict[str, Any]:
    runs = []
    for layer in LAYER_FAMILIES:
        rescored, _ = rank_fact_rows(fact_rows, events, excluded_layers={layer})
        segment = _winning_segment(rescored)
        runs.append({
            "removed_layer": layer,
            "winning_segment": segment,
            "full_unique_leader_retained": bool(
                full_leader and segment and segment["width_minutes"] == 1
                and segment["representative_time"] == full_leader
            ),
        })
    return {"scope": "fact_layer_ablation", "runs": runs}


def score_fact_ranker_v4(
    fact_rows: Sequence[dict[str, Any]], events: Sequence[LifeEvent],
) -> dict[str, Any]:
    rows, contract = rank_fact_rows(fact_rows, events)
    segment = _winning_segment(rows)
    full_leader = (
        segment["representative_time"]
        if segment and segment["width_minutes"] == 1 else None
    )
    neighbor = build_stability_diagnostics(rows, winning_segment=segment)
    leave_one_out = _leave_one_event_out(fact_rows, events, full_leader)
    ablation = _ablation_report(fact_rows, events, full_leader)
    discriminability = analyze_candidate_rows(rows, ranking_rows=rows)
    scores = sorted({row["score"] for row in rows}, reverse=True)
    top = scores[0] if scores else 0.0
    second = scores[1] if len(scores) > 1 else top
    domains = {event["domain"] for event in events}
    missing = sorted({layer for row in rows for layer in row["missing_layers"]})
    reasons = []
    if not full_leader:
        reasons.append("unique_minute_not_found")
    if len(events) < 4:
        reasons.append("insufficient_events")
    if len(domains) < 3:
        reasons.append("insufficient_domains")
    if missing:
        reasons.append("missing_mandatory_layers")
    if not neighbor["all_required_passed"]:
        reasons.append("neighbor_stability_not_passed")
    if leave_one_out["status"] != "pass":
        reasons.append("leave_one_event_out_not_passed")
    if not discriminability["top_candidate_feature_unique"]:
        reasons.append("top_candidate_feature_not_unique")
    reasons.append("fact_ranker_v4_holdout_not_ready")
    fingerprint = hashlib.sha256(json.dumps(
        {"rows": rows, "events": list(events), "version": ALGORITHM_VERSION},
        ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()
    return {
        "result_id": str(uuid5(NAMESPACE_URL, f"{ALGORITHM_VERSION}:{fingerprint}")),
        "confidence": "high" if len(reasons) == 1 else "low",
        "can_apply": False,
        "winning_segment": segment,
        "event_count": len(events),
        "domain_count": len(domains),
        "top_score": top,
        "second_score": second,
        "margin_percent": round((top - second) / max(abs(top), 1.0) * 100, 2),
        "reasons": reasons,
        "algorithm_version": ALGORITHM_VERSION,
        "missing_layers": missing,
        "fact_ranking_contract": contract,
        "stability_diagnostics": {
            "neighbor_stability": neighbor,
            "leave_one_event_out": leave_one_out,
            "candidate_discriminability": discriminability,
            "ablation": ablation,
        },
        "shadow_only": True,
    }
