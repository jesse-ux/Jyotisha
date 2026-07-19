#!/usr/bin/env python3
"""Summarize three-engine mismatch closure progress without mutating queue."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "references/oracle/three_engine_mismatch_closure_queue_2026_07_19.json"
NODE_ATTR = ROOT / "references/oracle/jyotishganit_node_source_attribution_2026_07_19.json"


def build() -> dict:
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    node = json.loads(NODE_ATTR.read_text(encoding="utf-8"))
    attributed = [
        {
            "section": "D10",
            "field": body,
            "closure_state": "attributed_no_tuning",
            "reason": node["attribution"]["primary_delta"],
            "effect": node["attribution"]["effect"],
        }
        for body in ("Rahu", "Ketu")
        if f"D10 {body}" in node.get("remaining_mismatches", [])
    ]
    total = queue["summary"]["queue_count"]
    return {
        "scope": "three_engine_mismatch_progress_ledger",
        "created_at": "2026-07-19",
        "status": "progress_ledger_ready",
        "claim_status": "partial",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "source_queue": str(QUEUE.relative_to(ROOT)),
        "attribution_sources": [str(NODE_ATTR.relative_to(ROOT))],
        "summary": {
            "source_queue_count": total,
            "attributed_no_tuning_count": len(attributed),
            "remaining_open_count": total - len(attributed),
        },
        "attributed_rows": attributed,
        "boundary": (
            "Attribution closes explanation work only. The original mismatch queue "
            "stays open for formula/endpoint/worked-example evidence, and no "
            "engine majority vote is allowed."
        ),
    }


def main() -> int:
    print(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
