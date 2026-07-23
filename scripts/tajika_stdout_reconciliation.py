#!/usr/bin/env python3
"""Reconcile an archived PyJHora Tajika stdout artifact with its evidence packet.

This validates repository provenance only. It is not a public worked example,
does not compare an independent engine, and cannot promote annual predictions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


FIELDS = (
    "solar_return_datetime",
    "varsha_lagna_deg",
    "muntha_sign",
    "year_lord",
    "mudda_dasha_first_lord",
    "sahams.punya_saham",
    "sahams.rajya_saham",
    "sahams.vivah_saham",
    "tajika_yogas",
)
RAW_PREFIX = "TAJIKA_ANNUAL_VALUES_JSON "


def _get(value: dict[str, Any], dotted_field: str) -> Any:
    current: Any = value
    for key in dotted_field.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _extract_raw_values(raw_text: str) -> dict[str, Any]:
    for line in raw_text.splitlines():
        if line.startswith(RAW_PREFIX):
            value = json.loads(line.removeprefix(RAW_PREFIX))
            if isinstance(value, dict):
                return value
    raise ValueError(f"Missing {RAW_PREFIX.strip()} line")


def build_report(raw_path: Path, packet_path: Path) -> dict[str, Any]:
    raw_bytes = raw_path.read_bytes()
    raw_values = _extract_raw_values(raw_bytes.decode("utf-8"))
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    expected = packet.get("target_placeholders", {})
    comparisons = []
    for field in FIELDS:
        raw_value = _get(raw_values, field)
        expected_value = expected.get(f"target.{field}")
        comparisons.append({
            "field": field,
            "raw_value": raw_value,
            "packet_value": expected_value,
            "matches": raw_value == expected_value,
        })
    matched_count = sum(row["matches"] for row in comparisons)
    return {
        "scope": "tajika_stdout_template_reconciliation",
        "status": (
            "external_artifact_template_consistent_observation"
            if matched_count == len(comparisons)
            else "external_artifact_template_mismatch_observation"
        ),
        "claim_status": "observation_only",
        "consumer_policy": "research_observation_only",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "raw_artifact": {
            "path": str(raw_path),
            "sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "extraction_prefix": RAW_PREFIX.strip(),
        },
        "evidence_packet": {
            "path": str(packet_path),
            "capture_id": packet.get("capture_id"),
            "status": packet.get("status"),
        },
        "field_comparisons": comparisons,
        "summary": {
            "field_count": len(comparisons),
            "matched_field_count": matched_count,
            "mismatched_field_count": len(comparisons) - matched_count,
        },
        "claim_boundary": (
            "A matching archive proves only that the packet's selected fields are reproducible from its own stored "
            "PyJHora stdout. It does not establish independent software parity, a public worked example, traditional "
            "formula authority, annual judgment quality, timing accuracy, or production tuning permission."
        ),
        "remaining_requirements": [
            "At least one independently citable public Varshaphala/Tajika worked example with settings and numeric fields.",
            "Independent-engine replay with documented solar-return and timezone/DST conventions.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.raw, args.packet)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
