#!/usr/bin/env python3
"""Audit reusable public AA cases before admitting them to a minute holdout."""

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


def _birth_source(subject: dict[str, Any]) -> dict[str, Any]:
    if isinstance(subject.get("birth_source"), dict):
        return subject["birth_source"]
    birth = subject.get("birth") if isinstance(subject.get("birth"), dict) else {}
    return birth.get("source") if isinstance(birth.get("source"), dict) else {}


def _is_aa(source: dict[str, Any]) -> bool:
    return source.get("time_accuracy_rating") == "AA" or source.get("rodden_rating") == "AA"


def build_source_audit(paths: list[Path] | tuple[Path, ...] = DEFAULT_SOURCES) -> dict[str, Any]:
    entries: dict[str, dict[str, Any]] = {}
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        for case in data.get("cases", []):
            if not isinstance(case, dict):
                continue
            subject = case.get("subject") if isinstance(case.get("subject"), dict) else case
            source = _birth_source(subject)
            source_url = str(source.get("url") or "")
            if not _is_aa(source) or not source_url:
                continue
            label = str(subject.get("name") or subject.get("subject_label") or case.get("case_id") or "unnamed")
            entry = entries.setdefault(source_url, {
                "subject": label,
                "birth_source_url": source_url,
                "case_ids": [],
                "day_precision_event_dates": set(),
            })
            entry["case_ids"].append(str(case.get("case_id") or label))
            for event in _events(case):
                event_date = str(event.get("event_date") or event.get("date") or "")
                if len(event_date) == 10:
                    entry["day_precision_event_dates"].add(event_date)

    cases = []
    for entry in entries.values():
        event_count = len(entry["day_precision_event_dates"])
        cases.append({
            "subject": entry["subject"],
            "birth_source_url": entry["birth_source_url"],
            "case_ids": sorted(set(entry["case_ids"])),
            "existing_day_precision_event_count": event_count,
            "additional_day_precision_events_required": max(0, 3 - event_count),
            "review_and_commitment_controls_required": True,
        })
    cases.sort(key=lambda case: (case["additional_day_precision_events_required"], case["subject"]))
    return {
        "scope": "minute_rectification_public_aa_source_audit",
        "public_aa_case_count": len(cases),
        "minimum_public_aa_cases": 20,
        "additional_public_aa_cases_required": max(0, 20 - len(cases)),
        "cases": cases,
        "production_tuning_allowed": False,
        "boundary": (
            "Source discovery is not holdout validation. Every promoted case still requires "
            "independent review, day-precision events and committed false-minute controls."
        ),
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
