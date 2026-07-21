#!/usr/bin/env python3
"""Append one independently reviewed, frozen minute-rectification holdout case."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.minute_rectification_holdout_validator import case_error, validate


def append_case(path: Path, case: dict[str, Any]) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    gate = data.get("minimum_gate") if isinstance(data.get("minimum_gate"), dict) else {}
    case_id = str(case.get("case_id") or "").strip()
    if not case_id:
        return {"appended": False, "errors": ["case_id_missing"], "validation": validate(path)}
    if any(str(existing.get("case_id") or "") == case_id for existing in data.get("cases", []) if isinstance(existing, dict)):
        return {"appended": False, "errors": ["case_id_duplicate"], "validation": validate(path)}
    error = case_error(case, gate)
    if error:
        return {"appended": False, "errors": [error], "validation": validate(path)}
    data.setdefault("cases", []).append({
        **case,
        "ingested_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    })
    data["status"] = "collecting_independently_reviewed_cases"
    data["verified_minute_claim_allowed"] = False
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"appended": True, "errors": [], "validation": validate(path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--case-json", required=True, help="One complete, independently reviewed case JSON object.")
    args = parser.parse_args()
    print(json.dumps(append_case(args.manifest, json.loads(args.case_json)), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
