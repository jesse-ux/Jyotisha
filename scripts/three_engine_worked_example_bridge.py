#!/usr/bin/env python3
"""Link three-engine mismatch owner tracks to worked-example intake domains."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "references/oracle/three_engine_owner_track_batch_plan_2026_07_20.json"
INTAKE = ROOT / "references/oracle/worked_example_packet_intake_plan_2026_07_20.json"

TRACK_TO_INTAKE = {
    "formula_source": ["shadbala_component_closure"],
    "derived_total": ["shadbala_component_closure"],
}


def build(date: str) -> dict[str, Any]:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    intake = json.loads(INTAKE.read_text(encoding="utf-8"))
    intake_by_domain = {row["domain"]: row for row in intake["domain_queues"]}
    links = []
    for batch in plan["batches"]:
        domains = TRACK_TO_INTAKE.get(batch["owner_track"], [])
        linked = [intake_by_domain[d] for d in domains if d in intake_by_domain]
        links.append(
            {
                "owner_track": batch["owner_track"],
                "ticket_count": batch["ticket_count"],
                "categories": batch["categories"],
                "linked_intake_domains": domains,
                "linked_candidate_count": sum(row["candidate_count"] for row in linked),
                "linked_blocking_fields": sorted({field for row in linked for field in row["blocking_fields"]}),
                "next_non_numeric_evidence": batch["next_evidence"] if not domains else [],
                "closure_condition": "Close only by field-level replay against a numeric packet or by explicit method-variant attribution.",
                "claim_boundary": "Bridge only; does not close mismatches, tune production, or majority-vote truth.",
            }
        )
    return {
        "scope": "three_engine_worked_example_bridge",
        "created_at": date,
        "status": "bridge_ready",
        "claim_status": "open_queue",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "sources": {
            "owner_track_batch_plan": str(PLAN.relative_to(ROOT)),
            "worked_example_packet_intake_plan": str(INTAKE.relative_to(ROOT)),
        },
        "summary": {
            "owner_track_count": len(links),
            "linked_owner_track_count": sum(1 for row in links if row["linked_intake_domains"]),
            "linked_candidate_count": sum(row["linked_candidate_count"] for row in links),
            "closed_mismatch_count": 0,
        },
        "owner_track_links": links,
        "boundary": "Bridge converts owner tracks into evidence asks; all mismatch rows remain open until replay/attribution artifacts close them.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-07-20")
    args = parser.parse_args()
    print(json.dumps(build(args.date), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
