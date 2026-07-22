#!/usr/bin/env python3
"""Replay public structured events and a fixture-labeled transport filter."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.minute_rectification_blind_eval import (  # noqa: E402
    _candidate_moments,
    _clock_distance,
    _opaque_winner,
    _request,
)
from scripts.minute_rectification_fact_ranker_v4 import (  # noqa: E402
    rank_fact_rows,
    score_fact_ranker_v4,
)
from scripts.minute_rectification_feature_facts_v4 import build_feature_fact_rows  # noqa: E402

DEFAULT_MANIFEST = ROOT / "references/real_case_calibration/conversational_rectification_development_v1.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_cases(manifest: dict[str, Any], manifest_path: Path) -> dict[str, dict[str, Any]]:
    source_path = ROOT / manifest["source_manifest"]
    source = _load(source_path)
    return {case["case_id"]: case for case in source["cases"]}


def _step_result(benchmark_id: str, case: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    if not events:
        return {
            "scored_event_count": 0,
            "true_rank": None,
            "predicted_time": None,
            "minute_error": None,
            "winning_segment": None,
            "would_safely_converge": False,
            "result_reasons": ["no_scoreable_events"],
        }
    request = _request(case, events)
    candidates = _candidate_moments(case)
    fact_rows = build_feature_fact_rows(request, candidates=candidates)
    ranked_rows, _ = rank_fact_rows(fact_rows, request["events"])
    result = score_fact_ranker_v4(fact_rows, request["events"])
    truth = case["birth"]["time"]
    truth_row = next(row for row in ranked_rows if row["time"] == truth)
    top_score = max(row["score"] for row in ranked_rows)
    top_score_class_size = sum(row["score"] == top_score for row in ranked_rows)
    event_signature = ",".join(event["id"] for event in events)
    deterministic_tiebreak = _opaque_winner(
        f"{benchmark_id}:{event_signature}", case["case_id"], ranked_rows
    )
    true_rank = 1 + sum(row["score"] > truth_row["score"] for row in ranked_rows)
    segment = result["winning_segment"]
    neighbor_passed = result["stability_diagnostics"]["neighbor_stability"]["all_required_passed"]
    leave_one_out_passed = result["stability_diagnostics"]["leave_one_event_out"]["status"] == "pass"
    blocking_reasons = [reason for reason in result["reasons"] if reason != "fact_ranker_v4_holdout_not_ready"]
    runtime_confirmation_candidate = (
        len(events) >= 5
        and len({event["domain"] for event in events}) >= 3
        and segment is not None
        and segment["width_minutes"] == 1
        and neighbor_passed
        and leave_one_out_passed
        and not blocking_reasons
    )
    predicted = deterministic_tiebreak if segment and segment["width_minutes"] == 1 else None
    offline_truth_qualified_success = (
        runtime_confirmation_candidate
        and true_rank == 1
        and predicted is not None
        and _clock_distance(predicted, truth) <= 2
    )
    return {
        "scored_event_count": len(events),
        "true_rank": true_rank,
        "truth_in_top_score_tie": truth_row["score"] == top_score,
        "top_score_class_size": top_score_class_size,
        "predicted_time": predicted,
        "minute_error": _clock_distance(predicted, truth) if predicted else None,
        "deterministic_tiebreak_time": deterministic_tiebreak,
        "deterministic_tiebreak_error": _clock_distance(deterministic_tiebreak, truth),
        "winning_segment": segment,
        "neighbor_stability_passed": neighbor_passed,
        "leave_one_event_out_passed": leave_one_out_passed,
        "runtime_confirmation_candidate": runtime_confirmation_candidate,
        "offline_truth_qualified_success": offline_truth_qualified_success,
        "result_reasons": result["reasons"],
    }


def run(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = _load(manifest_path)
    sources = _source_cases(manifest, manifest_path)
    case_results = []
    for replay_case in manifest["cases"]:
        case = sources[replay_case["case_id"]]
        by_event_id = {event["id"]: event for event in case["events"]}
        oracle_events: list[dict[str, Any]] = []
        product_events: list[dict[str, Any]] = []
        turns = []
        for turn_index, disclosure in enumerate(replay_case["disclosure_order"], start=1):
            event = by_event_id[disclosure["event_id"]]
            oracle_events.append(event)
            if disclosure["expected_route_scoreable"]:
                product_events.append(event)
            turns.append({
                "turn": turn_index,
                "event_id": event["id"],
                "user_utterance": disclosure["user_utterance"],
                "route_scoreable": disclosure["expected_route_scoreable"],
                "oracle_structured": _step_result(
                    manifest["benchmark_id"], case, oracle_events,
                ),
                "simulated_current_transport_filter": _step_result(
                    manifest["benchmark_id"], case, product_events,
                ),
            })
        final_oracle = turns[-1]["oracle_structured"]
        final_product = turns[-1]["simulated_current_transport_filter"]
        case_results.append({
            "case_id": case["case_id"],
            "published_time": case["birth"]["time"],
            "turns": turns,
            "final_oracle_structured": final_oracle,
            "final_simulated_current_transport_filter": final_product,
        })

    def summary(key: str) -> dict[str, Any]:
        finals = [case[key] for case in case_results]
        segments = [item["winning_segment"] for item in finals if item["winning_segment"]]
        return {
            "case_count": len(finals),
            "cases_reaching_five_scoreable_events": sum(
                item["scored_event_count"] >= 5 for item in finals
            ),
            "truth_rank_le_3_rate": round(
                sum((item["true_rank"] or 999) <= 3 for item in finals) / len(finals), 4
            ),
            "deterministic_tiebreak_mean_absolute_error": round(
                sum(item["deterministic_tiebreak_error"] for item in finals) / len(finals), 4
            ),
            "truth_in_top_score_tie_rate": round(
                sum(item["truth_in_top_score_tie"] for item in finals) / len(finals), 4
            ),
            "unique_minute_count": sum(
                segment["width_minutes"] == 1 for segment in segments
            ),
            "mean_winning_segment_width_minutes": round(
                sum(segment["width_minutes"] for segment in segments) / len(segments), 4
            ) if segments else None,
            "neighbor_stability_pass_count": sum(item["neighbor_stability_passed"] for item in finals),
            "leave_one_event_out_pass_count": sum(item["leave_one_event_out_passed"] for item in finals),
            "runtime_confirmation_candidate_count": sum(
                item["runtime_confirmation_candidate"] for item in finals
            ),
            "offline_truth_qualified_success_count": sum(
                item["offline_truth_qualified_success"] for item in finals
            ),
        }

    return {
        "scope": "conversational_minute_rectification_entry_smoke_replay",
        "benchmark_id": manifest["benchmark_id"],
        "status": "diagnostics_available",
        "cases": case_results,
        "summary": {
            "oracle_structured": summary("final_oracle_structured"),
            "simulated_current_transport_filter": summary(
                "final_simulated_current_transport_filter"
            ),
        },
        "excluded_from_holdout": True,
        "may_open_release_gate": False,
        "boundary": (
            "This is a structured-event smoke replay. TypeScript tests separately assert the "
            "fixture's current extractor behavior; the Python filter is not an end-to-end product "
            "transport. Cases below five scoreable events cannot evaluate Skill-level convergence."
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.manifest)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
