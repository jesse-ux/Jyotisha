#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate structured real-case outcome replay manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

CASE_REQUIRED_FIELDS = {
    "case_id",
    "subject",
    "source",
    "chart_signature",
    "event_outcomes",
    "similarity",
    "replay",
}
SOURCE_REQUIRED_FIELDS = {"url", "source_grade", "license_or_quote_boundary"}
SUBJECT_REQUIRED_FIELDS = {
    "name", "year", "month", "day", "hour", "minute", "lat", "lon", "tz",
    "node_mode", "birth_source",
}
BIRTH_SOURCE_REQUIRED_FIELDS = {
    "url", "source_grade", "time_accuracy_rating", "evidence_basis",
}
EVENT_REQUIRED_FIELDS = {
    "event_type", "event_date", "domain", "expected_label", "outcome", "source",
}
EVENT_SOURCE_REQUIRED_FIELDS = {"url", "source_grade"}
ALLOWED_BIRTH_TIME_RATINGS = {"A", "AA"}


def _missing(mapping: dict[str, Any], required: set[str]) -> list[str]:
    return sorted(name for name in required if name not in mapping)


def _case_errors(case: Any, index: int) -> list[dict[str, Any]]:
    if not isinstance(case, dict):
        return [{"case_index": index, "field": "case", "error": "not_object"}]

    errors: list[dict[str, Any]] = []
    for field in _missing(case, CASE_REQUIRED_FIELDS):
        errors.append({"case_id": case.get("case_id"), "field": field, "error": "missing"})

    source = case.get("source")
    if isinstance(source, dict):
        for field in _missing(source, SOURCE_REQUIRED_FIELDS):
            errors.append({"case_id": case.get("case_id"), "field": f"source.{field}", "error": "missing"})
    elif "source" in case:
        errors.append({"case_id": case.get("case_id"), "field": "source", "error": "not_object"})

    subject = case.get("subject")
    if isinstance(subject, dict):
        for field in _missing(subject, SUBJECT_REQUIRED_FIELDS):
            errors.append({"case_id": case.get("case_id"), "field": f"subject.{field}", "error": "missing"})
        birth_source = subject.get("birth_source")
        if isinstance(birth_source, dict):
            for field in _missing(birth_source, BIRTH_SOURCE_REQUIRED_FIELDS):
                errors.append({"case_id": case.get("case_id"), "field": f"subject.birth_source.{field}", "error": "missing"})
            rating = birth_source.get("time_accuracy_rating")
            if rating not in ALLOWED_BIRTH_TIME_RATINGS:
                errors.append({
                    "case_id": case.get("case_id"),
                    "field": "subject.birth_source.time_accuracy_rating",
                    "error": "birth_time_rating_below_A",
                })
        elif "birth_source" in subject:
            errors.append({"case_id": case.get("case_id"), "field": "subject.birth_source", "error": "not_object"})
    elif "subject" in case:
        errors.append({"case_id": case.get("case_id"), "field": "subject", "error": "not_object"})

    events = case.get("event_outcomes")
    if isinstance(events, list):
        if not events:
            errors.append({"case_id": case.get("case_id"), "field": "event_outcomes", "error": "empty"})
        for event_index, event in enumerate(events):
            if not isinstance(event, dict):
                errors.append({"case_id": case.get("case_id"), "field": f"event_outcomes[{event_index}]", "error": "not_object"})
                continue
            for field in _missing(event, EVENT_REQUIRED_FIELDS):
                errors.append({"case_id": case.get("case_id"), "field": f"event_outcomes[{event_index}].{field}", "error": "missing"})
            event_source = event.get("source")
            if isinstance(event_source, dict):
                for field in _missing(event_source, EVENT_SOURCE_REQUIRED_FIELDS):
                    errors.append({"case_id": case.get("case_id"), "field": f"event_outcomes[{event_index}].source.{field}", "error": "missing"})
            elif "source" in event:
                errors.append({"case_id": case.get("case_id"), "field": f"event_outcomes[{event_index}].source", "error": "not_object"})
    elif "event_outcomes" in case:
        errors.append({"case_id": case.get("case_id"), "field": "event_outcomes", "error": "not_array"})

    return errors


def validate_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cases = manifest.get("cases")
    if not isinstance(cases, list):
        return {
            "status": "blocked",
            "manifest_path": str(manifest_path),
            "case_count": 0,
            "replay_ready_count": 0,
            "blocked_reason": "cases_not_array",
            "errors": [{"field": "cases", "error": "not_array"}],
        }

    errors: list[dict[str, Any]] = []
    replay_ready_count = 0
    domain_counts: dict[str, int] = {}
    birth_time_ratings: dict[str, int] = {}
    for index, case in enumerate(cases):
        case_errors = _case_errors(case, index)
        errors.extend(case_errors)
        replay = case.get("replay") if isinstance(case, dict) else {}
        if not case_errors and isinstance(replay, dict) and replay.get("outcome_replay_status") == "replayed":
            replay_ready_count += 1
        if isinstance(case, dict):
            subject = case.get("subject") or {}
            birth_source = subject.get("birth_source") if isinstance(subject, dict) else {}
            rating = birth_source.get("time_accuracy_rating") if isinstance(birth_source, dict) else None
            if isinstance(rating, str):
                birth_time_ratings[rating] = birth_time_ratings.get(rating, 0) + 1
            for event in case.get("event_outcomes") or []:
                if isinstance(event, dict) and isinstance(event.get("domain"), str):
                    domain = event["domain"]
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1

    if errors:
        status = "invalid"
        blocked_reason = "case_contract_errors"
    elif not cases:
        status = "blocked"
        blocked_reason = manifest.get("blocked_reason") or "no_structured_outcome_replay_cases_imported"
    elif replay_ready_count == len(cases):
        status = "pass"
        blocked_reason = None
    else:
        status = "partial"
        blocked_reason = "some_cases_not_replayed"

    return {
        "status": status,
        "manifest_path": str(manifest_path),
        "schema_version": manifest.get("schema_version"),
        "case_schema": manifest.get("case_schema"),
        "case_count": len(cases),
        "replay_ready_count": replay_ready_count,
        "domain_counts": dict(sorted(domain_counts.items())),
        "birth_time_ratings": dict(sorted(birth_time_ratings.items())),
        "blocked_reason": blocked_reason,
        "errors": errors,
        "runtime_boundary": manifest.get("runtime_boundary", ""),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", default="references/real_case_calibration/replay_manifest.json")
    args = parser.parse_args(argv)
    print(json.dumps(validate_manifest(args.manifest), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
