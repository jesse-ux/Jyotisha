#!/usr/bin/env python3
"""Replay the sealed AA birth-minute holdout without exposing truth to ranking."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.active_rectification_event_engine import (
    adjudicate_event_candidate_rows,
    compute_event_candidate_rows,
)
from scripts.active_rectification_events import ALGORITHM_VERSION, CandidateResult, CandidateScoreRow
from scripts.minute_rectification_holdout_validator import DEFAULT_MANIFEST, ROOT, validate


def implementation_sha256(files: list[str]) -> str:
    """Hash the ordered path/content pairs that define the frozen ranker."""
    digest = hashlib.sha256()
    for relative in sorted(files):
        path = ROOT / relative
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _minute_at_offset(value: str, offset: int) -> str:
    moment = datetime.strptime(value, "%H:%M") + timedelta(minutes=offset)
    return moment.strftime("%H:%M")


def _clock_distance(left: str, right: str) -> int:
    left_value = int(left[:2]) * 60 + int(left[3:])
    right_value = int(right[:2]) * 60 + int(right[3:])
    distance = abs(left_value - right_value)
    return min(distance, 1440 - distance)


def _request(case: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    birth = case["birth"]
    radius = int(case["candidate_radius_minutes"])
    return {
        "birth_date": birth["date"],
        "start_time": _minute_at_offset(birth["time"], -radius),
        "end_time": _minute_at_offset(birth["time"], radius),
        "lat": float(birth["latitude"]),
        "lon": float(birth["longitude"]),
        "tz": float(birth["timezone_offset"]),
        "events": [
            {"id": event["id"], "domain": event["domain"], "date": event["date"], "precision": event["precision"]}
            for event in events
        ],
    }


def _candidate_moments(case: dict[str, Any]) -> list[datetime]:
    birth = case["birth"]
    center = datetime.fromisoformat(f"{birth['date']}T{birth['time']}:00")
    radius = int(case["candidate_radius_minutes"])
    return [center + timedelta(minutes=offset) for offset in range(-radius, radius + 1)]


def _opaque_winner(benchmark_id: str, case_id: str, rows: list[CandidateScoreRow]) -> str:
    top_score = max(row["score"] for row in rows)
    leaders = [row["time"] for row in rows if row["score"] == top_score]
    return min(
        leaders,
        key=lambda value: hashlib.sha256(f"{benchmark_id}:{case_id}:{value}".encode()).hexdigest(),
    )


def _would_confirm(result: CandidateResult) -> bool:
    release_independent_reasons = [
        reason for reason in result["reasons"] if reason != "minute_holdout_not_ready"
    ]
    segment = result["winning_segment"]
    return (
        result["confidence"] == "high"
        and segment is not None
        and segment["width_minutes"] == 1
        and not release_independent_reasons
        and not result["missing_layers"]
    )


def summarize_trials(trials: list[dict[str, Any]], release_metrics: dict[str, Any]) -> dict[str, Any]:
    """Compute frozen aggregate metrics from truth-revealed trial outputs."""
    count = len(trials)
    if not count:
        metrics = {
            "top_1_rate": None,
            "top_3_rate": None,
            "mean_absolute_minute_error": None,
            "false_confirmation_rate": None,
            "correct_insufficient_evidence_rejection_rate": None,
            "confirmation_coverage_rate": None,
        }
        return {"metrics": metrics, "metric_gates_passed": False}
    metrics = {
        "top_1_rate": round(sum(item["true_rank"] <= 1 for item in trials) / count, 4),
        "top_3_rate": round(sum(item["true_rank"] <= 3 for item in trials) / count, 4),
        "mean_absolute_minute_error": round(sum(item["minute_error"] for item in trials) / count, 4),
        "false_confirmation_rate": round(sum(item["false_confirmation"] for item in trials) / count, 4),
        "correct_insufficient_evidence_rejection_rate": round(
            sum(item["insufficient_evidence_rejected"] for item in trials) / count, 4,
        ),
        "confirmation_coverage_rate": round(sum(item["would_confirm"] for item in trials) / count, 4),
    }
    passed = (
        metrics["top_1_rate"] >= float(release_metrics["top_1_rate_minimum"])
        and metrics["top_3_rate"] >= float(release_metrics["top_3_rate_minimum"])
        and metrics["mean_absolute_minute_error"] <= float(release_metrics["mean_absolute_minute_error_maximum"])
        and metrics["false_confirmation_rate"] <= float(release_metrics["false_confirmation_rate_maximum"])
        and metrics["correct_insufficient_evidence_rejection_rate"]
        >= float(release_metrics["correct_insufficient_evidence_rejection_rate_minimum"])
    )
    return {"metrics": metrics, "metric_gates_passed": passed}


def run(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validation = validate(manifest_path)
    frozen = manifest.get("frozen_scoring") or {}
    files = frozen.get("files") if isinstance(frozen.get("files"), list) else []
    actual_hash = implementation_sha256(files) if files else None
    hash_matches = actual_hash == frozen.get("implementation_sha256")
    algorithm_matches = frozen.get("algorithm_version") == ALGORITHM_VERSION
    invalid_ids = set(validation["invalid_cases"])
    trials: list[dict[str, Any]] = []
    if hash_matches and algorithm_matches:
        for case in manifest.get("cases", []):
            if case.get("case_id") in invalid_ids:
                continue
            request = _request(case, case["events"])
            rows = compute_event_candidate_rows(request, candidates=_candidate_moments(case))
            result = adjudicate_event_candidate_rows(request, rows)
            true_time = case["birth"]["time"]
            true_row = next(row for row in rows if row["time"] == true_time)
            true_rank = 1 + sum(row["score"] > true_row["score"] for row in rows)
            predicted = _opaque_winner(manifest["benchmark_id"], case["case_id"], rows)
            would_confirm = _would_confirm(result)

            sparse_request = _request(case, case["events"][:1])
            sparse_rows = compute_event_candidate_rows(sparse_request, candidates=_candidate_moments(case))
            sparse_result = adjudicate_event_candidate_rows(sparse_request, sparse_rows)
            trials.append({
                "case_id": case["case_id"],
                "candidate_count": len(rows),
                "published_truth_revealed_after_ranking": true_time,
                "predicted_time": predicted,
                "true_rank": true_rank,
                "minute_error": _clock_distance(predicted, true_time),
                "would_confirm": would_confirm,
                "false_confirmation": would_confirm and predicted != true_time,
                "insufficient_evidence_rejected": not _would_confirm(sparse_result),
                "full_trial_reasons": result["reasons"],
                "sparse_trial_reasons": sparse_result["reasons"],
            })

    aggregate = summarize_trials(trials, manifest.get("release_metrics") or {})
    minimum_cases_met = validation["valid_public_aa_cases"] >= validation["minimum_public_aa_cases"]
    release_ready = (
        validation["status"] == "ready_for_blind_replay"
        and hash_matches
        and algorithm_matches
        and minimum_cases_met
        and aggregate["metric_gates_passed"]
    )
    return {
        "scope": "minute_rectification_blind_holdout",
        "benchmark_id": manifest.get("benchmark_id"),
        "status": "release_gate_passed" if release_ready else "blocked",
        "validation": validation,
        "frozen_scoring": {
            "algorithm_matches": algorithm_matches,
            "implementation_hash_matches": hash_matches,
            "expected_sha256": frozen.get("implementation_sha256"),
            "actual_sha256": actual_hash,
        },
        "trial_count": len(trials),
        "trials": trials,
        **aggregate,
        "verified_minute_claim_allowed": release_ready,
        "boundary": "Holdout outcomes must never be used to tune scoring. Any scoring change requires a new benchmark version and a newly sealed evaluation set.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    print(json.dumps(run(args.manifest), ensure_ascii=False, indent=2, sort_keys=True))
