#!/usr/bin/env python3
"""Evaluate frozen day/month timing candidates against independent holdout labels."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.day_level_holdout_validator import validate


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _key(row: dict) -> tuple[str, str, str]:
    return (str(row.get("case_id") or ""), str(row.get("start") or ""), str(row.get("end") or ""))


def evaluate(manifest_path: Path, candidates_path: Path) -> dict:
    validation = validate(manifest_path)
    manifest = _load(manifest_path)
    candidates = sorted(
        (_load(candidates_path).get("candidate_windows") or []),
        key=lambda row: float(row.get("score") or 0),
        reverse=True,
    )
    labels = {_key(row): row.get("label") for row in manifest.get("annotations") or []}
    ranked = [{**row, "rank": index + 1, "label": labels.get(_key(row))} for index, row in enumerate(candidates)]
    positives = [row for row in ranked if row.get("label") == "target_event"]
    negatives = [row for row in ranked if row.get("label") == "no_target_event"]
    top_3_positive = sum(1 for row in positives if row["rank"] <= 3)
    positive_top_3_rate = top_3_positive / len(positives) if positives else 0.0
    min_positive_score = min((float(row.get("score") or 0) for row in positives), default=0.0)
    false_positive_negatives = sum(1 for row in negatives if float(row.get("score") or 0) >= min_positive_score)
    specificity = 1 - (false_positive_negatives / len(negatives)) if negatives else 0.0
    gate = manifest.get("frozen_gate") or {}
    blockers = []
    if validation["status"] != "ready_for_blind_replay":
        blockers.append("holdout_not_ready")
    if positive_top_3_rate < gate.get("minimum_positive_top_3_rate", 1):
        blockers.append("positive_top_3_rate_below_gate")
    if specificity < gate.get("minimum_specificity", 1):
        blockers.append("specificity_below_gate")
    passed = not blockers
    return {
        "scope": "timing_ranker_blind_eval",
        "status": "pass" if passed else "blocked",
        "claim_status": "calibrated_day_level" if passed else "exploratory_unvalidated",
        "production_tuning_allowed": bool(passed),
        "positive_count": len(positives),
        "negative_count": len(negatives),
        "positive_top_3_rate": positive_top_3_rate,
        "specificity": specificity,
        "blockers": blockers,
        "validation": validation,
        "ranked_windows": ranked,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("candidates", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.manifest, args.candidates), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
