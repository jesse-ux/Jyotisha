#!/usr/bin/env python3
"""Append one independently reviewed case to a non-production v4 intake queue."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from scripts.minute_rectification_holdout_validator import case_errors
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from minute_rectification_holdout_validator import case_errors

INTAKE_SCHEMA_VERSION = "minute-rectification-holdout-v4-intake"
DEFAULT_INTAKE = (
    Path(__file__).resolve().parents[1]
    / "references"
    / "real_case_calibration"
    / "minute_rectification_holdout_v4_intake.json"
)


def append_case(path: Path, case: dict[str, Any]) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != INTAKE_SCHEMA_VERSION:
        return {"appended": False, "errors": ["intake_schema_required"]}
    gate = data.get("minimum_gate") if isinstance(data.get("minimum_gate"), dict) else {}
    cases = data.get("cases") if isinstance(data.get("cases"), list) else []
    case_id = str(case.get("case_id") or "").strip()
    if not case_id:
        return {"appended": False, "errors": ["missing_case_id"]}
    if any(isinstance(existing, dict) and existing.get("case_id") == case_id for existing in cases):
        return {"appended": False, "errors": ["duplicate_case_id"]}
    errors = case_errors(case, gate, require_review_safeguards=True)
    if errors:
        return {"appended": False, "errors": errors}

    cases.append({**case, "ingested_at": datetime.now(UTC).isoformat().replace("+00:00", "Z")})
    data["cases"] = cases
    data["status"] = "collecting_independently_reviewed_cases"
    data["production_tuning_allowed"] = False
    data["verified_minute_claim_allowed"] = False
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "appended": True,
        "errors": [],
        "case_count": len(cases),
        "verified_minute_claim_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", type=Path, default=DEFAULT_INTAKE)
    parser.add_argument("--case-json", required=True)
    args = parser.parse_args()
    result = append_case(args.manifest, json.loads(args.case_json))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["appended"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
