from __future__ import annotations

from pathlib import Path

from scripts.day_level_holdout_pilot_source_queue_report import build_report

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "references/real_case_calibration/day_level_holdout_v3_pilot_source_queue_2026_07_19.json"


def test_pilot_source_queue_expands_to_nine_unscored_windows() -> None:
    report = build_report(QUEUE)

    assert report["scope"] == "day_level_holdout_pilot_source_queue_report"
    assert report["status"] == "awaiting_independent_human_labels"
    assert report["production_tuning_allowed"] is False
    assert report["blind_scoring_allowed"] is False
    assert report["summary"] == {
        "subject_count": 3,
        "window_count": 9,
        "positive_candidate_count": 3,
        "negative_candidate_count": 6,
        "ready_annotation_count": 0,
        "blocked_annotation_count": 9,
    }


def test_pilot_source_queue_windows_keep_public_source_and_boundary() -> None:
    report = build_report(QUEUE)

    for window in report["windows"]:
        assert window["claim_status"] == "candidate_not_label"
        assert window["required_next_step"] == "independent_human_adjudication"
        assert window["scoring_status"] == "blocked_not_frozen"
        if window["label_candidate"] == "target_event":
            assert window["source_urls"]
            assert all(url.startswith("https://") for url in window["source_urls"])
        else:
            assert window["event_absent_assertion"]

