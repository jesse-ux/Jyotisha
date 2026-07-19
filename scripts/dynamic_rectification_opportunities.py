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

from scripts.dynamic_rectification_copy import (
    DIMENSION_CONTEXT,
    SUPPORTED_DIMENSIONS,
    visible_range_labels,
)

ALGORITHM_VERSION: Final = "birth-time-choice-scoring-v2"
OPPORTUNITY_MODEL_VERSION: Final = "birth-time-opportunity-model-v2"
MIN_INFORMATION_GAIN: Final = 0.15


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


def experience_window_sets(
    birth_date: str, as_of_date: str,
) -> list[tuple[str, list[tuple[date, date]]]]:
    born = date.fromisoformat(birth_date)
    as_of = date.fromisoformat(as_of_date)
    try:
        first = born.replace(year=born.year + 12)
    except ValueError:
        first = born.replace(year=born.year + 12, day=28)
    if as_of < first:
        return []
    day_count = (as_of - first).days + 1
    counts = [1] if day_count == 1 else list(range(2, min(4, day_count) + 1))
    return [
        (
            f"periods-{count}",
            [
                (
                    first + timedelta(days=day_count * index // count),
                    as_of if index == count - 1 else (
                        first + timedelta(days=day_count * (index + 1) // count - 1)
                    ),
                )
                for index in range(count)
            ],
        )
        for count in counts
    ]


def experience_windows(birth_date: str, as_of_date: str) -> list[tuple[date, date]]:
    sets = experience_window_sets(birth_date, as_of_date)
    return sets[-1][1] if sets else []


def candidate_window_rows(request: dict) -> list[dict]:
    """Compute each candidate chart once and reuse it across every window."""
    from scripts.active_rectification_event_engine import (
        DOMAIN_CONFIG,
        _candidate_datetimes,
        _candidate_row,
    )

    window_sets = experience_window_sets(request["birth_date"], request["as_of_date"])
    if not window_sets:
        return []
    events = []
    event_windows: dict[str, tuple[str, str, date, date]] = {}
    for dimension in sorted(SUPPORTED_DIMENSIONS):
        for window_group, windows in window_sets:
            for window_start, window_end in windows:
                event_id = str(uuid5(
                    NAMESPACE_URL,
                    f"{ALGORITHM_VERSION}:{window_group}:{dimension}:{window_start}:{window_end}",
                ))
                midpoint = window_start + (window_end - window_start) / 2
                events.append({
                    "id": event_id,
                    "domain": dimension,
                    "date": midpoint.isoformat(),
                    "precision": "day",
                })
                event_windows[event_id] = (
                    window_group, dimension, window_start, window_end,
                )
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
            "window_group": window_group,
            "dimension_code": dimension,
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "activations": activations[event_id],
            "missing_layers": [DOMAIN_CONFIG[dimension][0]]
            if DOMAIN_CONFIG[dimension][0] in missing else [],
        }
        for event_id, (window_group, dimension, window_start, window_end) in event_windows.items()
    ]


def compute_candidate_model(request: dict, row_builder: Callable[[dict], list[dict]]) -> dict:
    return {
        "version": ALGORITHM_VERSION,
        "opportunity_model_version": OPPORTUNITY_MODEL_VERSION,
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
        "version", "opportunity_model_version", "birth_date", "as_of_date", "range", "location",
        "candidate_times", "windows",
    }
    candidates = candidate_times(request["birth_date"], request["start_time"], request["end_time"])
    try:
        valid_header = (
            set(model) == expected
            and model["version"] == ALGORITHM_VERSION
            and model["opportunity_model_version"] == OPPORTUNITY_MODEL_VERSION
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
    generated = experience_window_sets(request["birth_date"], request["as_of_date"])
    minimum = generated[0][1][0][0] if generated else date.max
    maximum = date.fromisoformat(request["as_of_date"])
    groups = {name for name, _windows in generated}
    keys = [
        (row.get("window_group"), row.get("dimension_code"), row.get("window_start"), row.get("window_end"))
        for row in windows if isinstance(row, dict)
    ]
    return len(keys) == len(set(keys)) and all(
        isinstance(row, dict)
        and set(row) == {
            "window_group", "dimension_code", "window_start", "window_end", "activations", "missing_layers"
        }
        and row["window_group"] in groups
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
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in model["windows"]:
        if not row["missing_layers"]:
            grouped[(row["dimension_code"], row["window_group"])].append(row)
    variants: dict[str, list[dict]] = defaultdict(list)
    for (dimension, window_group), windows in sorted(grouped.items()):
        opportunity = _dimension_opportunity(
            dimension, window_group, windows, model["candidate_times"],
        )
        if opportunity is not None:
            variants[dimension].append(opportunity)
    result = [
        sorted(items, key=lambda item: (-item["estimated_information_gain"], item["opportunity_id"]))[0]
        for items in variants.values()
    ]
    return sorted(result, key=lambda item: (-item["estimated_information_gain"], item["opportunity_id"]))


def _dimension_opportunity(
    dimension: str, window_group: str, windows: list[dict], candidates: list[str],
) -> dict | None:
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
            "window_group": window_group,
            "dimension": dimension,
            "window_start": window["window_start"],
            "window_end": window["window_end"],
            "members": sorted(members),
        }
        for window, members in populated
    ]
    labels = visible_range_labels([
        {"window_start": item["window_start"], "window_end": item["window_end"]}
        for item in basis
    ])
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
