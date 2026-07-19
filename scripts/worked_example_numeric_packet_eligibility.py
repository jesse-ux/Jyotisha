#!/usr/bin/env python3
"""Normalize public worked-example candidates into numeric-packet eligibility rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "references/oracle/public_worked_example_candidate_numeric_audit_2026_07_19.json"
QUEUE = ROOT / "references/oracle/kp_muhurta_shadbala_numeric_packet_queue_2026_07_19.json"


def classify(status: str) -> str:
    if status == "runtime_raw_available_public_oracle_missing":
        return "runtime_only_public_oracle_missing"
    if status == "table_hash_candidate_pending_capture":
        return "reference_table_hash_needed"
    if status == "worked_example_candidate_pending_raw_capture":
        return "raw_capture_needed"
    if status == "calculation_reference_pending_fixture":
        return "fixture_and_raw_capture_needed"
    return "formula_reference_only"


def build(date: str) -> dict[str, Any]:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    required_by_topic = {row["topic"]: row.get("required_fields", []) for row in queue.get("packet_rows", [])}
    rows = []
    for candidate in audit["candidates"]:
        topic = candidate["topic"].replace("KP cusp star/sub/sub-sub", "KP cusp")
        missing = list(candidate.get("missing_for_oracle", []))
        for field in required_by_topic.get(topic, []):
            if field not in missing:
                missing.append(field)
        rows.append(
            {
                "topic": topic,
                "url": candidate["url"],
                "candidate_type": candidate["candidate_type"],
                "eligibility_status": classify(candidate["numeric_packet_status"]),
                "runtime_observation_available": bool(candidate.get("runtime_observation_available")),
                "missing_for_oracle": missing,
                "claim_boundary": "Not oracle-ready until exact public input, settings, expected values, raw/hash and replay comparison are archived.",
            }
        )
    return {
        "scope": "worked_example_numeric_packet_eligibility",
        "created_at": date,
        "status": "eligibility_queue_ready",
        "claim_status": "open_queue",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "sources": {
            "candidate_numeric_audit": str(AUDIT.relative_to(ROOT)),
            "numeric_packet_queue": str(QUEUE.relative_to(ROOT)),
        },
        "summary": {
            "candidate_count": len(rows),
            "oracle_ready_count": 0,
            "runtime_only_count": sum(1 for row in rows if row["eligibility_status"] == "runtime_only_public_oracle_missing"),
            "raw_capture_needed_count": sum(1 for row in rows if "raw_capture" in row["eligibility_status"]),
        },
        "rows": rows,
        "boundary": "Eligibility queue only; no public numeric candidate is promoted to oracle_ready.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-07-20")
    args = parser.parse_args()
    print(json.dumps(build(args.date), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
