#!/usr/bin/env python3
"""Validate public cases that may be used for development but never for holdout claims."""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.minute_rectification_holdout_validator import ROOT, _case_errors

DEFAULT_MANIFEST = ROOT / "references" / "real_case_calibration" / "minute_rectification_development_v1.json"


def validate(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    gate = manifest.get("minimum_case_contract") or {}
    invalid: list[dict[str, Any]] = []
    valid = 0
    seen: set[str] = set()
    for raw_case in manifest.get("cases", []):
        case = deepcopy(raw_case) if isinstance(raw_case, dict) else raw_case
        errors: list[str] = []
        if isinstance(case, dict):
            if case.get("development_partition") != "tuning_and_diagnostics":
                errors.append("case_not_in_development_partition")
            if case.get("allowed_for_tuning") is not True:
                errors.append("case_not_allowed_for_tuning")
            if case.get("excluded_from_holdout") is not True:
                errors.append("case_not_excluded_from_holdout")
            case["holdout_partition"] = "sealed_evaluation"
            case["excluded_from_tuning"] = True
        errors.extend(_case_errors(case, gate))
        errors = [
            error for error in errors
            if error not in {"case_not_in_sealed_evaluation_partition", "case_not_excluded_from_tuning"}
        ]
        case_id = raw_case.get("case_id") if isinstance(raw_case, dict) else "non_object_case"
        if case_id in seen:
            errors.append("duplicate_case_id")
        if isinstance(case_id, str):
            seen.add(case_id)
        if errors:
            invalid.append({"case_id": case_id, "errors": sorted(set(errors))})
        else:
            valid += 1
    schema_valid = manifest.get("schema_version") == "minute-rectification-development-v1"
    return {
        "scope": "minute_rectification_development_validation",
        "status": "ready_for_development" if schema_valid and not invalid and valid else "blocked",
        "valid_development_cases": valid,
        "invalid_cases": invalid,
        "excluded_from_holdout": True,
        "may_open_release_gate": False,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, indent=2, sort_keys=True))
