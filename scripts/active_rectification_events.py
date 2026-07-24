# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
# ─── How to run ───
# .venv/bin/python -m pytest -q tests/test_active_rectification_events.py
"""Deterministically adjudicate dated events against birth-time candidates."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Final, Literal, NotRequired, TypedDict, assert_never
from uuid import NAMESPACE_URL, uuid5

EventPrecision = Literal["year", "month", "day"]
EventDomain = Literal[
    "education",
    "relocation",
    "relationship",
    "career",
    "finance",
    "health_pressure",
]
Confidence = Literal["low", "medium", "high"]

ALGORITHM_VERSION: Final = "birth-time-event-scoring-v2"
PRECISION_WEIGHTS: Final[dict[EventPrecision, float]] = {
    "day": 1.0,
    "month": 0.8,
    "year": 0.5,
}


class CandidateEvidence(TypedDict):
    event_id: str
    domain: str
    candidate_time: str
    rule_ids: list[str]
    points: float


class LifeEvent(TypedDict):
    id: str
    domain: EventDomain
    date: str
    precision: EventPrecision
    summary: NotRequired[str]


class RectificationEventRequest(TypedDict):
    birth_date: str
    start_time: str
    end_time: str
    lat: float
    lon: float
    tz: float
    events: list[LifeEvent]


class CandidateScoreRow(TypedDict):
    time: str
    score: float
    evidence: list[CandidateEvidence]
    missing_layers: list[str]


class WinningSegment(TypedDict):
    start_time: str
    end_time: str
    representative_time: str
    width_minutes: int


class CandidateResult(TypedDict):
    result_id: str
    confidence: Confidence
    can_apply: bool
    winning_segment: WinningSegment | None
    event_count: int
    domain_count: int
    top_score: float
    second_score: float
    margin_percent: float
    reasons: list[str]
    evidence: list[CandidateEvidence]
    algorithm_version: str
    canonical_input_hash: str
    calculation_contract: dict[str, Any]
    stability_diagnostics: dict[str, Any]
    missing_layers: list[str]
    candidate_ranking_summary: NotRequired[list[dict[str, Any]]]


def precision_weight(precision: EventPrecision) -> float:
    """Return the fixed evidence weight for a declared date precision."""
    match precision:
        case "day" | "month" | "year":
            return PRECISION_WEIGHTS[precision]
        case unreachable:
            assert_never(unreachable)


def _minute_value(value: str) -> int:
    hour, minute = value.split(":", maxsplit=1)
    return int(hour) * 60 + int(minute)


def _is_next_minute(previous: str, current: str) -> bool:
    return (_minute_value(current) - _minute_value(previous)) % (24 * 60) == 1


def _top_segments(rows: Sequence[CandidateScoreRow], top_score: float) -> list[list[CandidateScoreRow]]:
    segments: list[list[CandidateScoreRow]] = []
    for row in rows:
        if row["score"] != top_score:
            continue
        if segments and _is_next_minute(segments[-1][-1]["time"], row["time"]):
            segments[-1].append(row)
        else:
            segments.append([row])
    return segments


def _winning_segment(rows: Sequence[CandidateScoreRow]) -> WinningSegment:
    width = len(rows)
    representative = rows[(width - 1) // 2]["time"]
    return {
        "start_time": rows[0]["time"],
        "end_time": rows[-1]["time"],
        "representative_time": representative,
        "width_minutes": width,
    }


def _clock_distance(left: str, right: str) -> int:
    distance = abs(_minute_value(left) - _minute_value(right))
    return min(distance, 24 * 60 - distance)


def _time_at_offset(value: str, offset: int) -> str:
    total = (_minute_value(value) + offset) % (24 * 60)
    return f"{total // 60:02d}:{total % 60:02d}"


def build_stability_diagnostics(
    rows: Sequence[CandidateScoreRow],
    *,
    winning_segment: WinningSegment | None,
) -> dict[str, Any]:
    """Describe exact-minute neighbor separation without claiming calibrated accuracy."""
    representative = winning_segment["representative_time"] if winning_segment else None
    by_time = {row["time"]: row for row in rows}
    representative_row = by_time.get(representative) if representative else None
    neighborhoods: list[dict[str, Any]] = []
    for radius in (1, 2, 5):
        required_times = {
            _time_at_offset(representative, -radius),
            _time_at_offset(representative, radius),
        } if representative else set()
        neighbors = [
            row for row in rows
            if representative is not None
            and 0 < _clock_distance(row["time"], representative) <= radius
        ]
        if representative_row is None or not required_times.issubset(by_time):
            neighborhoods.append({
                "radius_minutes": radius,
                "status": "blocked",
                "lead_points": None,
                "compared_candidate_count": len(neighbors),
                "reason": "candidate_range_does_not_cover_both_sides_of_neighborhood",
            })
            continue
        best_neighbor = max(row["score"] for row in neighbors)
        lead = round(representative_row["score"] - best_neighbor, 4)
        neighborhoods.append({
            "radius_minutes": radius,
            "status": "pass" if winning_segment["width_minutes"] == 1 and lead > 0 else "fail",
            "lead_points": lead,
            "compared_candidate_count": len(neighbors),
            "reason": (
                "unique_minute_leads_neighbor_candidates"
                if winning_segment["width_minutes"] == 1 and lead > 0
                else "minute_not_uniquely_separated_from_neighbors"
            ),
        })
    return {
        "scope": "candidate_neighbor_stability",
        "representative_time": representative,
        "neighborhoods": neighborhoods,
        "all_required_passed": all(item["status"] == "pass" for item in neighborhoods),
        "boundary": "Neighbor separation is a diagnostic only until thresholds are frozen before public holdout replay.",
    }


def adjudicate_candidate_rows(
    rows: Sequence[CandidateScoreRow],
    *,
    event_count: int,
    domain_count: int,
    request_fingerprint: str,
    canonical_input_hash: str = "",
    calculation_contract: dict[str, Any] | None = None,
    leave_one_event_out: dict[str, Any] | None = None,
) -> CandidateResult:
    """Rank precomputed candidate rows and apply conservative confidence gates."""
    if not rows:
        return {
            "result_id": str(uuid5(NAMESPACE_URL, f"{ALGORITHM_VERSION}:{request_fingerprint}")),
            "confidence": "low",
            "can_apply": False,
            "winning_segment": None,
            "event_count": event_count,
            "domain_count": domain_count,
            "top_score": 0.0,
            "second_score": 0.0,
            "margin_percent": 0.0,
            "reasons": ["no_candidate_rows"],
            "evidence": [],
            "algorithm_version": ALGORITHM_VERSION,
            "canonical_input_hash": canonical_input_hash,
            "calculation_contract": calculation_contract or {},
            "stability_diagnostics": {
                "neighbor_stability": build_stability_diagnostics([], winning_segment=None),
                "leave_one_event_out": leave_one_event_out or {"status": "not_evaluated", "runs": []},
            },
            "missing_layers": [],
        }

    ranked_scores = sorted({row["score"] for row in rows}, reverse=True)
    top_score = ranked_scores[0]
    second_score = ranked_scores[1] if len(ranked_scores) > 1 else top_score
    margin = round((top_score - second_score) / max(abs(top_score), 1.0) * 100, 2)
    segments = _top_segments(rows, top_score)
    missing_layers = sorted({layer for row in rows for layer in row["missing_layers"]})
    reasons: list[str] = []

    if len(segments) != 1:
        reasons.append("tied_leader")
    if event_count < 3:
        reasons.append("insufficient_events")
    if domain_count < 2:
        reasons.append("insufficient_domains")
    if missing_layers:
        reasons.append("missing_mandatory_layers")

    segment = _winning_segment(segments[0]) if len(segments) == 1 else None
    if segment and segment["width_minutes"] > 15:
        reasons.append("winning_interval_too_wide")
    if margin < 10:
        reasons.append("lead_margin_below_medium_threshold")

    if reasons:
        confidence: Confidence = "low"
    elif (
        event_count >= 4
        and domain_count >= 3
        and segment is not None
        and segment["width_minutes"] <= 5
        and margin >= 20
    ):
        confidence = "high"
    else:
        confidence = "medium"

    top_rows = segments[0] if len(segments) == 1 else []
    representative_row = top_rows[(len(top_rows) - 1) // 2] if top_rows else None
    evidence = list(representative_row["evidence"]) if representative_row else []
    neighbor_stability = build_stability_diagnostics(rows, winning_segment=segment)
    if not neighbor_stability["all_required_passed"]:
        reasons.append("neighbor_stability_not_passed")
    if (leave_one_event_out or {}).get("status") != "pass":
        reasons.append("leave_one_event_out_not_passed")
    can_apply = (
        confidence == "high"
        and segment is not None
        and neighbor_stability["all_required_passed"]
        and (leave_one_event_out or {}).get("status") == "pass"
        and not missing_layers
        and not any(reason in reasons for reason in (
            "tied_leader",
            "insufficient_events",
            "insufficient_domains",
            "winning_interval_too_wide",
            "lead_margin_below_medium_threshold",
        ))
    )
    ranking_summary: list[dict[str, Any]] = []
    for score in ranked_scores[:3]:
        score_rows = sorted(
            (row for row in rows if row["score"] == score),
            key=lambda row: _minute_value(row["time"]),
        )
        if not score_rows:
            continue
        representative = score_rows[(len(score_rows) - 1) // 2]
        ranking_summary.append({
            "rank": len(ranking_summary) + 1,
            "time": representative["time"],
            "score": score,
            "tied_minute_count": len(score_rows),
        })
    return {
        "result_id": str(uuid5(NAMESPACE_URL, f"{ALGORITHM_VERSION}:{request_fingerprint}")),
        "confidence": confidence,
        "can_apply": can_apply,
        "winning_segment": segment,
        "event_count": event_count,
        "domain_count": domain_count,
        "top_score": top_score,
        "second_score": second_score,
        "margin_percent": margin,
        "reasons": reasons,
        "evidence": evidence,
        "algorithm_version": ALGORITHM_VERSION,
        "canonical_input_hash": canonical_input_hash,
        "calculation_contract": calculation_contract or {},
        "stability_diagnostics": {
            "neighbor_stability": neighbor_stability,
            "leave_one_event_out": leave_one_event_out or {"status": "not_evaluated", "runs": []},
        },
        "missing_layers": missing_layers,
        "candidate_ranking_summary": ranking_summary,
    }


def score_life_events(request: RectificationEventRequest) -> CandidateResult:
    """Compute actual candidate rows, then apply the versioned confidence gates."""
    from scripts.active_rectification_event_engine import compute_event_candidate_result

    return compute_event_candidate_result(request)
