#!/usr/bin/env python3
"""Expand pilot day-level holdout source candidates into unscored windows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_report(queue_path: Path) -> dict:
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    windows = []
    for subject in queue["subjects"]:
        positive = subject["candidate_positive_event"]
        windows.append(
            {
                "subject_id": subject["subject_id"],
                "name": subject["name"],
                "domain": subject["domain"],
                "label_candidate": positive["label"],
                "start": positive["start"],
                "end": positive["end"],
                "event_description": positive["event_description"],
                "event_absent_assertion": "",
                "source_urls": positive.get("source_urls", []),
                "claim_status": "candidate_not_label",
                "required_next_step": "independent_human_adjudication",
                "scoring_status": "blocked_not_frozen",
            }
        )
        for item in subject["candidate_negative_windows"]:
            windows.append(
                {
                    "subject_id": subject["subject_id"],
                    "name": subject["name"],
                    "domain": subject["domain"],
                    "label_candidate": "no_target_event",
                    "start": item["start"],
                    "end": item["end"],
                    "event_description": "",
                    "event_absent_assertion": item["event_absent_assertion"],
                    "source_urls": positive.get("source_urls", []),
                    "claim_status": "candidate_not_label",
                    "required_next_step": "independent_human_adjudication",
                    "scoring_status": "blocked_not_frozen",
                }
            )

    positive_count = sum(1 for row in windows if row["label_candidate"] == "target_event")
    negative_count = sum(1 for row in windows if row["label_candidate"] == "no_target_event")
    return {
        "scope": "day_level_holdout_pilot_source_queue_report",
        "source_queue": str(queue_path),
        "status": "awaiting_independent_human_labels",
        "production_tuning_allowed": False,
        "blind_scoring_allowed": False,
        "truth_boundary": queue["truth_boundary"],
        "summary": {
            "subject_count": len(queue["subjects"]),
            "window_count": len(windows),
            "positive_candidate_count": positive_count,
            "negative_candidate_count": negative_count,
            "ready_annotation_count": 0,
            "blocked_annotation_count": len(windows),
        },
        "windows": windows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--queue",
        type=Path,
        default=Path("references/real_case_calibration/day_level_holdout_v3_pilot_source_queue_2026_07_19.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report(args.queue)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
