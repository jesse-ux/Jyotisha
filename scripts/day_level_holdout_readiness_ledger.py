#!/usr/bin/env python3
"""Report day-level timing holdout readiness without promoting unlabeled data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/real_case_calibration/day_level_holdout_v3_human_annotation_packet_2026_07_19.json"
MIN_POSITIVE = 20
MIN_NEGATIVE = 80


def build() -> dict[str, Any]:
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    annotations = packet["annotations"]
    frozen_final = [
        row
        for row in annotations
        if row.get("final_label")
        and row.get("independent_human_reviewed") is True
        and row.get("frozen_before_scoring") is True
    ]
    positive = sum(1 for row in frozen_final if row["final_label"] == "target_event")
    negative = sum(1 for row in frozen_final if row["final_label"] == "no_target_event")
    return {
        "scope": "day_level_holdout_readiness_ledger",
        "created_at": "2026-07-19",
        "status": "awaiting_independent_labels",
        "claim_status": "blocked",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "source_packet": str(PACKET.relative_to(ROOT)),
        "current": {
            "candidate_annotation_count": len(annotations),
            "frozen_final_count": len(frozen_final),
            "frozen_positive_count": positive,
            "frozen_negative_count": negative,
        },
        "required": {
            "minimum_frozen_positive": MIN_POSITIVE,
            "minimum_frozen_negative": MIN_NEGATIVE,
        },
        "remaining": {
            "positive_needed": max(0, MIN_POSITIVE - positive),
            "negative_needed": max(0, MIN_NEGATIVE - negative),
        },
        "blocked_reason": (
            "Pilot candidates are not independent frozen labels. Public positive "
            "event sources cannot be used as negative intervals without human "
            "absence adjudication."
        ),
        "boundary": (
            "No day/month timing claim can be promoted until the frozen positive "
            "and negative thresholds are met before blind replay."
        ),
    }


def main() -> int:
    print(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
