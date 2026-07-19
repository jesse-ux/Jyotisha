#!/usr/bin/env python3
"""Group three-engine mismatch tickets by owner track for closure planning."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "references/oracle/three_engine_mismatch_closure_queue_2026_07_19.json"
PROGRESS = ROOT / "references/oracle/three_engine_mismatch_progress_ledger_2026_07_19.json"


def build(date: str) -> dict[str, Any]:
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    progress = json.loads(PROGRESS.read_text(encoding="utf-8"))
    already = {
        (row["section"], row["field"])
        for row in progress.get("attributed_rows", [])
        if row.get("closure_state") == "attributed_no_tuning"
    }
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in queue["queue"]:
        groups[row["owner_track"]].append(row)

    batches = []
    for owner_track in sorted(groups):
        rows = groups[owner_track]
        batches.append(
            {
                "owner_track": owner_track,
                "ticket_count": len(rows),
                "priorities": sorted({row["priority"] for row in rows}),
                "categories": sorted({row["category"] for row in rows}),
                "sample_ticket_ids": [row["ticket_id"] for row in rows[:5]],
                "next_evidence": sorted({row["required_evidence"] for row in rows}),
                "claim_boundary": "Batch planning only; does not close mismatches, tune production, or majority-vote truth.",
            }
        )

    return {
        "scope": "three_engine_owner_track_batch_plan",
        "created_at": date,
        "status": "open_queue",
        "claim_status": "open_queue",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "source_queue": str(QUEUE.relative_to(ROOT)),
        "source_progress": str(PROGRESS.relative_to(ROOT)),
        "summary": {
            "source_queue_count": len(queue["queue"]),
            "already_attributed_count": len(already),
            "remaining_ticket_count": progress["summary"]["remaining_open_count"],
            "batched_source_row_count": sum(batch["ticket_count"] for batch in batches),
            "owner_track_count": len(batches),
        },
        "batches": batches,
        "boundary": "Prioritized owner-track batch plan for remaining three-engine mismatches; no claim is upgraded.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-07-20")
    args = parser.parse_args()
    print(json.dumps(build(args.date), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
