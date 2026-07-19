#!/usr/bin/env python3
"""Validate the public, minute-specific rectification holdout gate."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "references" / "real_case_calibration" / "minute_rectification_holdout_v1.json"


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
        birth = case.get("birth_source") if isinstance(case.get("birth_source"), dict) else {}
        events = case.get("events") if isinstance(case.get("events"), list) else []
        negatives = case.get("negative_minutes") if isinstance(case.get("negative_minutes"), list) else []
        required = birth.get("time_accuracy_rating") == "AA" and bool(birth.get("url"))
        required = required and len(events) >= int(gate.get("events_per_case", 3))
        required = required and len(negatives) >= int(gate.get("negative_minutes_per_case", 4))
        if required:
            valid_cases += 1
        else:
            invalid.append(str(case.get("case_id") or "unnamed_case"))
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
