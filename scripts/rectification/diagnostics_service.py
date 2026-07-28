from __future__ import annotations

from collections import defaultdict
from statistics import variance
from typing import Any, Sequence

from scripts.active_rectification_events import CandidateScoreRow
from scripts.rectification.contracts import RectificationRequest


def _winner(rows: Sequence[CandidateScoreRow]) -> str | None:
    return max(rows, key=lambda row: row["score"])["time"] if rows else None


def _primary_cluster(rows: Sequence[CandidateScoreRow], relative_floor: float = .97) -> list[str]:
    if not rows:
        return []
    peak = max(row["score"] for row in rows)
    floor = peak * relative_floor if peak >= 0 else peak / relative_floor
    selected = [row["time"] for row in rows if row["score"] >= floor]
    if not selected:
        return []
    groups: list[list[str]] = []
    for current in selected:
        minute = lambda value: int(value[:2]) * 60 + int(value[3:])
        if groups and minute(current) - minute(groups[-1][-1]) == 1:
            groups[-1].append(current)
        else:
            groups.append([current])
    return max(groups, key=lambda group: (max(next(row["score"] for row in rows if row["time"] == time) for time in group), len(group)))


def _subtract(rows: Sequence[CandidateScoreRow], removed_ids: set[str]) -> list[CandidateScoreRow]:
    return [{**row, "score": round(row["score"] - sum(item["points"] for item in row["evidence"] if item["event_id"] in removed_ids), 4)} for row in rows]


def run_diagnostics(request: RectificationRequest, rows: list[CandidateScoreRow], built: dict[str, Any]) -> dict[str, Any]:
    primary = set(_primary_cluster(rows))
    event_runs = []
    domain_runs = []
    event_domain = {event["id"]: event["domain"] for event in request["events"]}
    for event in request["events"]:
        winner = _winner(_subtract(rows, {event["id"]}))
        event_runs.append({"removed_event_id": event["id"], "winner": winner, "retained": winner in primary})
    by_domain: dict[str, set[str]] = defaultdict(set)
    for event_id, domain in event_domain.items():
        by_domain[domain].add(event_id)
    for domain, event_ids in by_domain.items():
        winner = _winner(_subtract(rows, event_ids))
        domain_runs.append({"removed_domain": domain, "winner": winner, "retained": winner in primary})
    top = sorted(rows, key=lambda row: row["score"], reverse=True)
    top_score = top[0]["score"] if top else 0
    secondary = next((row for row in top if row["time"] not in primary), None)
    margin = 0 if not secondary else max(0, (top_score - secondary["score"]) / max(abs(top_score), 1e-9) * 100)
    positive_total = sum(max(row["score"], 0) for row in rows)
    primary_mass = sum(max(row["score"], 0) for row in rows if row["time"] in primary)
    date_items = []
    for item in built["date_sensitivity"]:
        date_items.append({
            **{key: value for key, value in item.items() if key != "sample_winners"},
            "candidate_cluster_retention_rate": sum(winner in primary for winner in item["sample_winners"]) / len(item["sample_winners"]),
        })
    layers: dict[str, float] = defaultdict(float)
    for event_id, candidates in built["matrix"].items():
        for contribution in candidates.values():
            for layer in contribution["technique_layers"]:
                layers[layer] += abs(contribution["points"])
    clusters = [_primary_cluster(rows)]
    candidate_splits = []
    if secondary and clusters[0]:
        candidate_splits.append({
            "left_cluster": {"start": clusters[0][0], "end": clusters[0][-1]},
            "right_cluster": {"start": secondary["time"], "end": secondary["time"]},
            "technique_layers": [name for name, _ in sorted(layers.items(), key=lambda item: item[1], reverse=True)[:8]],
            "event_ids": [item["event_id"] for item in secondary["evidence"] if item["points"] != 0],
        })
    return {
        "primary_cluster_retention_rate": 1.0 if primary else 0.0,
        "leave_one_event_out_retention_rate": sum(item["retained"] for item in event_runs) / len(event_runs) if event_runs else 0.0,
        "leave_one_domain_out_retention_rate": sum(item["retained"] for item in domain_runs) / len(domain_runs) if domain_runs else 0.0,
        "date_sensitivity_retention_rate": sum(item["candidate_cluster_retention_rate"] for item in date_items) / len(date_items) if date_items else 0.0,
        "neighbor_support_minutes": len(primary),
        "primary_secondary_margin_percent": round(min(margin, 100), 4),
        "cluster_mass_ratio": primary_mass / positive_total if positive_total else 0.0,
        "unstable_event_ids": [item["removed_event_id"] for item in event_runs if not item["retained"]],
        "most_discriminating_layers": [name for name, _ in sorted(layers.items(), key=lambda item: item[1], reverse=True)[:12]],
        "event_date_sensitivity": date_items,
        "candidate_splits": candidate_splits,
        "leave_one_event_out": event_runs,
        "leave_one_domain_out": domain_runs,
    }
