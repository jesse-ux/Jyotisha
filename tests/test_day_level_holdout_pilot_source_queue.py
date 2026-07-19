from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "references" / "real_case_calibration" / "day_level_holdout_v3_pilot_source_queue_2026_07_19.json"


def test_pilot_source_queue_has_three_public_subjects_but_no_truth_upgrade() -> None:
    data = json.loads(QUEUE.read_text(encoding="utf-8"))

    assert data["status"] == "candidate_requires_adjudication"
    assert data["production_tuning_allowed"] is False
    assert data["candidate_count"] == 3
    assert "not holdout annotations" in data["truth_boundary"]
    assert "independent adjudicator" in data["required_next_step"]

    subjects = {subject["subject_id"]: subject for subject in data["subjects"]}
    assert set(subjects) == {"steve_jobs", "barack_obama", "albert_einstein"}
    for subject in subjects.values():
        assert subject["candidate_positive_event"]["status"] == "candidate_requires_adjudication"
        assert len(subject["candidate_negative_windows"]) == 2
        assert all(window["status"] == "candidate_requires_adjudication" for window in subject["candidate_negative_windows"])
        assert all(url.startswith("https://") for url in subject["candidate_positive_event"]["source_urls"])


def test_pilot_source_queue_is_not_misrepresented_as_day_level_holdout_manifest() -> None:
    data = json.loads(QUEUE.read_text(encoding="utf-8"))

    assert "annotations" not in data
    assert data["scope"] == "day_level_holdout_v3_pilot_source_queue"
    assert data["status"] != "ready_for_blind_replay"
