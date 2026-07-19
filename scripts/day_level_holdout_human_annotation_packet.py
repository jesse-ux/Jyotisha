#!/usr/bin/env python3
"""Create human-review annotation packet from pilot source windows.

The packet is intentionally not a frozen holdout. Humans must fill final labels.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _stable_id(row: dict, index: int) -> str:
    base = f"{row['subject_id']}|{row['label_candidate']}|{row['start']}|{row['end']}|{index}"
    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()[:10].upper()
    return f"DLH-PILOT-{index:03d}-{digest}"


def build_packet(report_path: Path) -> dict:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    annotations = []
    for index, row in enumerate(report["windows"], start=1):
        annotations.append(
            {
                "annotation_id": _stable_id(row, index),
                "subject_id": row["subject_id"],
                "subject_name": row["name"],
                "domain": row["domain"],
                "start": row["start"],
                "end": row["end"],
                "candidate_label": row["label_candidate"],
                "final_label": None,
                "event_description": row["event_description"],
                "event_absent_assertion": row["event_absent_assertion"],
                "source_urls": row["source_urls"],
                "source_quote_or_summary": "",
                "adjudicator": "",
                "independent_human_reviewed": False,
                "frozen_before_scoring": False,
                "review_decision": "pending",
                "time_uncertainty_days": None,
                "notes": "",
            }
        )
    positive = sum(1 for row in annotations if row["candidate_label"] == "target_event")
    negative = sum(1 for row in annotations if row["candidate_label"] == "no_target_event")
    return {
        "scope": "day_level_holdout_human_annotation_packet",
        "created_at": "2026-07-19",
        "source_report": str(report_path),
        "status": "awaiting_independent_human_adjudication",
        "ready_for_blind_eval": False,
        "production_tuning_allowed": False,
        "truth_boundary": "This packet is for human labeling only. It must not be scored until final_label, adjudicator, independent_human_reviewed, and frozen_before_scoring are complete.",
        "instructions": [
            "Do not use candidate_label as final_label.",
            "For target_event, verify the event date from public sources.",
            "For no_target_event, verify absence in the interval from public sources.",
            "Freeze all labels before timing_ranker_blind_eval.py is run.",
            "Do not use existing observed control dates for tuning.",
        ],
        "summary": {
            "annotation_count": len(annotations),
            "final_label_count": sum(1 for row in annotations if row["final_label"]),
            "frozen_count": sum(1 for row in annotations if row["frozen_before_scoring"]),
            "positive_candidate_count": positive,
            "negative_candidate_count": negative,
        },
        "annotations": annotations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-report",
        type=Path,
        default=Path("references/real_case_calibration/day_level_holdout_v3_pilot_source_queue_report_2026_07_19.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    packet = build_packet(args.source_report)
    text = json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
