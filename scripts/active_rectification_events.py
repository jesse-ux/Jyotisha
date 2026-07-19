# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
# ─── How to run ───
# .venv/bin/python -m pytest -q tests/test_active_rectification_events.py
"""Deterministically adjudicate dated events against birth-time candidates."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final, Literal, TypedDict, assert_never
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

ALGORITHM_VERSION: Final = "birth-time-event-scoring-v1"
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


def adjudicate_candidate_rows(
    rows: Sequence[CandidateScoreRow],
    *,
    event_count: int,
    domain_count: int,
    request_fingerprint: str,
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
    return {
        "result_id": str(uuid5(NAMESPACE_URL, f"{ALGORITHM_VERSION}:{request_fingerprint}")),
        "confidence": confidence,
        "can_apply": confidence == "high",
        "winning_segment": segment,
        "event_count": event_count,
        "domain_count": domain_count,
        "top_score": top_score,
        "second_score": second_score,
        "margin_percent": margin,
        "reasons": reasons,
        "evidence": evidence,
        "algorithm_version": ALGORITHM_VERSION,
    }


def score_life_events(request: RectificationEventRequest) -> CandidateResult:
    """Compute actual candidate rows, then apply the versioned confidence gates."""
    from scripts.active_rectification_event_engine import compute_event_candidate_result

    return compute_event_candidate_result(request)
