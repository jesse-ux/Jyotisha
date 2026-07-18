#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate same-chart three-engine parity replay manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

REQUIRED_ENGINES = {"VedAstro", "PyJHora_JHora", "jyotishganit"}
REQUIRED_ROW_FIELDS = {"section", "field", "local_value", "oracle_values", "status"}
REQUIRED_HIGH_RIGOR_SECTIONS = {
    "D1",
    "D2",
    "D4",
    "D9",
    "D10",
    "ashtakavarga_bav",
    "ashtakavarga_sav",
    "shadbala_total",
    "shadbala_components",
}
VALID_ROW_STATUSES = {"match", "mismatch", "blocked", "not_comparable"}
RAW_VERIFIED_STATUSES = {"verified", "official_verified", "imported"}


def _artifact_errors(engine: str, payload: Any, manifest_dir: Path) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return [{"field": f"engines.{engine}", "error": "not_object"}]
    if payload.get("status") not in RAW_VERIFIED_STATUSES:
        return []
    raw_path = payload.get("official_raw_response_path") or payload.get("raw_output_path")
    artifact_hash = payload.get("artifact_hash")
    errors: list[dict[str, Any]] = []
    if not isinstance(raw_path, str) or not raw_path:
        errors.append({"field": f"engines.{engine}.raw_output_path", "error": "required_for_verified_status"})
        return errors
    if not isinstance(artifact_hash, str) or len(artifact_hash) != 64:
        errors.append({"field": f"engines.{engine}.artifact_hash", "error": "sha256_required_for_verified_status"})
        return errors
    artifact_path = (manifest_dir / raw_path).resolve()
    if not artifact_path.is_file():
        errors.append({"field": f"engines.{engine}.raw_output_path", "error": "missing_artifact"})
        return errors
    actual_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    if actual_hash != artifact_hash:
        errors.append({"field": f"engines.{engine}.artifact_hash", "error": "hash_mismatch"})
    if not isinstance(payload.get("settings"), dict):
        errors.append({"field": f"engines.{engine}.settings", "error": "required_for_verified_status"})
    return errors


def _row_errors(row: Any, index: int) -> list[dict[str, Any]]:
    if not isinstance(row, dict):
        return [{"row_index": index, "field": "row", "error": "not_object"}]
    errors: list[dict[str, Any]] = []
    for field in sorted(REQUIRED_ROW_FIELDS - set(row)):
        errors.append({"row_index": index, "field": field, "error": "missing"})
    if row.get("status") not in VALID_ROW_STATUSES:
        errors.append({"row_index": index, "field": "status", "error": "invalid"})
    if "oracle_values" in row and not isinstance(row.get("oracle_values"), dict):
        errors.append({"row_index": index, "field": "oracle_values", "error": "not_object"})
    return errors


def validate_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    engines = manifest.get("engines") if isinstance(manifest.get("engines"), dict) else {}
    rows = manifest.get("comparison_rows")
    errors: list[dict[str, Any]] = []

    missing_engines = sorted(REQUIRED_ENGINES - set(engines))
    for engine in missing_engines:
        errors.append({"field": f"engines.{engine}", "error": "missing"})
    for engine, payload in engines.items():
        errors.extend(_artifact_errors(engine, payload, manifest_path.parent))

    if not isinstance(rows, list):
        rows = []
        errors.append({"field": "comparison_rows", "error": "not_array"})

    for index, row in enumerate(rows):
        errors.extend(_row_errors(row, index))

    counts = {"match": 0, "mismatch": 0, "blocked": 0, "not_comparable": 0}
    for row in rows:
        if isinstance(row, dict) and row.get("status") in counts:
            counts[row["status"]] += 1
    covered_sections = {
        str(row.get("section"))
        for row in rows
        if isinstance(row, dict) and row.get("status") in {"match", "mismatch"}
    }
    missing_high_rigor_sections = sorted(REQUIRED_HIGH_RIGOR_SECTIONS - covered_sections)

    if errors:
        status = "invalid"
        blocked_reason = "parity_manifest_contract_errors"
    elif not rows:
        status = "blocked"
        blocked_reason = manifest.get("blocked_reason") or "no_same_chart_oracle_rows_imported"
    elif counts["mismatch"]:
        status = "mismatch"
        blocked_reason = None
    elif counts["blocked"]:
        status = "partial"
        blocked_reason = "some_comparison_rows_blocked"
    elif missing_high_rigor_sections:
        status = "partial"
        blocked_reason = "missing_high_rigor_sections"
    else:
        status = "pass"
        blocked_reason = None

    return {
        "status": status,
        "tested": status in {"pass", "mismatch", "partial"},
        "manifest_path": str(manifest_path),
        "case_id": manifest.get("case_id"),
        "birth_data_policy": manifest.get("birth_data_policy"),
        "engine_count": len(engines),
        "required_engines": sorted(REQUIRED_ENGINES),
        "missing_engines": missing_engines,
        "comparison_row_count": len(rows),
        "match_count": counts["match"],
        "mismatch_count": counts["mismatch"],
        "blocked_row_count": counts["blocked"],
        "not_comparable_count": counts["not_comparable"],
        "covered_sections": sorted(covered_sections),
        "missing_high_rigor_sections": missing_high_rigor_sections,
        "blocked_reason": blocked_reason,
        "errors": errors,
        "runtime_boundary": manifest.get("runtime_boundary", ""),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", default="references/oracle/three_engine_parity_replay_manifest.json")
    parser.add_argument("--require-pass", action="store_true", help="Return nonzero unless all comparison rows pass.")
    args = parser.parse_args(argv)
    report = validate_manifest(args.manifest)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not args.require_pass or report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
