# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Range-preserving event scoring for the asynchronous rectification V4 worker."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any, Final, Literal, NotRequired, TypedDict
from uuid import NAMESPACE_URL, uuid5

from scripts.active_rectification_event_engine import compute_event_candidate_rows
from scripts.active_rectification_events import CandidateEvidence, CandidateScoreRow

ALGORITHM_VERSION: Final = "rectification-v4-range-scoring-1"
INPUT_CONTRACT_VERSION: Final = "rectification-calculation-spec-v4"

EventDomain = Literal["education", "relocation", "relationship", "career", "finance", "health_pressure"]
EventPrecision = Literal["day", "month", "quarter", "year", "range"]


def _json_compatible_numbers(value: Any) -> Any:
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, dict):
        return {key: _json_compatible_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_compatible_numbers(item) for item in value]
    return value


class RangeLifeEvent(TypedDict):
    id: str
    domain: EventDomain
    event_kind: str
    date_start: str
    date_end: str
    precision: EventPrecision
    summary: NotRequired[str]


class RangeRectificationRequest(TypedDict):
    birth_date: str
    start_time: str
    end_time: str
    lat: float
    lon: float
    tz: float
    events: list[RangeLifeEvent]


def _legacy_request(request: RangeRectificationRequest, boundary: Literal["start", "end"]) -> dict[str, Any]:
    return {
        "birth_date": request["birth_date"],
        "start_time": request["start_time"],
        "end_time": request["end_time"],
        "lat": request["lat"],
        "lon": request["lon"],
        "tz": request["tz"],
        "events": [{
            "id": event["id"],
            "domain": event["domain"],
            "date": event[f"date_{boundary}"],
            "precision": "day",
            "summary": event.get("summary", ""),
        } for event in request["events"]],
    }


def _evidence_by_event(row: CandidateScoreRow) -> dict[str, CandidateEvidence]:
    return {item["event_id"]: item for item in row["evidence"]}


def _average_rows(
    lower_rows: Sequence[CandidateScoreRow],
    upper_rows: Sequence[CandidateScoreRow],
) -> list[CandidateScoreRow]:
    if [row["time"] for row in lower_rows] != [row["time"] for row in upper_rows]:
        raise ValueError("candidate_grid_mismatch")
    averaged: list[CandidateScoreRow] = []
    for lower, upper in zip(lower_rows, upper_rows, strict=True):
        lower_events = _evidence_by_event(lower)
        upper_events = _evidence_by_event(upper)
        evidence: list[CandidateEvidence] = []
        for event_id in sorted(set(lower_events) | set(upper_events)):
            lower_item = lower_events.get(event_id)
            upper_item = upper_events.get(event_id)
            source = lower_item or upper_item
            if source is None:
                continue
            lower_points = lower_item["points"] if lower_item else 0.0
            upper_points = upper_item["points"] if upper_item else 0.0
            evidence.append({
                "event_id": event_id,
                "domain": source["domain"],
                "candidate_time": lower["time"],
                "rule_ids": sorted(set(
                    (lower_item or {}).get("rule_ids", [])
                    + (upper_item or {}).get("rule_ids", [])
                    + ["date_range_boundaries_averaged"]
                )),
                "points": round((lower_points + upper_points) / 2, 4),
            })
        averaged.append({
            "time": lower["time"],
            "score": round(sum(item["points"] for item in evidence), 4),
            "evidence": evidence,
            "missing_layers": sorted(set(lower["missing_layers"] + upper["missing_layers"])),
        })
    return averaged


def _minute_value(value: str) -> int:
    hour, minute = value.split(":", maxsplit=1)
    return int(hour) * 60 + int(minute)


def _next_minute(previous: str, current: str) -> bool:
    return (_minute_value(current) - _minute_value(previous)) % 1_440 == 1


def _primary_cluster(rows: Sequence[CandidateScoreRow], relative_floor: float = 0.97) -> list[str]:
    if not rows:
        return []
    peak = max(row["score"] for row in rows)
    floor = peak * relative_floor if peak >= 0 else peak / relative_floor
    viable = sorted((row for row in rows if row["score"] >= floor), key=lambda row: _minute_value(row["time"]))
    clusters: list[list[CandidateScoreRow]] = []
    for row in viable:
        if clusters and _next_minute(clusters[-1][-1]["time"], row["time"]):
            clusters[-1].append(row)
        else:
            clusters.append([row])
    if not clusters:
        return []
    clusters.sort(key=lambda group: (-max(row["score"] for row in group), -sum(max(row["score"], 0) for row in group)))
    return [row["time"] for row in clusters[0]]


def _top_time(rows: Sequence[CandidateScoreRow]) -> str | None:
    if not rows:
        return None
    top = max(row["score"] for row in rows)
    return next(row["time"] for row in rows if row["score"] == top)


def _leave_one_out(rows: Sequence[CandidateScoreRow], event_ids: Sequence[str], primary: set[str]) -> dict[str, Any]:
    runs = []
    retained = 0
    for event_id in event_ids:
        rescored = []
        for row in rows:
            removed = sum(item["points"] for item in row["evidence"] if item["event_id"] == event_id)
            rescored.append({**row, "score": round(row["score"] - removed, 4)})
        winner = _top_time(rescored)
        stable = winner in primary
        retained += int(stable)
        runs.append({"removed_event_id": event_id, "winner": winner, "primary_cluster_retained": stable})
    return {
        "retention_rate": retained / len(event_ids) if event_ids else 0.0,
        "runs": runs,
    }


def score_life_events_v4(request: RangeRectificationRequest) -> dict[str, Any]:
    lower_rows = compute_event_candidate_rows(_legacy_request(request, "start"))
    upper_rows = compute_event_candidate_rows(_legacy_request(request, "end"))
    rows = _average_rows(lower_rows, upper_rows)
    primary = _primary_cluster(rows)
    primary_set = set(primary)
    lower_winner = _top_time(lower_rows)
    upper_winner = _top_time(upper_rows)
    date_retention = sum(winner in primary_set for winner in (lower_winner, upper_winner)) / 2
    loo = _leave_one_out(rows, [event["id"] for event in request["events"]], primary_set)
    normalized = json.dumps(request, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    spec = {
        "version": INPUT_CONTRACT_VERSION,
        "birthDate": request["birth_date"],
        "candidateRange": {"start": request["start_time"], "end": request["end_time"]},
        "latitude": request["lat"],
        "longitude": request["lon"],
        "timezoneOffsetHours": request["tz"],
        "ayanamsa": "lahiri",
        "nodeMode": "mean",
        "minuteStep": 1,
    }
    spec_hash = hashlib.sha256(json.dumps(
        _json_compatible_numbers(spec), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    missing_layers = sorted({layer for row in rows for layer in row["missing_layers"]})
    candidates = [{
        "time": row["time"],
        "score": row["score"],
        "supporting_event_ids": [item["event_id"] for item in row["evidence"] if item["points"] > 0],
        "conflicting_event_ids": [item["event_id"] for item in row["evidence"] if item["points"] < 0],
    } for row in rows]
    return {
        "result_id": str(uuid5(NAMESPACE_URL, f"{ALGORITHM_VERSION}:{fingerprint}")),
        "algorithm_version": ALGORITHM_VERSION,
        "calculation_spec": spec,
        "calculation_spec_hash": spec_hash,
        "candidate_scores": candidates,
        "primary_cluster_times": primary,
        "robustness": {
            "neighbor_support_minutes": len(primary),
            "leave_one_out_retention_rate": loo["retention_rate"],
            "date_sensitivity_retention_rate": date_retention,
            "date_boundary_winners": {"start": lower_winner, "end": upper_winner},
            "leave_one_out": loo,
        },
        "missing_layers": missing_layers,
        "can_confirm_exact_minute": False,
    }


if __name__ == "__main__":
    raise SystemExit("Import score_life_events_v4 from the worker or API server.")
