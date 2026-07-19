from __future__ import annotations

import json
from pathlib import Path

from scripts.day_level_holdout_validator import validate
from scripts.day_level_negative_holdout_intake import append_annotation
from scripts.timing_ranker_blind_eval import evaluate


def test_holdout_validator_rejects_non_independent_and_prohibited_rows(tmp_path: Path) -> None:
    manifest = {
        "prohibited_tuning_data": ["old_controls.json"],
        "frozen_gate": {"minimum_independent_cases": 1, "minimum_independent_negative_intervals": 1},
        "annotations": [
            {
                "case_id": "case-1",
                "domain": "career",
                "label": "no_target_event",
                "start": "2020-01-01",
                "end": "2020-01-07",
                "source_url": "https://example.org/timeline",
                "adjudicator": "same_person",
                "time_uncertainty_days": 0,
                "independent_human_reviewed": False,
                "source_path": "old_controls.json",
            }
        ],
    }
    path = tmp_path / "holdout.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate(path)

    assert report["status"] == "awaiting_independent_labels"
    assert report["production_tuning_allowed"] is False
    assert {error["error"] for error in report["errors"]} >= {
        "not_independently_human_reviewed",
        "prohibited_tuning_source",
    }


def test_blind_eval_requires_positive_windows_to_rank_above_negative_windows(tmp_path: Path) -> None:
    manifest = {
        "frozen_gate": {
            "minimum_positive_top_3_rate": 0.6,
            "minimum_specificity": 0.6,
            "minimum_independent_cases": 1,
            "minimum_independent_negative_intervals": 1,
        },
        "annotations": [
            {
                "case_id": "case-1",
                "domain": "career",
                "label": "target_event",
                "start": "2020-01-01",
                "end": "2020-01-07",
                "source_url": "https://example.org/event",
                "adjudicator": "reviewer-a",
                "time_uncertainty_days": 0,
                "independent_human_reviewed": True,
            },
            {
                "case_id": "case-1-neg",
                "domain": "career",
                "label": "no_target_event",
                "start": "2020-02-01",
                "end": "2020-02-07",
                "source_url": "https://example.org/non-event",
                "adjudicator": "reviewer-b",
                "time_uncertainty_days": 0,
                "independent_human_reviewed": True,
            },
        ],
    }
    candidates = {
        "candidate_windows": [
            {"case_id": "case-1", "start": "2020-01-01", "end": "2020-01-07", "score": 0.90},
            {"case_id": "case-1-neg", "start": "2020-02-01", "end": "2020-02-07", "score": 0.20},
        ]
    }
    manifest_path = tmp_path / "holdout.json"
    candidates_path = tmp_path / "candidates.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    candidates_path.write_text(json.dumps(candidates), encoding="utf-8")

    report = evaluate(manifest_path, candidates_path)

    assert report["status"] == "pass"
    assert report["claim_status"] == "calibrated_day_level"
    assert report["production_tuning_allowed"] is True
    assert report["positive_top_3_rate"] == 1.0
    assert report["specificity"] == 1.0


def test_blind_eval_blocks_when_negative_scores_outrank_positive_scores(tmp_path: Path) -> None:
    manifest = {
        "frozen_gate": {
            "minimum_positive_top_3_rate": 0.6,
            "minimum_specificity": 0.6,
            "minimum_independent_cases": 1,
            "minimum_independent_negative_intervals": 1,
        },
        "annotations": [
            {
                "case_id": "positive",
                "domain": "marriage",
                "label": "target_event",
                "start": "2020-01-01",
                "end": "2020-01-07",
                "source_url": "https://example.org/event",
                "adjudicator": "reviewer-a",
                "time_uncertainty_days": 0,
                "independent_human_reviewed": True,
            },
            {
                "case_id": "negative",
                "domain": "marriage",
                "label": "no_target_event",
                "start": "2020-02-01",
                "end": "2020-02-07",
                "source_url": "https://example.org/non-event",
                "adjudicator": "reviewer-b",
                "time_uncertainty_days": 0,
                "independent_human_reviewed": True,
            },
        ],
    }
    candidates = {
        "candidate_windows": [
            {"case_id": "positive", "start": "2020-01-01", "end": "2020-01-07", "score": 0.10},
            {"case_id": "negative", "start": "2020-02-01", "end": "2020-02-07", "score": 0.95},
        ]
    }
    manifest_path = tmp_path / "holdout.json"
    candidates_path = tmp_path / "candidates.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    candidates_path.write_text(json.dumps(candidates), encoding="utf-8")

    report = evaluate(manifest_path, candidates_path)

    assert report["status"] == "blocked"
    assert report["claim_status"] == "exploratory_unvalidated"
    assert report["production_tuning_allowed"] is False
    assert "specificity_below_gate" in report["blockers"]


def test_negative_holdout_intake_appends_valid_independent_label(tmp_path: Path) -> None:
    path = tmp_path / "holdout.json"
    path.write_text(json.dumps({"annotations": [], "prohibited_tuning_data": []}), encoding="utf-8")

    report = append_annotation(
        path,
        {
            "case_id": "case-2-neg",
            "domain": "career",
            "label": "no_target_event",
            "start": "2020-03-01",
            "end": "2020-03-31",
            "source_url": "https://example.org/biography",
            "adjudicator": "reviewer-c",
            "time_uncertainty_days": 0,
            "independent_human_reviewed": True,
        },
    )

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert report["appended"] is True
    assert saved["annotations"][0]["case_id"] == "case-2-neg"
    assert saved["annotations"][0]["frozen_before_scoring"] is True


def test_negative_holdout_intake_rejects_non_independent_label(tmp_path: Path) -> None:
    path = tmp_path / "holdout.json"
    path.write_text(json.dumps({"annotations": []}), encoding="utf-8")

    report = append_annotation(
        path,
        {
            "case_id": "bad",
            "domain": "career",
            "label": "no_target_event",
            "start": "2020-03-01",
            "end": "2020-03-31",
            "source_url": "https://example.org/biography",
            "adjudicator": "reviewer-c",
            "time_uncertainty_days": 0,
            "independent_human_reviewed": False,
        },
    )

    assert report["appended"] is False
    assert report["errors"][0]["error"] == "not_independently_human_reviewed"
