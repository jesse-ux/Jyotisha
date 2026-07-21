#!/usr/bin/env python3
"""Audit reusable public AA cases before adding them to the minute holdout."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES = (
    ROOT / "references" / "real_case_calibration" / "replay_manifest.json",
    ROOT / "references" / "real_case_calibration" / "replay_manifest_holdout_v2.json",
    ROOT / "references" / "real_case_calibration" / "replay_manifest_probe3_v2.json",
    ROOT / "references" / "real_case_calibration" / "public_context_manifest.json",
)


def _events(case: dict[str, Any]) -> list[dict[str, Any]]:
    raw = case.get("events") if isinstance(case.get("events"), list) else case.get("event_outcomes")
    return [event for event in raw or [] if isinstance(event, dict)]


def build_source_audit(paths: list[Path] | tuple[Path, ...] = DEFAULT_SOURCES) -> dict[str, Any]:
    entries: dict[str, dict[str, Any]] = {}
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        for case in data.get("cases", []):
            if not isinstance(case, dict):
                continue
            subject = case.get("subject") if isinstance(case.get("subject"), dict) else case
            birth = subject.get("birth_source") if isinstance(subject.get("birth_source"), dict) else {}
            source_url = str(birth.get("url") or "")
            if birth.get("time_accuracy_rating") != "AA" or not source_url:
                continue
            name = str(subject.get("name") or case.get("case_id") or "unnamed")
            entry = entries.setdefault(source_url, {
                "subject": name,
                "birth_source_url": source_url,
                "case_ids": [],
                "dated_event_dates": set(),
            })
            entry["case_ids"].append(str(case.get("case_id") or name))
            for event in _events(case):
                date = str(event.get("event_date") or event.get("date") or "")
                if len(date) == 10:
                    entry["dated_event_dates"].add(date)
    cases = []
    for entry in entries.values():
        event_count = len(entry["dated_event_dates"])
        cases.append({
            "subject": entry["subject"],
            "birth_source_url": entry["birth_source_url"],
            "case_ids": sorted(entry["case_ids"]),
            "existing_dated_event_count": event_count,
            "additional_dated_events_required": max(0, 3 - event_count),
            "negative_controls_required": 4,
        })
    cases.sort(key=lambda case: (case["additional_dated_events_required"], case["subject"]))
    return {
        "scope": "minute_rectification_public_aa_source_audit",
        "public_aa_case_count": len(cases),
        "minimum_public_aa_cases": 20,
        "additional_public_aa_cases_required": max(0, 20 - len(cases)),
        "cases": cases,
        "boundary": "Source discovery is not holdout validation. Cases require independent dated events and committed two-sided false-minute controls before blind replay.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="*", type=Path, default=list(DEFAULT_SOURCES))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_source_audit(args.sources)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
