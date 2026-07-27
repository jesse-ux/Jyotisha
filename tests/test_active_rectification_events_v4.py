from __future__ import annotations

from scripts import active_rectification_events_v4 as v4


def _row(candidate_time: str, event_id: str, points: float):
    return {
        "time": candidate_time,
        "score": points,
        "evidence": [{
            "event_id": event_id,
            "domain": "education",
            "candidate_time": candidate_time,
            "rule_ids": ["test"],
            "points": points,
        }],
        "missing_layers": [],
    }


def test_v4_scores_real_date_boundaries_and_never_confirms_a_minute(monkeypatch) -> None:
    calls = []

    def fake_compute(request):
        calls.append(request)
        event_id = request["events"][0]["id"]
        boundary = request["events"][0]["date"]
        return [
            _row("05:13", event_id, 10 if boundary.endswith("-01") else 8),
            _row("05:14", event_id, 9 if boundary.endswith("-01") else 9),
            _row("05:15", event_id, 8 if boundary.endswith("-01") else 10),
        ]

    monkeypatch.setattr(v4, "compute_event_candidate_rows", fake_compute)
    result = v4.score_life_events_v4({
        "birth_date": "1997-08-08",
        "start_time": "04:30",
        "end_time": "05:30",
        "lat": 36.419,
        "lon": 114.213,
        "tz": 8.0,
        "events": [{
            "id": "00000000-0000-4000-8000-000000000001",
            "domain": "education",
            "event_kind": "education_milestone",
            "date_start": "2016-09-01",
            "date_end": "2016-09-30",
            "precision": "month",
            "summary": "大学入学",
        }],
    })
    assert [call["events"][0]["date"] for call in calls] == ["2016-09-01", "2016-09-30"]
    assert result["candidate_scores"][1]["score"] == 9
    assert result["robustness"]["date_sensitivity_retention_rate"] == 1
    assert result["can_confirm_exact_minute"] is False
    assert result["calculation_spec_hash"] == "3e558d5aca9920357bda1d11c3f34fd9a4c2a7d92ccd9bc05cf85fbddd1bee20"


def test_v4_api_validates_event_kind_and_date_boundaries(monkeypatch) -> None:
    from scripts.jyotish_api_server import BadRequest, JyotishAPIHandler

    captured = {}
    monkeypatch.setattr("scripts.jyotish_api_server._load_local_module", lambda name: v4)
    monkeypatch.setattr(v4, "score_life_events_v4", lambda request: captured.setdefault("request", request) or {})
    handler = JyotishAPIHandler.__new__(JyotishAPIHandler)
    body = {
        "birth_date": "1997-08-08",
        "start_time": "05:00",
        "end_time": "05:30",
        "lat": 36.419,
        "lon": 114.213,
        "tz": 8,
        "events": [{
            "id": "00000000-0000-4000-8000-000000000001",
            "domain": "relationship",
            "event_kind": "relationship_end",
            "date_start": "2020-10-01",
            "date_end": "2020-10-31",
            "precision": "month",
            "summary": "关系结束",
        }],
    }
    result = handler._compute_active_rectification_events_v4(body)
    assert result["endpoint"] == "active_rectification_events_v4"
    assert captured["request"]["events"][0]["date_end"] == "2020-10-31"

    import pytest
    with pytest.raises(BadRequest, match="event_kind does not match"):
        handler._compute_active_rectification_events_v4({
            **body,
            "events": [{**body["events"][0], "event_kind": "relationship_start", "domain": "career"}],
        })
    with pytest.raises(BadRequest, match="date_start must not exceed"):
        handler._compute_active_rectification_events_v4({
            **body,
            "events": [{**body["events"][0], "date_start": "2020-11-01"}],
        })
