#!/usr/bin/env python3
"""Append one independent day-level holdout annotation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--label", choices=["target_event", "no_target_event"], required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--adjudicator", required=True)
    parser.add_argument("--event-description", default="")
    parser.add_argument("--event-absent-assertion", default="")
    parser.add_argument("--source-quote-or-summary", default="")
    parser.add_argument("--time-uncertainty-days", type=int, default=0)
    args = parser.parse_args()

    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    row = {
        "case_id": args.case_id,
        "domain": args.domain,
        "label": args.label,
        "start": args.start,
        "end": args.end,
        "event_description": args.event_description,
        "event_absent_assertion": args.event_absent_assertion,
        "source_url": args.source_url,
        "source_quote_or_summary": args.source_quote_or_summary,
        "adjudicator": args.adjudicator,
        "time_uncertainty_days": args.time_uncertainty_days,
        "independent_human_reviewed": True,
        "frozen_before_scoring": True,
        "source_path": "",
        "notes": "",
    }
    data.setdefault("annotations", []).append(row)
    data["status"] = "awaiting_independent_labels"
    data["production_tuning_allowed"] = False
    args.manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "appended", "annotation_count": len(data["annotations"]), "production_tuning_allowed": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
