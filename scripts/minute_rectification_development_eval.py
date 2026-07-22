#!/usr/bin/env python3
"""Run non-holdout development cases and expose minute discriminability failures."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.active_rectification_event_engine import (
    adjudicate_event_candidate_rows,
    compute_event_candidate_rows,
)
from scripts.minute_candidate_discriminability import analyze_candidate_rows
from scripts.minute_rectification_blind_eval import (
    _candidate_moments,
    _clock_distance,
    _opaque_winner,
    _request,
)
from scripts.minute_rectification_development_validator import DEFAULT_MANIFEST, validate
from scripts.minute_rectification_feature_facts_v4 import (
    analyze_feature_fact_rows,
    build_fact_difference_opportunities,
    build_feature_fact_rows,
)
from scripts.minute_rectification_fact_ranker_v4 import (
    rank_fact_rows,
    score_fact_ranker_v4,
)
from scripts.minute_rectification_pairwise_v3 import rank_candidate_rows, score_pairwise_v3


def run(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validation = validate(manifest_path)
    invalid = {item["case_id"] for item in validation["invalid_cases"]}
    cases = []
    for case in manifest.get("cases", []):
        if case.get("case_id") in invalid:
            continue
        request = _request(case, case["events"])
        candidate_moments = _candidate_moments(case)
        rows = compute_event_candidate_rows(request, candidates=candidate_moments)
        fact_rows = build_feature_fact_rows(request, candidates=candidate_moments)
        fact_diagnostics = analyze_feature_fact_rows(fact_rows)
        fact_opportunities = build_fact_difference_opportunities(fact_rows)
        v2_result = adjudicate_event_candidate_rows(request, rows)
        v2_diagnostics = analyze_candidate_rows(rows)
        v3_rows, _ = rank_candidate_rows(rows, request["events"])
        v3_result = score_pairwise_v3(rows, request["events"])
        v3_diagnostics = analyze_candidate_rows(rows, ranking_rows=v3_rows)
        v4_rows, _ = rank_fact_rows(fact_rows, request["events"])
        v4_result = score_fact_ranker_v4(fact_rows, request["events"])
        v4_diagnostics = analyze_candidate_rows(v4_rows, ranking_rows=v4_rows)
        truth = case["birth"]["time"]
        truth_row = next(row for row in rows if row["time"] == truth)
        v3_truth_row = next(row for row in v3_rows if row["time"] == truth)
        v4_truth_row = next(row for row in v4_rows if row["time"] == truth)
        v2_predicted = _opaque_winner(manifest["benchmark_id"], case["case_id"], rows)
        v3_predicted = _opaque_winner(f"{manifest['benchmark_id']}:v3", case["case_id"], v3_rows)
        v4_predicted = _opaque_winner(f"{manifest['benchmark_id']}:v4", case["case_id"], v4_rows)
        cases.append({
            "case_id": case["case_id"],
            "published_time": truth,
            "production_confirmation_allowed": False,
            "p6_feature_facts": fact_diagnostics,
            "p6_fact_difference_opportunities": fact_opportunities,
            "v2": {
                "predicted_time": v2_predicted,
                "true_rank": 1 + sum(row["score"] > truth_row["score"] for row in rows),
                "minute_error": _clock_distance(v2_predicted, truth),
                "result_reasons": v2_result["reasons"],
                "discriminability": v2_diagnostics,
            },
            "v3": {
                "predicted_time": v3_predicted,
                "true_rank": 1 + sum(row["score"] > v3_truth_row["score"] for row in v3_rows),
                "minute_error": _clock_distance(v3_predicted, truth),
                "result_reasons": v3_result["reasons"],
                "winning_segment": v3_result["winning_segment"],
                "discriminability": v3_diagnostics,
            },
            "v4": {
                "predicted_time": v4_predicted,
                "true_rank": 1 + sum(row["score"] > v4_truth_row["score"] for row in v4_rows),
                "minute_error": _clock_distance(v4_predicted, truth),
                "result_reasons": v4_result["reasons"],
                "winning_segment": v4_result["winning_segment"],
                "stability_diagnostics": v4_result["stability_diagnostics"],
                "discriminability": v4_diagnostics,
            },
        })
    v2_errors = [case["v2"]["minute_error"] for case in cases]
    v3_errors = [case["v3"]["minute_error"] for case in cases]
    v4_errors = [case["v4"]["minute_error"] for case in cases]
    adjacent_pair_count = sum(
        max(case["v3"]["discriminability"]["candidate_count"] - 1, 0)
        for case in cases
    )
    indistinguishable_pair_count = sum(
        case["v3"]["discriminability"]["indistinguishable_adjacent_pair_count"]
        for case in cases
    )
    p6_indistinguishable_pair_count = sum(
        case["p6_feature_facts"]["indistinguishable_adjacent_pair_count"]
        for case in cases
    )
    p6_opportunities = [
        opportunity
        for case in cases
        for opportunity in case["p6_fact_difference_opportunities"]
    ]
    summary = {
        "v2_mean_minute_error": round(sum(v2_errors) / len(v2_errors), 4) if v2_errors else None,
        "v3_mean_minute_error": round(sum(v3_errors) / len(v3_errors), 4) if v3_errors else None,
        "v3_improved_case_count": sum(v3 < v2 for v2, v3 in zip(v2_errors, v3_errors)),
        "v3_worsened_case_count": sum(v3 > v2 for v2, v3 in zip(v2_errors, v3_errors)),
        "v3_unchanged_case_count": sum(v3 == v2 for v2, v3 in zip(v2_errors, v3_errors)),
        "v4_mean_minute_error": round(sum(v4_errors) / len(v4_errors), 4) if v4_errors else None,
        "v4_improved_vs_v2_case_count": sum(v4 < v2 for v2, v4 in zip(v2_errors, v4_errors)),
        "v4_worsened_vs_v2_case_count": sum(v4 > v2 for v2, v4 in zip(v2_errors, v4_errors)),
        "v4_unique_minute_count": sum(
            (case["v4"]["winning_segment"] or {}).get("width_minutes") == 1 for case in cases
        ),
        "v4_neighbor_stability_pass_count": sum(
            case["v4"]["stability_diagnostics"]["neighbor_stability"]["all_required_passed"]
            for case in cases
        ),
        "v4_leave_one_event_out_pass_count": sum(
            case["v4"]["stability_diagnostics"]["leave_one_event_out"]["status"] == "pass"
            for case in cases
        ),
        "indistinguishable_adjacent_pair_count": indistinguishable_pair_count,
        "adjacent_pair_count": adjacent_pair_count,
        "indistinguishable_adjacent_pair_ratio": round(
            indistinguishable_pair_count / adjacent_pair_count, 4
        ) if adjacent_pair_count else None,
        "p6_fact_indistinguishable_adjacent_pair_count": p6_indistinguishable_pair_count,
        "p6_fact_indistinguishable_adjacent_pair_ratio": round(
            p6_indistinguishable_pair_count / adjacent_pair_count, 4
        ) if adjacent_pair_count else None,
        "p6_fact_atoms_may_affect_score": False,
        "p6_fact_difference_opportunity_count": len(p6_opportunities),
        "p6_question_ready_opportunity_count": sum(
            opportunity["question_ready"] for opportunity in p6_opportunities
        ),
        "v3_shadow_only": True,
        "v3_may_replace_production": False,
        "v4_shadow_only": True,
        "v4_may_replace_production": False,
        "decision": "reject_v3_production_promotion",
        "v4_decision": "requires_independent_frozen_holdout",
    }
    return {
        "scope": "minute_rectification_development_evaluation",
        "benchmark_id": manifest.get("benchmark_id"),
        "status": "diagnostics_available" if cases else "blocked",
        "validation": validation,
        "case_count": len(cases),
        "cases": cases,
        "summary": summary,
        "excluded_from_holdout": True,
        "may_open_release_gate": False,
        "boundary": "Development outcomes may guide a future scorer version but are never added to sealed holdout metrics.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    print(json.dumps(run(args.manifest), ensure_ascii=False, indent=2, sort_keys=True))
