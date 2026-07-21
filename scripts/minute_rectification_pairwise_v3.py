#!/usr/bin/env python3
"""Domain-balanced, difference-only candidate ranking for rectification v3."""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Sequence
from typing import Any, Final
from uuid import NAMESPACE_URL, uuid5

from scripts.active_rectification_events import (
    CandidateScoreRow,
    LifeEvent,
    build_stability_diagnostics,
)
from scripts.minute_candidate_discriminability import analyze_candidate_rows

ALGORITHM_VERSION: Final = "birth-time-event-pairwise-v3"


def _percentile_ranks(values: dict[str, float]) -> dict[str, float]:
    """Map one event's candidate points to tie-aware [0, 1] ranks."""
    if not values:
        return {}
    unique = set(values.values())
    if len(unique) == 1:
        return {candidate: 0.0 for candidate in values}
    count = len(values)
    return {
        candidate: round(
            (
                sum(other < value for other in values.values())
                + 0.5 * (sum(other == value for other in values.values()) - 1)
            ) / (count - 1),
            6,
        )
        for candidate, value in values.items()
    }


def rank_candidate_rows(
    raw_rows: Sequence[CandidateScoreRow],
    events: Sequence[LifeEvent],
) -> tuple[list[CandidateScoreRow], dict[str, Any]]:
    """Rank within each event, average within domains, then weight domains equally."""
    rows = list(raw_rows)
    times = [row["time"] for row in rows]
    evidence_by_time = {
        row["time"]: {item["event_id"]: item for item in row["evidence"]}
        for row in rows
    }
    event_ranks: dict[str, dict[str, float]] = {}
    constant_events: list[str] = []
    for event in events:
        points = {
            candidate_time: float((evidence_by_time[candidate_time].get(event["id"]) or {}).get("points", 0.0))
            for candidate_time in times
        }
        ranks = _percentile_ranks(points)
        event_ranks[event["id"]] = ranks
        if len(set(points.values())) <= 1:
            constant_events.append(event["id"])

    event_ids_by_domain: dict[str, list[str]] = defaultdict(list)
    for event in events:
        event_ids_by_domain[event["domain"]].append(event["id"])
    candidate_domain_scores: dict[str, dict[str, float]] = {}
    ranked_rows: list[CandidateScoreRow] = []
    for row in rows:
        domain_scores = {
            domain: round(
                sum(event_ranks[event_id][row["time"]] for event_id in event_ids) / len(event_ids),
                6,
            )
            for domain, event_ids in event_ids_by_domain.items()
        }
        candidate_domain_scores[row["time"]] = domain_scores
        overall = sum(domain_scores.values()) / len(domain_scores) if domain_scores else 0.0
        ranked_rows.append({
            **row,
            "score": round(overall * 100, 6),
        })
    return ranked_rows, {
        "schema_version": "minute-pairwise-domain-balanced-v1",
        "algorithm_version": ALGORITHM_VERSION,
        "event_count": len(events),
        "domain_count": len(event_ids_by_domain),
        "constant_event_ids": sorted(constant_events),
        "discriminating_event_ids": sorted(set(event_ranks) - set(constant_events)),
        "event_percentile_ranks": event_ranks,
        "candidate_domain_scores": candidate_domain_scores,
        "aggregation": "tie_aware_event_percentile_then_domain_mean_then_equal_domain_mean",
        "boundary": "Common support shared by every candidate contributes zero and repeated events cannot increase a domain's weight.",
    }


def _winning_segment(rows: Sequence[CandidateScoreRow]) -> dict[str, Any] | None:
    if not rows:
        return None
    top = max(row["score"] for row in rows)
    leaders = [row for row in rows if row["score"] == top]
    if not leaders:
        return None
    segments: list[list[CandidateScoreRow]] = []
    for row in leaders:
        if segments:
            previous = segments[-1][-1]["time"]
            previous_minute = int(previous[:2]) * 60 + int(previous[3:])
            current_minute = int(row["time"][:2]) * 60 + int(row["time"][3:])
            if (current_minute - previous_minute) % 1440 == 1:
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


def _leave_one_event_out(raw_rows: list[CandidateScoreRow], events: list[LifeEvent]) -> dict[str, Any]:
    full_rows, _ = rank_candidate_rows(raw_rows, events)
    full_segment = _winning_segment(full_rows)
    full_leader = full_segment["representative_time"] if full_segment and full_segment["width_minutes"] == 1 else None
    runs = []
    stable = full_leader is not None
    for event in events:
        remaining = [item for item in events if item["id"] != event["id"]]
        rescored, _ = rank_candidate_rows(raw_rows, remaining)
        segment = _winning_segment(rescored)
        retained = bool(
            full_leader
            and segment
            and segment["width_minutes"] == 1
            and segment["representative_time"] == full_leader
        )
        stable = stable and retained
        runs.append({
            "removed_event_id": event["id"],
            "winning_segment": segment,
            "original_unique_leader_retained": retained,
        })
    return {
        "status": "pass" if stable else "fail",
        "runs": runs,
        "boundary": "Every event deletion must retain the same unique leading minute after ranks and domain means are recomputed.",
    }


def score_pairwise_v3(raw_rows: Sequence[CandidateScoreRow], events: Sequence[LifeEvent]) -> dict[str, Any]:
    """Produce a guarded v3 candidate result without opening minute confirmation."""
    raw = list(raw_rows)
    event_list = list(events)
    rows, contract = rank_candidate_rows(raw, event_list)
    segment = _winning_segment(rows)
    unique_scores = sorted({row["score"] for row in rows}, reverse=True)
    top_score = unique_scores[0] if unique_scores else 0.0
    second_score = unique_scores[1] if len(unique_scores) > 1 else top_score
    margin = round((top_score - second_score) / max(abs(top_score), 1.0) * 100, 2)
    missing = sorted({layer for row in raw for layer in row["missing_layers"]})
    neighbor = build_stability_diagnostics(rows, winning_segment=segment)
    leave_one_out = _leave_one_event_out(raw, event_list)
    discriminability = analyze_candidate_rows(raw, ranking_rows=rows)
    domains = {event["domain"] for event in event_list}
    reasons: list[str] = []
    if segment is None:
        reasons.append("tied_or_disconnected_leader")
    elif segment["width_minutes"] != 1:
        reasons.append("leading_range_not_unique_minute")
    if len(event_list) < 3:
        reasons.append("insufficient_events")
    if len(domains) < 2:
        reasons.append("insufficient_domains")
    if missing:
        reasons.append("missing_mandatory_layers")
    if not neighbor["all_required_passed"]:
        reasons.append("neighbor_stability_not_passed")
    if leave_one_out["status"] != "pass":
        reasons.append("leave_one_event_out_not_passed")
    if not discriminability["top_candidate_feature_unique"]:
        reasons.append("top_candidate_feature_not_unique")
    high = (
        len(event_list) >= 4
        and len(domains) >= 3
        and not reasons
    )
    medium = (
        len(event_list) >= 3
        and len(domains) >= 2
        and segment is not None
        and segment["width_minutes"] <= 15
        and not missing
    )
    confidence = "high" if high else "medium" if medium else "low"
    reasons.append("pairwise_v3_holdout_not_ready")
    fingerprint = hashlib.sha256(json.dumps(
        {"rows": rows, "events": event_list, "version": ALGORITHM_VERSION},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()).hexdigest()
    return {
        "result_id": str(uuid5(NAMESPACE_URL, f"{ALGORITHM_VERSION}:{fingerprint}")),
        "confidence": confidence,
        "can_apply": False,
        "winning_segment": segment,
        "event_count": len(event_list),
        "domain_count": len(domains),
        "top_score": top_score,
        "second_score": second_score,
        "margin_percent": margin,
        "reasons": reasons,
        "algorithm_version": ALGORITHM_VERSION,
        "missing_layers": missing,
        "pairwise_contract": contract,
        "stability_diagnostics": {
            "neighbor_stability": neighbor,
            "leave_one_event_out": leave_one_out,
            "candidate_discriminability": discriminability,
        },
    }
