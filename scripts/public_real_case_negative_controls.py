#!/usr/bin/env python3
"""Rank known public event dates against deterministic non-target control dates."""

from __future__ import annotations

import argparse
import copy
import json
import statistics
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable

from scripts.public_real_case_benchmark import clear_engine_cache, replay_case

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OFFSETS = (-120, -90, -60, -30, 30, 60, 90, 120)


def parse_offsets(raw: str) -> tuple[int, ...]:
    return tuple(dict.fromkeys(value for value in (int(item.strip()) for item in raw.split(",")) if value != 0))


def generate_control_dates(event_date: str, offsets: Iterable[int] = DEFAULT_OFFSETS) -> list[str]:
    target = date.fromisoformat(event_date)
    return [(target + timedelta(days=int(offset))).isoformat() for offset in offsets if int(offset) != 0]


def rank_positive_against_controls(positive_score: int, control_scores: list[int]) -> dict[str, Any]:
    rank = 1 + sum(score >= positive_score for score in control_scores)
    max_control = max(control_scores) if control_scores else None
    return {
        "positive_score": positive_score,
        "positive_rank": rank,
        "candidate_count": len(control_scores) + 1,
        "reciprocal_rank": 1 / rank,
        "top_1": rank == 1,
        "top_3": rank <= 3,
        "max_control_score": max_control,
        "score_margin": positive_score - max_control if max_control is not None else None,
    }


def summarize_negative_control_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    controls = [control for row in rows for control in row.get("controls") or [] if not control.get("blocked")]
    rankings = [row["ranking"] for row in rows if row.get("ranking")]
    margins = [item["score_margin"] for item in rankings if item["score_margin"] is not None]
    control_activation_rate = sum((control.get("score") or 0) >= 4 for control in controls) / len(controls) if controls else None
    control_strong_activation_rate = sum((control.get("score") or 0) >= 7 for control in controls) / len(controls) if controls else None
    positive_top_1_rate = sum(item["top_1"] for item in rankings) / len(rankings) if rankings else None
    positive_top_3_rate = sum(item["top_3"] for item in rankings) / len(rankings) if rankings else None
    specificity_proxy = 1 - control_activation_rate if control_activation_rate is not None else None
    strong_specificity_proxy = 1 - control_strong_activation_rate if control_strong_activation_rate is not None else None
    timing_precision_pass = (
        positive_top_3_rate is not None
        and specificity_proxy is not None
        and positive_top_3_rate >= 0.6
        and specificity_proxy >= 0.6
    )
    return {
        "case_count": len(rows),
        "ranked_case_count": len(rankings),
        "control_date_count": len(controls),
        "control_activation_rate": control_activation_rate,
        "control_strong_activation_rate": control_strong_activation_rate,
        "specificity_proxy": specificity_proxy,
        "strong_specificity_proxy": strong_specificity_proxy,
        "positive_top_1_rate": positive_top_1_rate,
        "positive_top_3_rate": positive_top_3_rate,
        "mean_reciprocal_rank": statistics.mean(item["reciprocal_rank"] for item in rankings) if rankings else None,
        "mean_score_margin": statistics.mean(margins) if margins else None,
        "timing_precision_gate": {
            "status": "pass" if timing_precision_pass else "blocked",
            "positive_top_3_minimum": 0.6,
            "specificity_proxy_minimum": 0.6,
            "reason": None if timing_precision_pass else "positive_dates_do_not_rank_above_controls_with_required_specificity",
        },
        "balanced_accuracy": None,
        "balanced_accuracy_blocked_reason": "controls_are_non_target_dates_not_independently_adjudicated_all-domain_non_events",
    }


def build_report(manifest: dict[str, Any], offsets: Iterable[int] = DEFAULT_OFFSETS) -> dict[str, Any]:
    clear_engine_cache()
    rows = []
    for case in manifest.get("cases") or []:
        event = case["event_outcomes"][0]
        positive = replay_case(case, rule_version="v2_1")
        controls = []
        for control_date in generate_control_dates(event["event_date"], offsets):
            control_case = copy.deepcopy(case)
            control_event = control_case["event_outcomes"][0]
            control_event["event_date"] = control_date
            control_event["outcome"] = f"non_target_control_date_for:{event['outcome']}"
            result = replay_case(control_case, rule_version="v2_1")
            controls.append({
                "date": control_date,
                "score": result.get("score"),
                "result_class": result.get("result_class"),
                "blocked": bool(result.get("blocked")),
                "blocked_reason": result.get("blocked_reason"),
            })
        control_scores = [int(item["score"]) for item in controls if not item["blocked"] and item.get("score") is not None]
        ranking = None
        if not positive.get("blocked") and positive.get("score") is not None:
            ranking = rank_positive_against_controls(int(positive["score"]), control_scores)
        rows.append({
            "case_id": case["case_id"],
            "name": case["subject"]["name"],
            "domain": event["domain"],
            "positive_date": event["event_date"],
            "positive": positive,
            "controls": controls,
            "ranking": ranking,
        })
    return {
        "benchmark_id": "public_real_case_negative_control_pilot_2026_07_11",
        "rule_version": "v2_1",
        "control_offsets_days": list(offsets),
        "summary": summarize_negative_control_rows(rows),
        "boundary": (
            "Controls are dates without the exact recorded target outcome. They may contain other life events. "
            "This pilot measures date ranking and false domain activation, not scientific causal validity."
        ),
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="references/real_case_calibration/replay_manifest_probe3_v2.json")
    parser.add_argument("--output")
    parser.add_argument("--offsets", default=",".join(str(value) for value in DEFAULT_OFFSETS))
    args = parser.parse_args()
    manifest = json.loads((ROOT / args.manifest).read_text(encoding="utf-8"))
    report = build_report(manifest, parse_offsets(args.offsets))
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        output_path = ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
