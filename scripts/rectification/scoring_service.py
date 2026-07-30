from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import date, timedelta
from functools import lru_cache
from typing import Any, Callable, Sequence

from scripts.active_rectification_event_engine import compute_candidate_static_contexts, compute_event_candidate_rows
from scripts.active_rectification_events import CandidateScoreRow
from scripts.rectification.contracts import LifeEvent, RectificationRequest

ALGORITHM_VERSION = "rectification-v5-matrix-scoring-1"
INPUT_CONTRACT_VERSION = "rectification-calculation-spec-v4"


def _parse(value: str) -> date:
    return date.fromisoformat(value)


def _iso(value: date) -> str:
    return value.isoformat()


def _month_end(value: date) -> date:
    next_month = value.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


def _even_dates(start: date, end: date, count: int) -> list[date]:
    if count <= 1 or start == end:
        return [start]
    span = (end - start).days
    return sorted({start + timedelta(days=round(span * index / (count - 1))) for index in range(count)})


def sample_event_dates(event: LifeEvent) -> list[str]:
    start, end = _parse(event["date_start"]), _parse(event["date_end"])
    precision = event["precision"]
    if start > end:
        raise ValueError("invalid_event_date_range")
    if precision == "day" or start == end:
        return [_iso(start)]
    if precision == "month":
        middle = start.replace(day=min(15, _month_end(start).day))
        return sorted({_iso(start), _iso(middle), _iso(end)})
    if precision == "quarter":
        values: list[date] = []
        cursor = start.replace(day=15)
        while cursor <= end and len(values) < 3:
            values.append(cursor)
            cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=15)
        return [_iso(item) for item in values] or [_iso(start)]
    if precision == "year":
        return [_iso(start.replace(month=month, day=15)) for month in range(1, 13)]
    return [_iso(item) for item in _even_dates(start, end, 12)]


def _legacy_request(request: RectificationRequest, event: LifeEvent, sampled_date: str) -> dict[str, Any]:
    return {
        "birth_date": request["birth_date"],
        "start_time": request["start_time"],
        "end_time": request["end_time"],
        "lat": request["lat"],
        "lon": request["lon"],
        "tz": request["tz"],
        "events": [{
            "id": event["id"], "domain": event["domain"], "date": sampled_date,
            "precision": "day", "summary": event.get("summary", ""),
        }],
    }


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


@lru_cache(maxsize=4096)
def _cached_rows(serialized: str) -> tuple[CandidateScoreRow, ...]:
    return tuple(compute_event_candidate_rows(json.loads(serialized)))


def build_event_contribution_matrix(
    request: RectificationRequest,
    row_provider: Callable[[dict[str, Any]], Sequence[CandidateScoreRow]] | None = None,
) -> dict[str, Any]:
    static_contexts = None if row_provider is not None else compute_candidate_static_contexts(request)
    provider = row_provider or (lambda value: compute_event_candidate_rows(value, static_contexts=static_contexts))
    matrix: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    missing_layers: set[str] = set()
    date_sensitivity: list[dict[str, Any]] = []
    candidate_grid: list[str] | None = None
    for event in request["events"]:
        samples = sample_event_dates(event)
        sample_rows = [list(provider(_legacy_request(request, event, sampled))) for sampled in samples]
        grids = [[row["time"] for row in rows] for rows in sample_rows]
        if any(grid != grids[0] for grid in grids[1:]) or (candidate_grid is not None and grids[0] != candidate_grid):
            raise ValueError("candidate_grid_mismatch")
        candidate_grid = grids[0]
        winners = []
        for rows in sample_rows:
            winners.append(max(rows, key=lambda row: row["score"])["time"])
            missing_layers.update(layer for row in rows for layer in row["missing_layers"])
        for index, candidate_time in enumerate(candidate_grid):
            evidences = [rows[index]["evidence"][0] for rows in sample_rows]
            points = [float(item["points"]) for item in evidences]
            matrix[event["id"]][candidate_time] = {
                "points": round(sum(points) / len(points), 4),
                "rule_ids": sorted({rule for item in evidences for rule in item["rule_ids"]}),
                "technique_layers": sorted({rule.split(":", 1)[0] for item in evidences for rule in item["rule_ids"]}),
            }
        winner = max(set(winners), key=winners.count)
        mean = sum(matrix[event["id"]][time]["points"] for time in candidate_grid) / len(candidate_grid)
        variance = sum((matrix[event["id"]][time]["points"] - mean) ** 2 for time in candidate_grid) / len(candidate_grid)
        date_sensitivity.append({
            "event_id": event["id"],
            "declared_date_range": {"start": event["date_start"], "end": event["date_end"], "precision": event["precision"]},
            "sample_dates": samples,
            "winner_retention_rate": winners.count(winner) / len(winners),
            "score_variance": round(variance, 6),
            "sample_winners": winners,
        })
    return {
        "candidate_times": candidate_grid or [],
        "matrix": dict(matrix),
        "date_sensitivity": date_sensitivity,
        "missing_layers": sorted(missing_layers),
        "static_contexts": static_contexts,
    }


def score_from_matrix(request: RectificationRequest, built: dict[str, Any]) -> list[CandidateScoreRow]:
    rows: list[CandidateScoreRow] = []
    for candidate_time in built["candidate_times"]:
        evidence = []
        for event in request["events"]:
            contribution = built["matrix"][event["id"]][candidate_time]
            evidence.append({
                "event_id": event["id"], "domain": event["domain"], "candidate_time": candidate_time,
                "rule_ids": contribution["rule_ids"], "points": contribution["points"],
            })
        rows.append({
            "time": candidate_time,
            "score": round(sum(item["points"] for item in evidence), 4),
            "evidence": evidence,
            "missing_layers": built["missing_layers"],
        })
    return rows


def calculation_spec(request: RectificationRequest) -> dict[str, Any]:
    def json_number(value: float) -> int | float:
        return int(value) if value.is_integer() else value

    spec = {
        "version": INPUT_CONTRACT_VERSION,
        "birthDate": request["birth_date"],
        "candidateRange": {"start": request["start_time"], "end": request["end_time"]},
        "latitude": json_number(request["lat"]),
        "longitude": json_number(request["lon"]),
        "timezoneOffsetHours": json_number(request["tz"]),
        "ayanamsa": "lahiri", "nodeMode": "mean", "minuteStep": 1,
    }
    for source, target in (
        ("birth_time_source", "birthTimeSource"),
        ("timezone_id", "timezoneId"),
        ("timezone_source", "timezoneSource"),
        ("local_time_status", "localTimeStatus"),
    ):
        if source in request:
            spec[target] = request[source]  # type: ignore[literal-required]
    return spec


def sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()
