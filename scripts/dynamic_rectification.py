# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
# ─── How to run ───
# .venv/bin/python -m pytest -q tests/test_dynamic_rectification_scoring.py
"""Public dynamic-rectification packet and deterministic scoring entrypoints."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, TypedDict
from uuid import NAMESPACE_URL, uuid5

from scripts.dynamic_rectification_opportunities import (
    ALGORITHM_VERSION,
    OPPORTUNITY_MODEL_VERSION,
    SUPPORTED_DIMENSIONS,
    candidate_times,
    candidate_window_rows,
    canonical_hash,
    compute_candidate_model,
    experience_windows,
    historical_event_fingerprint,
    opportunities,
    validate_candidate_model,
)

Confidence = Literal["low", "medium", "high"]
_candidate_times = candidate_times
_candidate_window_rows = candidate_window_rows
_canonical_hash = canonical_hash
_experience_windows = experience_windows
_opportunities = opportunities
_validate_candidate_model = validate_candidate_model


class ChoiceRow(TypedDict):
    time: str
    score: float


class WinningSegment(TypedDict):
    start_time: str
    end_time: str
    representative_time: str
    width_minutes: int


def _compute_candidate_model(request: dict) -> dict:
    return compute_candidate_model(request, _candidate_window_rows)


def build_difference_packet(request: dict) -> dict:
    """Build reusable candidate activations and unused high-gain opportunities."""
    candidates = _candidate_times(
        request["birth_date"], request["start_time"], request["end_time"]
    )
    _validated_choice_evidence(request.get("evidence"), candidates)
    persisted = request.get("candidate_model")
    model = (
        _compute_candidate_model(request)
        if persisted is None
        or persisted.get("opportunity_model_version") != OPPORTUNITY_MODEL_VERSION
        or persisted.get("historical_event_fingerprint") != historical_event_fingerprint(request)
        else _validate_candidate_model(persisted, request)
    )
    dismissed = set(request.get("dismissed_opportunity_ids", []))
    fingerprints = set(request.get("partition_fingerprints", []))
    unused = [
        item for item in _opportunities(model)
        if item["opportunity_id"] not in dismissed
        and item["candidate_partition_fingerprint"] not in fingerprints
    ]
    return {
        "case_id": request["case_id"],
        "scoring_version": ALGORITHM_VERSION,
        "current_range": {
            "start_time": request["start_time"], "end_time": request["end_time"]
        },
        "opportunities": unused,
        "asked_question_fingerprints": list(request.get("question_fingerprints", [])),
        "candidate_partition_fingerprints": list(request.get("partition_fingerprints", [])),
        "recent_range_history": list(request.get("recent_ranges", [])),
        "candidate_model": model,
    }


def _minute_value(value: str) -> int:
    hour, minute = value.split(":", maxsplit=1)
    return int(hour) * 60 + int(minute)


def _winning_segments(rows: Sequence[ChoiceRow], top_score: float) -> list[list[ChoiceRow]]:
    segments: list[list[ChoiceRow]] = []
    for row in rows:
        if row["score"] != top_score:
            continue
        follows = bool(segments) and (
            _minute_value(row["time"]) - _minute_value(segments[-1][-1]["time"])
        ) % 1_440 == 1
        if follows:
            segments[-1].append(row)
        else:
            segments.append([row])
    return segments


def adjudicate_choice_rows(
    rows: Sequence[ChoiceRow], *, effective_answer_count: int, dimension_count: int,
    missing_layers: Sequence[str], request_fingerprint: str = "",
) -> dict:
    """Apply v2 confidence gates while preserving submitted candidate chronology."""
    ranked = list(rows)
    scores = sorted({row["score"] for row in ranked}, reverse=True)
    top_score = scores[0] if scores else 0.0
    second_score = scores[1] if len(scores) > 1 else top_score
    segments = _winning_segments(ranked, top_score) if ranked else []
    winning_rows = segments[0] if len(segments) == 1 else []
    segment: WinningSegment | None = None
    if winning_rows:
        segment = {
            "start_time": winning_rows[0]["time"],
            "end_time": winning_rows[-1]["time"],
            "representative_time": winning_rows[(len(winning_rows) - 1) // 2]["time"],
            "width_minutes": len(winning_rows),
        }
    margin = round((top_score - second_score) / max(abs(top_score), 1.0) * 100, 2)
    blocked = len(segments) != 1 or bool(missing_layers)
    high = (
        not blocked and effective_answer_count >= 4 and dimension_count >= 3
        and segment is not None and segment["width_minutes"] <= 5 and margin >= 20
    )
    medium = (
        not blocked and effective_answer_count >= 3 and dimension_count >= 2
        and segment is not None and segment["width_minutes"] <= 15 and margin >= 10
    )
    confidence: Confidence = "high" if high else "medium" if medium else "low"
    reasons = []
    if len(segments) != 1:
        reasons.append("tied_leader" if segments else "no_candidate_rows")
    if missing_layers:
        reasons.append("missing_mandatory_layers")
    if confidence == "low" and effective_answer_count < 3:
        reasons.append("insufficient_effective_evidence")
    fingerprint = request_fingerprint or _canonical_hash(ranked)
    return {
        "result_id": str(uuid5(NAMESPACE_URL, f"{ALGORITHM_VERSION}:{fingerprint}")),
        "confidence": confidence,
        "can_apply": confidence == "high",
        "winning_segment": segment,
        "event_count": effective_answer_count,
        "domain_count": dimension_count,
        "top_score": top_score,
        "second_score": second_score,
        "margin_percent": margin,
        "reasons": reasons,
        "evidence": [],
        "algorithm_version": ALGORITHM_VERSION,
        "evidence_mode": "dynamic_choice",
        "effective_answer_count": effective_answer_count,
        "dimension_count": dimension_count,
    }


def _validated_choice_evidence(
    evidence_rows: list | None, candidates: Sequence[str],
) -> tuple[list[dict], set[str]]:
    if not isinstance(evidence_rows, list):
        raise ValueError("choice evidence must contain partition evidence")
    if len(evidence_rows) > 10:
        raise ValueError("choice evidence may contain at most 10 rows")
    question_ids: set[str] = set()
    dimensions: set[str] = set()
    required = {
        "question_id", "opportunity_id", "partition_id", "dimension_code",
        "candidate_scores", "information_gain",
    }
    for evidence in evidence_rows:
        if not isinstance(evidence, dict) or set(evidence) != required:
            field = (
                "option_id"
                if isinstance(evidence, dict) and "option_id" in evidence
                else "partition evidence"
            )
            raise ValueError(f"choice evidence contains invalid {field}")
        question_id = evidence["question_id"].strip() if isinstance(evidence["question_id"], str) else ""
        if not question_id:
            raise ValueError("partition evidence question identifier must be non-empty")
        if question_id in question_ids:
            raise ValueError("duplicate question evidence is not allowed")
        if any(
            not isinstance(evidence[key], str) or not evidence[key].strip()
            for key in ("opportunity_id", "partition_id")
        ):
            raise ValueError("partition evidence identifier must be a non-empty string")
        _validate_scores(evidence, candidates)
        if evidence["dimension_code"] not in SUPPORTED_DIMENSIONS:
            raise ValueError("choice evidence dimension is unsupported")
        question_ids.add(question_id)
        dimensions.add(evidence["dimension_code"])
    return evidence_rows, dimensions


def _validate_scores(evidence: dict, candidates: Sequence[str]) -> None:
    import math

    scores = evidence["candidate_scores"]
    gain = evidence["information_gain"]
    valid_scores = isinstance(scores, dict) and set(scores) == set(candidates) and all(
        not isinstance(score, bool)
        and isinstance(score, int | float)
        and math.isfinite(score)
        and score >= 0
        for score in scores.values()
    )
    if not valid_scores:
        raise ValueError("candidate scores must exactly match the submitted range")
    if (
        isinstance(gain, bool) or not isinstance(gain, int | float)
        or not math.isfinite(gain) or gain < 0
    ):
        raise ValueError("choice evidence information gain must be finite")


def score_choice_evidence(request: dict) -> dict:
    """Sum only strict server-resolved primary evidence, then adjudicate it."""
    candidates = _candidate_times(
        request["birth_date"], request["start_time"], request["end_time"]
    )
    evidence_rows, dimensions = _validated_choice_evidence(
        request.get("choice_evidence"), candidates
    )
    totals = {candidate: 0.0 for candidate in candidates}
    for evidence in evidence_rows:
        for candidate in candidates:
            totals[candidate] += (
                float(evidence["candidate_scores"][candidate])
                * float(evidence["information_gain"])
            )
    rows: list[ChoiceRow] = [
        {"time": candidate, "score": round(score, 6)} for candidate, score in totals.items()
    ]
    return adjudicate_choice_rows(
        rows,
        effective_answer_count=len(evidence_rows),
        dimension_count=len(dimensions),
        missing_layers=[],
        request_fingerprint=_canonical_hash(request),
    )
