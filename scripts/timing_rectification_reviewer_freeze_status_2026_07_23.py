#!/usr/bin/env python3
"""Record reviewer confirmation status for timing/rectification holdout candidates."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "references/real_case_calibration/timing_rectification_candidate_holdout_labels_2026_07_23.json"
DEFAULT_OUTPUT = ROOT / "references/real_case_calibration/timing_rectification_reviewer_freeze_status_2026_07_23.json"


def build_report(candidate_path: Path = CANDIDATES) -> dict[str, Any]:
    candidates = json.loads(candidate_path.read_text(encoding="utf-8"))
    cases = candidates.get("cases") or []
    reviewer_1 = {
        "reviewer_id": "user_confirmed_business_owner",
        "confirmation_text": "我确认这 3 个候选案例可以作为第一轮 holdout。",
        "confirmed_at": "2026-07-23",
        "independent_of_model_run": False,
        "allowed_for_tuning": False,
        "scope": "first_reviewer_acceptance_of_machine_prepared_candidates",
    }
    rows = [
        {
            "case_id": case["case_id"],
            "public_person": case["public_person"],
            "positive_event_label": case["positive_event"]["label"],
            "reviewer_1_status": "confirmed",
            "reviewer_2_status": "missing",
            "freeze_status": "one_reviewer_confirmed_second_required",
        }
        for case in cases
    ]
    return {
        "scope": "timing_rectification_reviewer_freeze_status",
        "created_at": date.today().isoformat(),
        "claim_status": "one_reviewer_confirmed_second_required",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "source_candidate_packet": str(candidate_path.relative_to(ROOT)),
        "reviewer_1": reviewer_1,
        "reviewer_2_required": True,
        "summary": {
            "case_count": len(rows),
            "reviewer_1_confirmed_count": len(rows),
            "reviewer_2_confirmed_count": 0,
            "ready_for_blind_replay_count": 0,
        },
        "rows": rows,
        "next_action": "Collect a second independent reviewer confirmation before running blind timing/rectification replay.",
        "boundary": "One reviewer confirmation advances candidate governance but does not satisfy the two-reviewer freeze requirement or upgrade timing claims.",
    }


def main() -> int:
    DEFAULT_OUTPUT.write_text(json.dumps(build_report(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(build_report(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
