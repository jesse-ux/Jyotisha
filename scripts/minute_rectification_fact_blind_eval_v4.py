#!/usr/bin/env python3
"""Replay a sealed public-AA holdout with the shadow fact ranker v4."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.minute_rectification_blind_eval import (
    _candidate_moments,
    _clock_distance,
    _opaque_winner,
    _request,
    implementation_sha256,
    summarize_trials,
)
from scripts.minute_rectification_fact_ranker_v4 import (
    ALGORITHM_VERSION,
    rank_fact_rows,
    score_fact_ranker_v4,
)
from scripts.minute_rectification_feature_facts_v4 import build_feature_fact_rows
from scripts.minute_rectification_holdout_validator import validate

DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / "references" / "real_case_calibration" / "minute_rectification_holdout_v3.json"


def _would_confirm(result: dict[str, Any]) -> bool:
    independent_reasons = [
        reason for reason in result["reasons"]
        if reason != "fact_ranker_v4_holdout_not_ready"
    ]
    segment = result["winning_segment"]
    return (
        result["confidence"] == "high"
        and segment is not None
        and segment["width_minutes"] == 1
        and not independent_reasons
        and not result["missing_layers"]
    )


def run(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validation = validate(manifest_path)
    frozen = manifest.get("frozen_scoring") or {}
    files = frozen.get("files") if isinstance(frozen.get("files"), list) else []
    actual_hash = implementation_sha256(files) if files else None
    hash_matches = actual_hash == frozen.get("implementation_sha256")
    algorithm_matches = frozen.get("algorithm_version") == ALGORITHM_VERSION
    invalid_ids = set(validation["invalid_cases"])
    trials = []
    if hash_matches and algorithm_matches:
        for case in manifest.get("cases", []):
            if case.get("case_id") in invalid_ids:
                continue
            request = _request(case, case["events"])
            candidates = _candidate_moments(case)
            fact_rows = build_feature_fact_rows(request, candidates=candidates)
            ranked_rows, _ = rank_fact_rows(fact_rows, request["events"])
            result = score_fact_ranker_v4(fact_rows, request["events"])
            true_time = case["birth"]["time"]
            true_row = next(row for row in ranked_rows if row["time"] == true_time)
            true_rank = 1 + sum(row["score"] > true_row["score"] for row in ranked_rows)
            predicted = _opaque_winner(
                manifest["benchmark_id"], case["case_id"], ranked_rows,
            )
            would_confirm = _would_confirm(result)

            sparse_request = _request(case, case["events"][:1])
            sparse_facts = build_feature_fact_rows(sparse_request, candidates=candidates)
            sparse_result = score_fact_ranker_v4(sparse_facts, sparse_request["events"])
            trials.append({
                "case_id": case["case_id"],
                "candidate_count": len(ranked_rows),
                "published_truth_revealed_after_ranking": true_time,
                "predicted_time": predicted,
                "true_rank": true_rank,
                "minute_error": _clock_distance(predicted, true_time),
                "would_confirm": would_confirm,
                "false_confirmation": would_confirm and predicted != true_time,
                "insufficient_evidence_rejected": not _would_confirm(sparse_result),
                "full_trial_reasons": result["reasons"],
                "sparse_trial_reasons": sparse_result["reasons"],
                "neighbor_stability": result["stability_diagnostics"]["neighbor_stability"],
                "leave_one_event_out": result["stability_diagnostics"]["leave_one_event_out"],
                "ablation": result["stability_diagnostics"]["ablation"],
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
        "scope": "minute_rectification_fact_ranker_v4_blind_holdout",
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
        "boundary": "Frozen holdout outcomes may not tune v4. A scoring change requires a new algorithm version and a new sealed evaluation set.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    print(json.dumps(run(args.manifest), ensure_ascii=False, indent=2, sort_keys=True))
