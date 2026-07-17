#!/usr/bin/env python3
"""Replay Western timing geometry for an existing public real-case manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from western_timing_engine import calculate_parans_status, calculate_secondary_progressions
except ImportError:
    from scripts.western_timing_engine import calculate_parans_status, calculate_secondary_progressions


DEFAULT_MANIFEST = Path("references/real_case_calibration/replay_manifest.json")


def build_case(case_id: str, manifest_path: Path = DEFAULT_MANIFEST) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    case = next((row for row in manifest["cases"] if row["case_id"] == case_id), None)
    if case is None:
        return {"status": "blocked", "reason": "case_id_not_found", "case_id": case_id}
    event = case["event_outcomes"][0]
    subject = case["subject"]
    birth = {
        "year": subject["year"], "month": subject["month"], "day": subject["day"],
        "hour": subject["hour"], "minute": subject["minute"], "second": 0,
        "latitude": subject["lat"], "longitude": subject["lon"], "timezone": subject["tz"],
    }
    progressions = calculate_secondary_progressions(target_date=event["event_date"], **birth)
    parans = calculate_parans_status(target_date=event["event_date"], **birth)
    return {
        "scope": "western_real_case_calibration",
        "status": "calculated_not_predictive_validation",
        "case_id": case_id,
        "subject": subject["name"],
        "event": {
            "date": event["event_date"],
            "type": event["event_type"],
            "source": event["source"],
        },
        "birth_source": subject["birth_source"],
        "layers": {
            "secondary_progressions": progressions,
            "parans": parans,
        },
        "summary": {
            "progressed_aspect_count": len(progressions["aspects"]),
            "paran_event_count": parans["event_count"],
            "paran_pair_count": len(parans["paran_pairs_within_4_minutes"]),
        },
        "boundary": "Known-event geometry replay only. One positive case cannot establish specificity, false-positive rate, or predictive accuracy.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", default="jobs_iphone_2007")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_case(args.case_id, args.manifest)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
