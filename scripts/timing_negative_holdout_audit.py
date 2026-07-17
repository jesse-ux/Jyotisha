#!/usr/bin/env python3
"""Audit whether candidate sources can promote day/month timing claims."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


DEFAULT_SOURCES = [
    {
        "name": "Wikidata/EventKG/BiographyNet derived timelines",
        "positive_events": True,
        "explicit_non_event_intervals": False,
        "independent_human_reviewed": False,
        "observed_before_preregistration": True,
        "notes": "Useful for positive event dates; missing events are not non-event labels.",
    },
    {
        "name": "existing 40 control dates",
        "positive_events": False,
        "explicit_non_event_intervals": True,
        "independent_human_reviewed": False,
        "observed_before_preregistration": True,
        "notes": "May remain diagnostic only; cannot tune or promote claims.",
    },
]


def evaluate_source(source: dict) -> dict:
    blockers = []
    if not source.get("explicit_non_event_intervals"):
        blockers.append("missing_explicit_non_event_intervals")
    if not source.get("independent_human_reviewed"):
        blockers.append("not_independently_human_reviewed")
    if source.get("observed_before_preregistration"):
        blockers.append("observed_before_preregistration")
    return {
        **source,
        "usable_for_promotion": not blockers,
        "blockers": blockers,
    }


def build_report(sources: list[dict] | None = None) -> dict:
    rows = [evaluate_source(source) for source in (sources or DEFAULT_SOURCES)]
    usable = [row for row in rows if row["usable_for_promotion"]]
    return {
        "scope": "timing_negative_holdout_source_audit",
        "claim_status": "exploratory_unvalidated" if not usable else "ready_for_blind_holdout",
        "timing_precision": "candidate_day_window",
        "production_tuning_allowed": False if not usable else True,
        "candidate_window_policy": (
            "Return ranked candidate days/months with signals and confidence caps; "
            "do not label them verified predictions until blind negative holdout passes."
        ),
        "required_label_contract": {
            "explicit_non_event_intervals": True,
            "independent_human_reviewed": True,
            "unobserved_before_preregistration": True,
            "positive_and_negative_split_locked_before_scoring": True,
        },
        "sources": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-json", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    sources = None
    if args.source_json:
        sources = json.loads(args.source_json.read_text(encoding="utf-8"))["sources"]
    report = build_report(sources)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
