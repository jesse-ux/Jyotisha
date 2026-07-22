#!/usr/bin/env python3
"""Audit whether event evidence actually distinguishes adjacent birth minutes."""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from scripts.active_rectification_events import CandidateScoreRow


def _evidence_features(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": item["event_id"],
        "domain": item["domain"],
        "points": float(item["points"]),
        "rule_ids": sorted(item["rule_ids"]),
    }


def feature_fingerprint(row: CandidateScoreRow) -> str:
    """Hash only computed evidence features, never the candidate time or truth label."""
    payload = {
        "evidence": sorted(
            (
                _evidence_features(item)
                for item in row["evidence"]
            ),
            key=lambda item: (item["event_id"], item["domain"]),
        ),
        "missing_layers": sorted(row["missing_layers"]),
    }
    canonical = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def analyze_candidate_rows(
    rows: Sequence[CandidateScoreRow],
    *,
    ranking_rows: Sequence[CandidateScoreRow] | None = None,
) -> dict[str, Any]:
    """Return feature-equivalence classes and real adjacent-minute transitions."""
    candidates = list(rows)
    if not candidates:
        return {
            "scope": "minute_candidate_discriminability",
            "candidate_count": 0,
            "unique_feature_fingerprint_count": 0,
            "distinguishable_candidate_ratio": 0.0,
            "equivalence_classes": [],
            "adjacent_transitions": [],
            "indistinguishable_adjacent_pair_count": 0,
            "top_candidate_feature_unique": False,
            "status": "blocked_no_candidates",
        }

    fingerprints = {row["time"]: feature_fingerprint(row) for row in candidates}
    classes: dict[str, list[str]] = defaultdict(list)
    for row in candidates:
        classes[fingerprints[row["time"]]].append(row["time"])
    equivalence_classes = [
        {"feature_fingerprint": fingerprint, "candidate_times": times, "size": len(times)}
        for fingerprint, times in sorted(classes.items(), key=lambda item: item[1][0])
    ]

    adjacent_transitions = []
    indistinguishable = 0
    for previous, current in zip(candidates, candidates[1:]):
        previous_by_event = {
            item["event_id"]: _evidence_features(item) for item in previous["evidence"]
        }
        current_by_event = {
            item["event_id"]: _evidence_features(item) for item in current["evidence"]
        }
        changed_event_ids = sorted(
            event_id
            for event_id in set(previous_by_event) | set(current_by_event)
            if previous_by_event.get(event_id) != current_by_event.get(event_id)
        )
        feature_changed = fingerprints[previous["time"]] != fingerprints[current["time"]]
        indistinguishable += int(not feature_changed)
        adjacent_transitions.append({
            "between": [previous["time"], current["time"]],
            "feature_changed": feature_changed,
            "changed_event_ids": changed_event_ids,
            "score_delta": round(float(current["score"]) - float(previous["score"]), 4),
        })

    ranked = list(ranking_rows) if ranking_rows is not None else candidates
    top_score = max(float(row["score"]) for row in ranked)
    top_times = [row["time"] for row in ranked if float(row["score"]) == top_score]
    top_unique = len(top_times) == 1 and len(classes[fingerprints[top_times[0]]]) == 1
    unique_count = len(classes)
    status = (
        "minute_feature_unique"
        if top_unique
        else "range_has_differences_but_top_not_unique"
        if unique_count > 1
        else "blocked_feature_equivalent_range"
    )
    return {
        "scope": "minute_candidate_discriminability",
        "candidate_count": len(candidates),
        "unique_feature_fingerprint_count": unique_count,
        "distinguishable_candidate_ratio": round(unique_count / len(candidates), 4),
        "equivalence_classes": equivalence_classes,
        "adjacent_transitions": adjacent_transitions,
        "indistinguishable_adjacent_pair_count": indistinguishable,
        "top_candidate_times": top_times,
        "top_candidate_feature_unique": top_unique,
        "status": status,
        "boundary": "Feature uniqueness describes this scorer's computed evidence only; it is not proof that a birth minute is true.",
    }
