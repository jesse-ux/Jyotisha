# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
# ─── How to run ───
# .venv/bin/python -m pytest -q tests/test_dynamic_rectification.py
"""Candidate-backed opportunities and deterministic dynamic-choice scoring."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import date, datetime, time, timedelta
from typing import Final, Literal, TypedDict
from uuid import NAMESPACE_URL, UUID, uuid5

ALGORITHM_VERSION: Final = "birth-time-choice-scoring-v2"
MIN_INFORMATION_GAIN: Final = 0.15
SUPPORTED_DIMENSIONS: Final = frozenset(
    {"education", "relocation", "relationship", "career", "health_pressure"}
)


class ChoiceRow(TypedDict):
    time: str
    score: float


class WinningSegment(TypedDict):
    start_time: str
    end_time: str
    representative_time: str
    width_minutes: int


Confidence = Literal["low", "medium", "high"]


def _canonical_hash(value: Mapping | Sequence) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _candidate_times(birth_date: str, start_time: str, end_time: str) -> list[str]:
    day = date.fromisoformat(birth_date)
    start = datetime.combine(day, time.fromisoformat(start_time))
    end = datetime.combine(day, time.fromisoformat(end_time))
    if end < start:
        end += timedelta(days=1)
    count = int((end - start).total_seconds() // 60) + 1
    if not 1 <= count <= 1_440:
        raise ValueError("candidate range must contain between 1 and 1440 minutes")
    return [(start + timedelta(minutes=offset)).strftime("%H:%M") for offset in range(count)]


def _experience_windows(birth_date: str, as_of_date: str) -> list[tuple[date, date]]:
    born = date.fromisoformat(birth_date)
    as_of = date.fromisoformat(as_of_date)
    try:
        first = born.replace(year=born.year + 12)
    except ValueError:
        first = born.replace(year=born.year + 12, day=28)
    if as_of < first:
        return []
    day_count = (as_of - first).days + 1
    window_count = min(4, day_count, max(2, math.ceil(day_count / (6 * 365))))
    boundaries = [first + timedelta(days=day_count * index // window_count) for index in range(window_count)]
    return [
        (start, as_of if index == window_count - 1 else boundaries[index + 1] - timedelta(days=1))
        for index, start in enumerate(boundaries)
    ]


def _candidate_window_rows(request: dict) -> list[dict]:
    """Compute each candidate chart once and reuse it for every dimension/window."""
    from scripts.active_rectification_event_engine import (
        DOMAIN_CONFIG,
        _candidate_datetimes,
        _candidate_row,
    )

    windows = _experience_windows(request["birth_date"], request["as_of_date"])
    if not windows:
        return []
    synthetic_events = []
    event_windows: dict[str, tuple[str, date, date]] = {}
    for dimension in sorted(SUPPORTED_DIMENSIONS):
        for window_start, window_end in windows:
            event_id = str(uuid5(NAMESPACE_URL, f"{ALGORITHM_VERSION}:{dimension}:{window_start}:{window_end}"))
            midpoint = window_start + (window_end - window_start) / 2
            synthetic_events.append(
                {"id": event_id, "domain": dimension, "date": midpoint.isoformat(), "precision": "day"}
            )
            event_windows[event_id] = (dimension, window_start, window_end)
    calculation_request = {
        "birth_date": request["birth_date"],
        "start_time": request["start_time"],
        "end_time": request["end_time"],
        "lat": request["lat"],
        "lon": request["lon"],
        "tz": request["tz"],
        "events": synthetic_events,
    }
    rows = [_candidate_row(calculation_request, candidate) for candidate in _candidate_datetimes(calculation_request)]
    activations = {
        event_id: {row["time"]: 0.0 for row in rows}
        for event_id in event_windows
    }
    missing_layers = sorted({layer for row in rows for layer in row["missing_layers"]})
    for row in rows:
        for evidence in row["evidence"]:
            activations[evidence["event_id"]][row["time"]] = float(evidence["points"])
    return [
        {
            "dimension_code": dimension,
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "activations": activations[event_id],
            "missing_layers": [DOMAIN_CONFIG[dimension][0]]
            if DOMAIN_CONFIG[dimension][0] in missing_layers else [],
        }
        for event_id, (dimension, window_start, window_end) in event_windows.items()
    ]


def _compute_candidate_model(request: dict) -> dict:
    return {
        "version": ALGORITHM_VERSION,
        "birth_date": request["birth_date"],
        "as_of_date": request["as_of_date"],
        "range": {"start_time": request["start_time"], "end_time": request["end_time"]},
        "candidate_times": _candidate_times(request["birth_date"], request["start_time"], request["end_time"]),
        "windows": _candidate_window_rows(request),
    }


def _validate_candidate_model(model: dict, request: dict) -> dict:
    expected_keys = {"version", "birth_date", "as_of_date", "range", "candidate_times", "windows"}
    candidates = _candidate_times(request["birth_date"], request["start_time"], request["end_time"])
    try:
        valid_header = (
            set(model) == expected_keys
            and model["version"] == ALGORITHM_VERSION
            and model["birth_date"] == request["birth_date"]
            and model["as_of_date"] == request["as_of_date"]
            and model["range"] == {"start_time": request["start_time"], "end_time": request["end_time"]}
            and model["candidate_times"] == candidates
            and isinstance(model["windows"], list)
        )
        first_window = _experience_windows(request["birth_date"], request["as_of_date"])
        minimum_date = first_window[0][0] if first_window else date.max
        maximum_date = date.fromisoformat(request["as_of_date"])
        window_keys = [
            (row.get("dimension_code"), row.get("window_start"), row.get("window_end"))
            for row in model["windows"] if isinstance(row, dict)
        ]
        valid_windows = len(window_keys) == len(set(window_keys)) and all(
            isinstance(row, dict)
            and set(row) == {"dimension_code", "window_start", "window_end", "activations", "missing_layers"}
            and row["dimension_code"] in SUPPORTED_DIMENSIONS
            and minimum_date <= date.fromisoformat(row["window_start"])
            <= date.fromisoformat(row["window_end"]) <= maximum_date
            and isinstance(row["activations"], dict)
            and set(row["activations"]) == set(candidates)
            and all(
                not isinstance(score, bool)
                and isinstance(score, int | float)
                and math.isfinite(score)
                and score >= 0
                for score in row["activations"].values()
            )
            and isinstance(row["missing_layers"], list)
            and all(isinstance(layer, str) and layer for layer in row["missing_layers"])
            for row in model["windows"]
        )
    except (KeyError, TypeError, ValueError):
        valid_header = valid_windows = False
    if not valid_header or not valid_windows:
        raise ValueError("candidate model does not match the submitted request")
    return model


def _opportunities(model: dict) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in model["windows"]:
        if not row["missing_layers"]:
            grouped[row["dimension_code"]].append(row)
    opportunities = []
    candidates = model["candidate_times"]
    for dimension, windows in sorted(grouped.items()):
        memberships: dict[int, list[str]] = defaultdict(list)
        for candidate in candidates:
            winner = max(range(len(windows)), key=lambda index: (windows[index]["activations"][candidate], -index))
            memberships[winner].append(candidate)
        populated = [(windows[index], members) for index, members in sorted(memberships.items()) if members]
        if not 2 <= len(populated) <= 4:
            continue
        probabilities = [len(members) / len(candidates) for _, members in populated]
        information_gain = -sum(value * math.log(value) for value in probabilities) / math.log(len(populated))
        if information_gain < MIN_INFORMATION_GAIN:
            continue
        partition_basis = []
        partitions = []
        for window, members in populated:
            basis = {
                "version": ALGORITHM_VERSION,
                "dimension": dimension,
                "window_start": window["window_start"],
                "window_end": window["window_end"],
                "members": sorted(members),
            }
            partition_basis.append(basis)
            partitions.append(
                {
                    "partition_id": _canonical_hash(basis),
                    "descriptor": f"{window['window_start']}--{window['window_end']}",
                    "fallback_label": f"{window['window_start'][:4]}—{window['window_end'][:4]}",
                    "candidate_scores": {candidate: 1.0 if candidate in members else 0.0 for candidate in candidates},
                }
            )
        fingerprint = _canonical_hash({"version": ALGORITHM_VERSION, "partitions": partition_basis})
        opportunities.append(
            {
                "opportunity_id": _canonical_hash({"version": ALGORITHM_VERSION, "dimension": dimension, "partitions": partition_basis}),
                "dimension_code": dimension,
                "neutral_context": dimension,
                "estimated_information_gain": round(information_gain, 6),
                "candidate_partition_fingerprint": fingerprint,
                "fallback_prompt": f"下面哪个时间段更接近你在 {dimension} 方面的明显变化？",
                "partitions": partitions,
            }
        )
    return sorted(opportunities, key=lambda item: (-item["estimated_information_gain"], item["opportunity_id"]))


def build_difference_packet(request: dict) -> dict:
    """Build reusable candidate activations and unused high-gain opportunities."""
    candidates = _candidate_times(request["birth_date"], request["start_time"], request["end_time"])
    _validated_choice_evidence(request.get("evidence"), candidates)
    model = request.get("candidate_model")
    candidate_model = _compute_candidate_model(request) if model is None else _validate_candidate_model(model, request)
    dismissed = set(request.get("dismissed_opportunity_ids", []))
    fingerprints = set(request.get("partition_fingerprints", []))
    opportunities = [
        item for item in _opportunities(candidate_model)
        if item["opportunity_id"] not in dismissed
        and item["candidate_partition_fingerprint"] not in fingerprints
    ]
    return {
        "case_id": request["case_id"],
        "scoring_version": ALGORITHM_VERSION,
        "current_range": {"start_time": request["start_time"], "end_time": request["end_time"]},
        "opportunities": opportunities,
        "asked_question_fingerprints": list(request.get("question_fingerprints", [])),
        "candidate_partition_fingerprints": list(request.get("partition_fingerprints", [])),
        "recent_range_history": list(request.get("recent_ranges", [])),
        "candidate_model": candidate_model,
    }


def _minute_value(value: str) -> int:
    hour, minute = value.split(":", maxsplit=1)
    return int(hour) * 60 + int(minute)


def _winning_segments(rows: Sequence[ChoiceRow], top_score: float) -> list[list[ChoiceRow]]:
    segments: list[list[ChoiceRow]] = []
    for row in rows:
        if row["score"] != top_score:
            continue
        follows = segments and (
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
    """Apply v2 confidence gates to precomputed effective choice evidence."""
    ranked = sorted(rows, key=lambda row: _minute_value(row["time"]))
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
    fingerprint = request_fingerprint or _canonical_hash(list(ranked))
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


def _validated_choice_evidence(evidence_rows: list | None, candidates: Sequence[str]) -> tuple[list[dict], set[str]]:
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
            field = "option_id" if isinstance(evidence, dict) and "option_id" in evidence else "partition evidence"
            raise ValueError(f"choice evidence contains invalid {field}")
        try:
            UUID(evidence["question_id"])
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError("partition evidence question_id must be a UUID") from exc
        if evidence["question_id"] in question_ids:
            raise ValueError("duplicate question evidence is not allowed")
        if any(
            not isinstance(evidence[key], str) or not evidence[key]
            for key in ("opportunity_id", "partition_id")
        ):
            raise ValueError("partition evidence identifier must be a non-empty string")
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
        if evidence["dimension_code"] not in SUPPORTED_DIMENSIONS:
            raise ValueError("choice evidence dimension is unsupported")
        if (
            isinstance(gain, bool) or not isinstance(gain, int | float)
            or not math.isfinite(gain) or gain < 0
        ):
            raise ValueError("choice evidence information gain must be finite")
        question_ids.add(evidence["question_id"])
        dimensions.add(evidence["dimension_code"])
    return evidence_rows, dimensions


def score_choice_evidence(request: dict) -> dict:
    """Sum only strict server-resolved primary evidence, then adjudicate it."""
    candidates = _candidate_times(request["birth_date"], request["start_time"], request["end_time"])
    evidence_rows, dimensions = _validated_choice_evidence(
        request.get("choice_evidence"), candidates
    )
    totals = {candidate: 0.0 for candidate in candidates}
    for evidence in evidence_rows:
        scores = evidence["candidate_scores"]
        gain = evidence["information_gain"]
        for candidate in candidates:
            totals[candidate] += float(scores[candidate]) * float(gain)
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
