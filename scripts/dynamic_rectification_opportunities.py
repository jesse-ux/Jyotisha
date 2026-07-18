# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
# ─── How to run ───
# .venv/bin/python -m pytest -q tests/test_dynamic_rectification.py
"""Candidate-model construction and opportunity partitioning for rectification."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from datetime import date, datetime, time, timedelta
from typing import Final
from uuid import NAMESPACE_URL, uuid5

ALGORITHM_VERSION: Final = "birth-time-choice-scoring-v2"
MIN_INFORMATION_GAIN: Final = 0.15
DIMENSION_CONTEXT: Final = {
    "education": "一次明显的升学、转学或学习方向变化",
    "relocation": "一次明显的搬家、离乡或长期居住地变化",
    "relationship": "一次明显的关系进入、结束或重要转变",
    "career": "一次明显的工作、职业方向或身份变化",
    "health_pressure": "一次持续的健康压力或生活压力变化",
}
SUPPORTED_DIMENSIONS: Final = frozenset(DIMENSION_CONTEXT)


def canonical_hash(value: Mapping | Sequence) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def candidate_times(birth_date: str, start_time: str, end_time: str) -> list[str]:
    day = date.fromisoformat(birth_date)
    start = datetime.combine(day, time.fromisoformat(start_time))
    end = datetime.combine(day, time.fromisoformat(end_time))
    if end < start:
        end += timedelta(days=1)
    count = int((end - start).total_seconds() // 60) + 1
    if not 1 <= count <= 1_440:
        raise ValueError("candidate range must contain between 1 and 1440 minutes")
    return [(start + timedelta(minutes=offset)).strftime("%H:%M") for offset in range(count)]


def experience_windows(birth_date: str, as_of_date: str) -> list[tuple[date, date]]:
    born = date.fromisoformat(birth_date)
    as_of = date.fromisoformat(as_of_date)
    try:
        first = born.replace(year=born.year + 12)
    except ValueError:
        first = born.replace(year=born.year + 12, day=28)
    if as_of < first:
        return []
    day_count = (as_of - first).days + 1
    count = min(4, day_count, max(2, math.ceil(day_count / (6 * 365))))
    boundaries = [first + timedelta(days=day_count * index // count) for index in range(count)]
    return [
        (start, as_of if index == count - 1 else boundaries[index + 1] - timedelta(days=1))
        for index, start in enumerate(boundaries)
    ]


def candidate_window_rows(request: dict) -> list[dict]:
    """Compute each candidate chart once and reuse it across every window."""
    from scripts.active_rectification_event_engine import (
        DOMAIN_CONFIG,
        _candidate_datetimes,
        _candidate_row,
    )

    windows = experience_windows(request["birth_date"], request["as_of_date"])
    if not windows:
        return []
    events = []
    event_windows: dict[str, tuple[str, date, date]] = {}
    for dimension in sorted(SUPPORTED_DIMENSIONS):
        for window_start, window_end in windows:
            event_id = str(uuid5(
                NAMESPACE_URL,
                f"{ALGORITHM_VERSION}:{dimension}:{window_start}:{window_end}",
            ))
            midpoint = window_start + (window_end - window_start) / 2
            events.append({
                "id": event_id,
                "domain": dimension,
                "date": midpoint.isoformat(),
                "precision": "day",
            })
            event_windows[event_id] = (dimension, window_start, window_end)
    calculation_request = {
        "birth_date": request["birth_date"],
        "start_time": request["start_time"],
        "end_time": request["end_time"],
        "lat": request["lat"],
        "lon": request["lon"],
        "tz": request["tz"],
        "events": events,
    }
    candidates = _candidate_datetimes(calculation_request)
    rows = [_candidate_row(calculation_request, candidate) for candidate in candidates]
    activations = {
        event_id: {row["time"]: 0.0 for row in rows} for event_id in event_windows
    }
    missing = {layer for row in rows for layer in row["missing_layers"]}
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
            if DOMAIN_CONFIG[dimension][0] in missing else [],
        }
        for event_id, (dimension, window_start, window_end) in event_windows.items()
    ]


def compute_candidate_model(request: dict, row_builder: Callable[[dict], list[dict]]) -> dict:
    return {
        "version": ALGORITHM_VERSION,
        "birth_date": request["birth_date"],
        "as_of_date": request["as_of_date"],
        "range": {"start_time": request["start_time"], "end_time": request["end_time"]},
        "location": {
            "lat": request["lat"],
            "lon": request["lon"],
            "tz": request["tz"],
        },
        "candidate_times": candidate_times(
            request["birth_date"], request["start_time"], request["end_time"]
        ),
        "windows": row_builder(request),
    }


def validate_candidate_model(model: dict, request: dict) -> dict:
    expected = {
        "version", "birth_date", "as_of_date", "range", "location",
        "candidate_times", "windows",
    }
    candidates = candidate_times(request["birth_date"], request["start_time"], request["end_time"])
    try:
        valid_header = (
            set(model) == expected
            and model["version"] == ALGORITHM_VERSION
            and model["birth_date"] == request["birth_date"]
            and model["as_of_date"] == request["as_of_date"]
            and model["range"] == {
                "start_time": request["start_time"], "end_time": request["end_time"]
            }
            and model["location"] == {
                "lat": request["lat"], "lon": request["lon"], "tz": request["tz"]
            }
            and model["candidate_times"] == candidates
            and isinstance(model["windows"], list)
        )
        valid_windows = _validate_windows(model["windows"], request, candidates)
    except (KeyError, TypeError, ValueError):
        valid_header = valid_windows = False
    if not valid_header or not valid_windows:
        raise ValueError("candidate model does not match the submitted request")
    return model


def _validate_windows(windows: list, request: dict, candidates: list[str]) -> bool:
    generated = experience_windows(request["birth_date"], request["as_of_date"])
    minimum = generated[0][0] if generated else date.max
    maximum = date.fromisoformat(request["as_of_date"])
    keys = [
        (row.get("dimension_code"), row.get("window_start"), row.get("window_end"))
        for row in windows if isinstance(row, dict)
    ]
    return len(keys) == len(set(keys)) and all(
        isinstance(row, dict)
        and set(row) == {
            "dimension_code", "window_start", "window_end", "activations", "missing_layers"
        }
        and row["dimension_code"] in SUPPORTED_DIMENSIONS
        and minimum <= date.fromisoformat(row["window_start"])
        <= date.fromisoformat(row["window_end"]) <= maximum
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
        for row in windows
    )


def opportunities(model: dict) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in model["windows"]:
        if not row["missing_layers"]:
            grouped[row["dimension_code"]].append(row)
    result = []
    for dimension, windows in sorted(grouped.items()):
        opportunity = _dimension_opportunity(dimension, windows, model["candidate_times"])
        if opportunity is not None:
            result.append(opportunity)
    return sorted(result, key=lambda item: (-item["estimated_information_gain"], item["opportunity_id"]))


def _range_label(item: dict, precision: str) -> str:
    start = date.fromisoformat(item["window_start"])
    end = date.fromisoformat(item["window_end"])
    if precision == "year":
        return f"{start.year} 年" if start.year == end.year else f"{start.year}—{end.year} 年"
    if precision == "month":
        if start.year == end.year:
            return f"{start.year} 年 {start.month} 月—{end.month} 月"
        return f"{start.year} 年 {start.month} 月—{end.year} 年 {end.month} 月"
    if start.year == end.year and start.month == end.month:
        return f"{start.year} 年 {start.month} 月 {start.day} 日—{end.day} 日"
    return (
        f"{start.year} 年 {start.month} 月 {start.day} 日—"
        f"{end.year} 年 {end.month} 月 {end.day} 日"
    )


def _visible_range_labels(items: list[dict]) -> list[str]:
    labels = [_range_label(item, "year") for item in items]
    for precision in ("month", "day"):
        duplicates = {label for label in labels if labels.count(label) > 1}
        if not duplicates:
            break
        labels = [
            _range_label(item, precision) if label in duplicates else label
            for item, label in zip(items, labels, strict=True)
        ]
    return labels


def _dimension_opportunity(dimension: str, windows: list[dict], candidates: list[str]) -> dict | None:
    neutral_context = DIMENSION_CONTEXT[dimension]
    memberships: dict[int, list[str]] = defaultdict(list)
    for candidate in candidates:
        winner = max(
            range(len(windows)),
            key=lambda index: (windows[index]["activations"][candidate], -index),
        )
        memberships[winner].append(candidate)
    populated = [(windows[index], members) for index, members in sorted(memberships.items())]
    if not 2 <= len(populated) <= 4:
        return None
    probabilities = [len(members) / len(candidates) for _, members in populated]
    gain = -sum(value * math.log(value) for value in probabilities) / math.log(len(populated))
    if gain < MIN_INFORMATION_GAIN:
        return None
    basis = [
        {
            "version": ALGORITHM_VERSION,
            "dimension": dimension,
            "window_start": window["window_start"],
            "window_end": window["window_end"],
            "members": sorted(members),
        }
        for window, members in populated
    ]
    labels = _visible_range_labels(basis)
    partitions = [
        {
            "partition_id": canonical_hash(item),
            "descriptor": f"{item['window_start']}--{item['window_end']}",
            "fallback_label": label,
            "candidate_scores": {
                candidate: 1.0 if candidate in item["members"] else 0.0
                for candidate in candidates
            },
        }
        for item, label in zip(basis, labels, strict=True)
    ]
    fingerprint = canonical_hash({"version": ALGORITHM_VERSION, "partitions": basis})
    return {
        "opportunity_id": canonical_hash({
            "version": ALGORITHM_VERSION, "dimension": dimension, "partitions": basis
        }),
        "dimension_code": dimension,
        "neutral_context": neutral_context,
        "estimated_information_gain": round(gain, 6),
        "candidate_partition_fingerprint": fingerprint,
        "fallback_prompt": f"哪一个时间段更接近{neutral_context}？",
        "partitions": partitions,
    }
