from __future__ import annotations

from scripts.active_rectification_events import (
    CandidateScoreRow,
    adjudicate_candidate_rows,
    precision_weight,
    score_life_events,
)


def _row(time: str, score: float) -> CandidateScoreRow:
    return {
        "time": time,
        "score": score,
        "evidence": [],
        "missing_layers": [],
    }


def test_high_confidence_requires_four_events_three_domains_and_narrow_leader() -> None:
    result = adjudicate_candidate_rows(
        [
            _row("14:22", 16),
            _row("14:23", 16),
            _row("14:24", 16),
            _row("14:25", 16),
            _row("14:26", 16),
            _row("14:27", 10),
        ],
        event_count=4,
        domain_count=3,
        request_fingerprint="high-fixture",
    )

    assert result["confidence"] == "high"
    assert result["can_apply"] is True
    assert result["winning_segment"] == {
        "start_time": "14:22",
        "end_time": "14:26",
        "representative_time": "14:24",
        "width_minutes": 5,
    }
    assert result["margin_percent"] == 37.5


def test_tied_disjoint_candidates_abstain() -> None:
    result = adjudicate_candidate_rows(
        [_row("14:20", 10), _row("14:21", 8), _row("14:22", 10)],
        event_count=4,
        domain_count=3,
        request_fingerprint="tie-fixture",
    )

    assert result["confidence"] == "low"
    assert result["can_apply"] is False
    assert "tied_leader" in result["reasons"]
    assert result["winning_segment"] is None


def test_medium_confidence_never_allows_application() -> None:
    result = adjudicate_candidate_rows(
        [_row("14:20", 10), _row("14:21", 8)],
        event_count=3,
        domain_count=2,
        request_fingerprint="medium-fixture",
    )

    assert result["confidence"] == "medium"
    assert result["can_apply"] is False
    assert result["winning_segment"]["representative_time"] == "14:20"


def test_result_keeps_only_representative_minute_evidence() -> None:
    rows = [_row("14:20", 10), _row("14:21", 10), _row("14:22", 10), _row("14:23", 5)]
    for row in rows:
        row["evidence"] = [{
            "event_id": "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
            "domain": "education",
            "candidate_time": row["time"],
            "rule_ids": ["fixture"],
            "points": row["score"],
        }]

    result = adjudicate_candidate_rows(
        rows,
        event_count=3,
        domain_count=2,
        request_fingerprint="representative-evidence-fixture",
    )

    assert [item["candidate_time"] for item in result["evidence"]] == ["14:21"]


def test_missing_mandatory_layer_caps_confidence_at_low() -> None:
    row = _row("14:20", 10)
    row["missing_layers"] = ["D24"]

    result = adjudicate_candidate_rows(
        [row, _row("14:21", 5)],
        event_count=4,
        domain_count=3,
        request_fingerprint="missing-layer-fixture",
    )

    assert result["confidence"] == "low"
    assert "missing_mandatory_layers" in result["reasons"]
    assert result["can_apply"] is False


def test_date_precision_weights_are_fixed() -> None:
    assert precision_weight("day") == 1.0
    assert precision_weight("month") == 0.8
    assert precision_weight("year") == 0.5


def test_real_local_scoring_uses_dated_events_and_actual_candidate_minutes() -> None:
    result = score_life_events({
        "birth_date": "1993-04-17",
        "start_time": "14:29",
        "end_time": "14:31",
        "lat": 36.683333,
        "lon": 114.35,
        "tz": 8.0,
        "events": [
            {
                "id": "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
                "domain": "education",
                "date": "2011-09",
                "precision": "month",
            },
            {
                "id": "0790866c-ad5e-4a45-b2b4-a5c73f6be6ea",
                "domain": "career",
                "date": "2019-07-01",
                "precision": "day",
            },
            {
                "id": "0ef52e51-ab5f-453b-81e5-adb44a929224",
                "domain": "relationship",
                "date": "2021",
                "precision": "year",
            },
        ],
    })

    assert result["result_id"]
    assert result["event_count"] == 3
    assert result["domain_count"] == 3
    assert result["algorithm_version"] == "birth-time-event-scoring-v1"
    assert result["confidence"] in {"low", "medium"}
