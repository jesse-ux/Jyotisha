#!/usr/bin/env python3
"""Validate the public, minute-specific rectification holdout gate."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "references" / "real_case_calibration" / "minute_rectification_holdout_v1.json"


def _valid_events(events: list[Any], *, minimum: int, birth_url: str) -> bool:
    if len(events) < minimum:
        return False
    for event in events:
        if not isinstance(event, dict):
            return False
        source = event.get("source") if isinstance(event.get("source"), dict) else {}
        date = str(event.get("event_date") or "")
        # Month/year-only biographies cannot distinguish neighbouring minutes.
        if len(date) != 10 or not source.get("url") or str(source["url"]) == birth_url:
            return False
    return True


def _valid_negative_controls(controls: list[Any], *, minimum: int) -> bool:
    if len(controls) < minimum:
        return False
    offsets: list[int] = []
    commitments: set[str] = set()
    for control in controls:
        if not isinstance(control, dict):
            return False
        offset = control.get("offset_minutes")
        commitment = str(control.get("commitment_hash") or "")
        if not isinstance(offset, int) or offset == 0 or len(commitment) != 64:
            return False
        if any(key in control for key in ("candidate_minute", "published_minute", "birth_time")):
            return False
        offsets.append(offset)
        commitments.add(commitment)
    return any(offset < 0 for offset in offsets) and any(offset > 0 for offset in offsets) and len(set(offsets)) == len(offsets) and len(commitments) == len(controls)


def case_error(case: dict[str, Any], gate: dict[str, Any]) -> str | None:
    """Return the one blocking reason for a prospective minute-holdout case."""
    birth = case.get("birth_source") if isinstance(case.get("birth_source"), dict) else {}
    events = case.get("events") if isinstance(case.get("events"), list) else []
    negatives = case.get("negative_minutes") if isinstance(case.get("negative_minutes"), list) else []
    if not str(case.get("adjudicator") or "").strip() or case.get("independent_human_reviewed") is not True or case.get("frozen_before_scoring") is not True:
        return "independent_review_invalid"
    if birth.get("time_accuracy_rating") != "AA" or not birth.get("url"):
        return "birth_source_invalid"
    if not _valid_events(events, minimum=int(gate.get("events_per_case", 3)), birth_url=str(birth["url"])):
        return "events_invalid"
    if not _valid_negative_controls(negatives, minimum=int(gate.get("negative_minutes_per_case", 4))):
        return "negative_controls_invalid"
    return None


def validate(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    gate = manifest.get("minimum_gate") if isinstance(manifest.get("minimum_gate"), dict) else {}
    cases = manifest.get("cases") if isinstance(manifest.get("cases"), list) else []
    valid_cases = 0
    invalid: list[str] = []
    for case in cases:
        if not isinstance(case, dict):
            invalid.append("non_object_case")
            continue
        case_id = str(case.get("case_id") or "unnamed_case")
        error = case_error(case, gate)
        if error:
            invalid.append(f"{case_id}:{error}")
        else:
            valid_cases += 1
    needed = int(gate.get("public_aa_cases", 20))
    status = "ready_for_blind_replay" if valid_cases >= needed else "blocked_awaiting_public_aa_cases"
    return {
        "scope": "minute_rectification_holdout_validation",
        "benchmark_id": manifest.get("benchmark_id"),
        "status": status,
        "valid_public_aa_cases": valid_cases,
        "minimum_public_aa_cases": needed,
        "invalid_cases": invalid,
        "verified_minute_claim_allowed": False,
        "boundary": manifest.get("boundary"),
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, indent=2, sort_keys=True))
