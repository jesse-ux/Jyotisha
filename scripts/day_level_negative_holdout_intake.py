#!/usr/bin/env python3
"""Append independently sourced day-level timing holdout annotations."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.day_level_holdout_validator import REQUIRED, validate


def _row_errors(row: dict, prohibited: set[str]) -> list[dict]:
    errors = []
    for key in sorted(REQUIRED - set(row)):
        errors.append({"field": key, "error": "missing"})
    if row.get("label") not in {"target_event", "no_target_event"}:
        errors.append({"field": "label", "error": "invalid"})
    if not str(row.get("source_url") or "").startswith(("https://", "http://")):
        errors.append({"field": "source_url", "error": "not_public_url"})
    if row.get("independent_human_reviewed") is not True:
        errors.append({"field": "independent_human_reviewed", "error": "not_independently_human_reviewed"})
    if row.get("source_path") in prohibited:
        errors.append({"field": "source_path", "error": "prohibited_tuning_source"})
    return errors


def append_annotation(path: Path, row: dict) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    prohibited = set(data.get("prohibited_tuning_data") or [])
    errors = _row_errors(row, prohibited)
    if errors:
        return {"appended": False, "errors": errors, "validation": validate(path)}
    next_row = {
        **row,
        "frozen_before_scoring": True,
        "ingested_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    data.setdefault("annotations", []).append(next_row)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"appended": True, "errors": [], "validation": validate(path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--row-json", required=True, help="One annotation JSON object.")
    args = parser.parse_args()
    print(json.dumps(append_annotation(args.manifest, json.loads(args.row_json)), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
