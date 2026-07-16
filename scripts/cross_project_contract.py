#!/usr/bin/env python3
"""Validate public synthetic calculation fixtures shared across Jyotish projects."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from jyotish_engine import compute_chart_data


PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
REQUIRED_LEDGER_FIELDS = {
    "source_repository", "source_commit", "target_repository", "target_commit",
    "change_class", "copied_files", "dependency_delta", "privacy_review",
    "focused_tests", "hash_contract_result", "rollback",
}


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("fixture manifest schema_version must be 1")
    if manifest.get("privacy_scope") != "public_synthetic_only":
        raise ValueError("fixture manifest must be public_synthetic_only")
    if not isinstance(manifest.get("fixtures"), list) or not manifest["fixtures"]:
        raise ValueError("fixture manifest must contain fixtures")
    return manifest


def load_ledger(path: Path) -> dict[str, Any]:
    ledger = json.loads(path.read_text(encoding="utf-8"))
    if ledger.get("schema_version") != 1 or not isinstance(ledger.get("entries"), list):
        raise ValueError("sync ledger must contain schema_version=1 and entries array")
    return ledger


def validate_ledger_entry(entry: dict[str, Any]) -> list[str]:
    return sorted(REQUIRED_LEDGER_FIELDS - entry.keys())


def _calculate_fixture_chart(fixture: dict[str, Any]) -> dict[str, Any]:
    birth = fixture["birth"]
    effective = fixture["effective"]
    chart, _asc_idx, _jd, _ayanamsa = compute_chart_data(
        birth["year"], birth["month"], birth["day"], birth["hour"], birth["minute"],
        birth["lat"], birth["lon"], birth["tz"], node_mode=effective["node_mode"],
        second=birth.get("second", 0), ayanamsa_name=effective["ayanamsa"],
    )
    return chart


def _longitude(row: dict[str, Any]) -> float:
    value = row.get("lon", row.get("degree"))
    if not isinstance(value, (int, float)):
        raise ValueError("chart row must provide numeric lon or degree")
    return float(value)


def compatibility_payload(chart: dict[str, Any], fixture: dict[str, Any]) -> dict[str, Any]:
    return {
        "fixture_id": fixture["id"],
        "birth": {key: value for key, value in fixture["birth"].items() if key != "synthetic"},
        "effective": fixture["effective"],
        "ascendant": {"sign": chart["ascendant"]["sign"], "lon": _longitude(chart["ascendant"])},
        "planets": {
            planet: {"sign": chart["planets"][planet]["sign"], "lon": _longitude(chart["planets"][planet])}
            for planet in PLANETS
        },
    }


def compatibility_hash(chart: dict[str, Any], fixture: dict[str, Any]) -> str:
    encoded = json.dumps(compatibility_payload(chart, fixture), ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def evaluate_manifest(path: Path) -> dict[str, Any]:
    manifest = load_manifest(path)
    fixtures = []
    for fixture in manifest["fixtures"]:
        chart = _calculate_fixture_chart(fixture)
        actual = compatibility_hash(chart, fixture)
        expected = fixture["compatibility_hash"]
        fixtures.append({"id": fixture["id"], "expected_compatibility_hash": expected, "actual_compatibility_hash": actual, "matches": actual == expected})
    return {"schema_version": 1, "manifest": str(path), "fixtures": fixtures, "matches": all(row["matches"] for row in fixtures)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "references" / "cross_project_contract" / "fixture_manifest.v1.json")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--require-match", action="store_true")
    args = parser.parse_args(argv)
    report = evaluate_manifest(args.manifest)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for row in report["fixtures"]:
            print(f"{row['id']}: {'match' if row['matches'] else 'mismatch'}")
    return 0 if report["matches"] or not args.require_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
