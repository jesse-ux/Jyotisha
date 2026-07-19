#!/usr/bin/env python3
"""Create a blank independent day-level timing holdout annotation template."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


TEMPLATE = {
    "case_id": "",
    "subject": {
        "name": "",
        "public_profile_url": "",
        "birth_time_rating": "AA/A only preferred",
    },
    "domain": "career|marriage|wealth|health",
    "label": "target_event|no_target_event",
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD",
    "event_description": "",
    "event_absent_assertion": "",
    "source_url": "https://",
    "source_quote_or_summary": "",
    "adjudicator": "",
    "time_uncertainty_days": 0,
    "independent_human_reviewed": True,
    "frozen_before_scoring": True,
    "source_path": "",
    "notes": "",
}


def build_template() -> dict:
    return {
        "template_type": "day_level_holdout_annotation_v3",
        "instructions": [
            "Use target_event for known dated events.",
            "Use no_target_event only when a public source supports that the target event did not occur in the interval.",
            "Do not use old control dates or rows observed before preregistration for tuning.",
            "Freeze labels before running timing_ranker_blind_eval.py.",
        ],
        "annotation": TEMPLATE,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    text = json.dumps(build_template(), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
