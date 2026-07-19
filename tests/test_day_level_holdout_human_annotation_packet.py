from __future__ import annotations

import json
from pathlib import Path

from scripts.day_level_holdout_human_annotation_packet import build_packet

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "references/real_case_calibration/day_level_holdout_v3_pilot_source_queue_report_2026_07_19.json"


def test_human_annotation_packet_keeps_all_windows_unlabeled_and_unfrozen() -> None:
    packet = build_packet(REPORT)

    assert packet["scope"] == "day_level_holdout_human_annotation_packet"
    assert packet["status"] == "awaiting_independent_human_adjudication"
    assert packet["ready_for_blind_eval"] is False
    assert packet["production_tuning_allowed"] is False
    assert packet["summary"] == {
        "annotation_count": 9,
        "final_label_count": 0,
        "frozen_count": 0,
        "positive_candidate_count": 3,
        "negative_candidate_count": 6,
    }


def test_human_annotation_packet_has_required_blank_review_fields() -> None:
    packet = build_packet(REPORT)
    for row in packet["annotations"]:
        assert row["candidate_label"] in {"target_event", "no_target_event"}
        assert row["final_label"] is None
        assert row["independent_human_reviewed"] is False
        assert row["frozen_before_scoring"] is False
        assert row["adjudicator"] == ""
        assert row["source_quote_or_summary"] == ""
        assert row["review_decision"] == "pending"
        assert row["source_urls"]
        assert row["annotation_id"].startswith("DLH-PILOT-")


def test_human_annotation_packet_artifact_matches_generator() -> None:
    artifact = ROOT / "references/real_case_calibration/day_level_holdout_v3_human_annotation_packet_2026_07_19.json"
    data = json.loads(artifact.read_text(encoding="utf-8"))
    generated = build_packet(REPORT)
    assert data["summary"] == generated["summary"]
    assert data["ready_for_blind_eval"] is False

