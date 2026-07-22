from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/timing_rectification_public_holdout_candidate_queue_2026_07_22.json"


def test_public_holdout_candidate_queue_has_positive_sources_but_no_negative_labels() -> None:
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    assert packet["claim_status"] == "blocked_until_human_labels"
    assert packet["summary"]["public_positive_event_candidate_count"] >= 3
    assert packet["summary"]["frozen_negative_window_count"] == 0
    assert packet["summary"]["day_month_claim_upgrade_allowed"] is False
    assert all(row["source_url"].startswith("https://") for row in packet["positive_event_candidates"])
    assert "does not provide negative labels" in packet["boundary"]
