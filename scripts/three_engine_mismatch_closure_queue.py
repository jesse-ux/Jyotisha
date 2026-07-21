#!/usr/bin/env python3
"""Create actionable closure tickets for three-engine mismatch rows."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


POLICY = {
    "endpoint_or_varga_semantics": ("P0", "endpoint_contract", "identified endpoint/method contract with ayanamsa, node mode, varga, timezone semantics"),
    "shadbala_formula_variant": ("P0", "formula_source", "public formula source + unit/cap/floor evidence for the component"),
    "derived_total_from_component_variants": ("P1", "unit_schema", "component closure before total recomputation; explicit Rupa/Virupa total rule"),
    "ashtakavarga_table_or_contributor_variant": ("P1", "worked_example", "public worked BAV/SAV table with contributor set, shodhana state, and Lagna inclusion"),
}


def build_queue(arbitration_path: str | Path) -> dict[str, Any]:
    path = Path(arbitration_path)
    report = json.loads(path.read_text(encoding="utf-8"))
    tickets = []
    for index, row in enumerate(report.get("rows") or [], start=1):
        priority, owner_track, required = POLICY.get(
            row["category"],
            ("P2", "worked_example", "manual source review and worked example required"),
        )
        tickets.append({
            "ticket_id": f"TEMCQ-{index:03d}",
            "priority": priority,
            "owner_track": owner_track,
            "section": row.get("section"),
            "field": row.get("field"),
            "category": row.get("category"),
            "differing_engines": row.get("differing_engines") or [],
            "required_evidence": required,
            "closure_status": "open",
            "commercial_visibility": "do_not_expose_raw",
        })
    return {
        "scope": "three_engine_mismatch_closure_queue",
        "source_arbitration": str(path),
        "status": "open" if tickets else "empty",
        "truth_policy": "no_majority_vote",
        "production_tuning_allowed": False,
        "summary": {
            "source_mismatch_count": report.get("mismatch_count", 0),
            "queue_count": len(tickets),
            "priority_counts": dict(Counter(ticket["priority"] for ticket in tickets)),
            "owner_track_counts": dict(Counter(ticket["owner_track"] for ticket in tickets)),
        },
        "queue": tickets,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arbitration", nargs="?", default="references/oracle/three_engine_mismatch_arbitration_2026_07_19.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    queue = build_queue(args.arbitration)
    text = json.dumps(queue, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
