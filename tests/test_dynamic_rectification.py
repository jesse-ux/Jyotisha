from __future__ import annotations

from datetime import date, datetime

import pytest

from scripts import dynamic_rectification


def _base_request() -> dict:
    return {
        "case_id": "case-1",
        "birth_date": "1990-01-01",
        "as_of_date": "2026-07-18",
        "start_time": "05:30",
        "end_time": "05:33",
        "lat": 31.23,
        "lon": 121.47,
        "tz": 8.0,
        "evidence": [],
        "dismissed_opportunity_ids": [],
        "question_fingerprints": [],
        "partition_fingerprints": [],
        "recent_ranges": [],
    }


def _fake_rows(_request: dict) -> list[dict]:
    return [
        {
            "window_group": "periods-3",
            "dimension_code": "career",
            "window_start": "2014-01-01",
            "window_end": "2017-12-31",
            "activations": {"05:30": 5.0, "05:31": 1.0, "05:32": 0.0, "05:33": 0.0},
            "missing_layers": [],
        },
        {
            "window_group": "periods-3",
            "dimension_code": "career",
            "window_start": "2018-01-01",
            "window_end": "2021-12-31",
            "activations": {"05:30": 0.0, "05:31": 5.0, "05:32": 4.0, "05:33": 0.0},
            "missing_layers": [],
        },
        {
            "window_group": "periods-3",
            "dimension_code": "career",
            "window_start": "2022-01-01",
            "window_end": "2026-07-18",
            "activations": {"05:30": 0.0, "05:31": 0.0, "05:32": 1.0, "05:33": 5.0},
            "missing_layers": [],
        },
    ]


def _fake_model() -> dict:
    return {
        "version": "birth-time-choice-scoring-v2",
        "opportunity_model_version": "birth-time-opportunity-model-v2",
        "birth_date": "1990-01-01",
        "as_of_date": "2026-07-18",
        "range": {"start_time": "05:30", "end_time": "05:33"},
        "location": {"lat": 31.23, "lon": 121.47, "tz": 8.0},
        "candidate_times": ["05:30", "05:31", "05:32", "05:33"],
        "windows": _fake_rows({}),
    }


def test_packet_contains_only_candidate_backed_high_gain_opportunities(monkeypatch) -> None:
    monkeypatch.setattr(dynamic_rectification, "_candidate_window_rows", _fake_rows)

    packet = dynamic_rectification.build_difference_packet(_base_request())

    assert packet["scoring_version"] == "birth-time-choice-scoring-v2"
    assert packet["current_range"] == {"start_time": "05:30", "end_time": "05:33"}
    assert packet["opportunities"]
    for opportunity in packet["opportunities"]:
        assert opportunity["estimated_information_gain"] >= 0.15
        assert 2 <= len(opportunity["partitions"]) <= 4
        assert len({item["partition_id"] for item in opportunity["partitions"]}) == len(
            opportunity["partitions"]
        )
        for partition in opportunity["partitions"]:
            assert set(partition["candidate_scores"]) == {
                "05:30", "05:31", "05:32", "05:33",
            }


def test_period_range_offers_multiple_distinct_evidence_domains() -> None:
    packet = dynamic_rectification.build_difference_packet({
        **_base_request(),
        "birth_date": "1997-08-09",
        "as_of_date": "2026-07-19",
        "start_time": "04:00",
        "end_time": "07:59",
        "lat": 36.6,
        "lon": 114.5,
    })

    dimensions = {item["dimension_code"] for item in packet["opportunities"]}
    assert len(dimensions) >= 4


def test_packet_excludes_used_opportunity_and_partition_fingerprints(monkeypatch) -> None:
    monkeypatch.setattr(dynamic_rectification, "_candidate_window_rows", _fake_rows)
    first = dynamic_rectification.build_difference_packet(_base_request())
    used = first["opportunities"][0]
    request = _base_request()
    request["dismissed_opportunity_ids"] = [used["opportunity_id"]]
    request["partition_fingerprints"] = [used["candidate_partition_fingerprint"]]

    second = dynamic_rectification.build_difference_packet(request)

    assert all(item["opportunity_id"] != used["opportunity_id"] for item in second["opportunities"])
    assert all(
        item["candidate_partition_fingerprint"] != used["candidate_partition_fingerprint"]
        for item in second["opportunities"]
    )


def test_packet_reuses_the_persisted_candidate_model(monkeypatch) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(
        dynamic_rectification,
        "_compute_candidate_model",
        lambda request: calls.append(request) or _fake_model(),
    )
    first = dynamic_rectification.build_difference_packet(_base_request())

    second = dynamic_rectification.build_difference_packet(
        {**_base_request(), "candidate_model": first["candidate_model"]}
    )

    assert len(calls) == 1
    assert second["candidate_model"] == first["candidate_model"]


def test_candidate_model_rejects_wrong_range_and_non_finite_activation() -> None:
    model = _fake_model()
    model["range"] = {"start_time": "05:31", "end_time": "05:33"}
    with pytest.raises(ValueError, match="candidate model"):
        dynamic_rectification.build_difference_packet({**_base_request(), "candidate_model": model})

    model = _fake_model()
    model["windows"][0]["activations"]["05:30"] = float("nan")
    with pytest.raises(ValueError, match="candidate model"):
        dynamic_rectification.build_difference_packet({**_base_request(), "candidate_model": model})


def test_candidate_model_rejects_out_of_bounds_windows_and_boolean_activations() -> None:
    model = _fake_model()
    model["windows"][0]["window_end"] = "2027-01-01"
    with pytest.raises(ValueError, match="candidate model"):
        dynamic_rectification.build_difference_packet({**_base_request(), "candidate_model": model})

    model = _fake_model()
    model["windows"][0]["activations"]["05:30"] = True
    with pytest.raises(ValueError, match="candidate model"):
        dynamic_rectification.build_difference_packet({**_base_request(), "candidate_model": model})


@pytest.mark.parametrize(("field", "changed"), [("lat", 30.0), ("lon", 120.0), ("tz", 7.0)])
def test_candidate_model_reuse_rejects_location_or_timezone_change(field, changed) -> None:
    with pytest.raises(ValueError, match="candidate model"):
        dynamic_rectification.build_difference_packet({
            **_base_request(), field: changed, "candidate_model": _fake_model(),
        })


def test_existing_evidence_summary_must_be_effective_partition_evidence(monkeypatch) -> None:
    monkeypatch.setattr(dynamic_rectification, "_candidate_window_rows", _fake_rows)

    with pytest.raises(ValueError, match="partition evidence"):
        dynamic_rectification.build_difference_packet(
            {**_base_request(), "evidence": [{"kind": "unmatched", "note": "free text"}]}
        )


def test_candidate_charts_are_computed_once_and_missing_layers_are_dimension_scoped(
    monkeypatch,
) -> None:
    from scripts import active_rectification_event_engine

    candidates = [datetime(1990, 1, 1, 5, 30), datetime(1990, 1, 1, 5, 31)]
    calls: list[datetime] = []
    monkeypatch.setattr(active_rectification_event_engine, "_candidate_datetimes", lambda _: candidates)

    def fake_candidate_row(request: dict, candidate: datetime) -> dict:
        calls.append(candidate)
        return {
            "time": candidate.strftime("%H:%M"),
            "score": 0.0,
            "evidence": [
                {
                    "event_id": event["id"],
                    "domain": event["domain"],
                    "candidate_time": candidate.strftime("%H:%M"),
                    "rule_ids": ["fixture"],
                    "points": 1.0,
                }
                for event in request["events"] if event["domain"] != "career"
            ],
            "missing_layers": ["D10"],
        }

    monkeypatch.setattr(active_rectification_event_engine, "_candidate_row", fake_candidate_row)
    rows = dynamic_rectification._candidate_window_rows(_base_request())

    assert calls == candidates
    assert {tuple(row["missing_layers"]) for row in rows if row["dimension_code"] == "career"} == {("D10",)}
    assert {tuple(row["missing_layers"]) for row in rows if row["dimension_code"] != "career"} == {()}


def test_window_edges_and_under_age_cases_do_not_create_invalid_calculation(monkeypatch) -> None:
    assert dynamic_rectification._experience_windows("2000-01-01", "2012-01-01") == [
        (date(2012, 1, 1), date(2012, 1, 1)),
    ]

    from scripts import active_rectification_event_engine

    monkeypatch.setattr(
        active_rectification_event_engine,
        "_candidate_row",
        lambda *_: pytest.fail("candidate chart should not be computed"),
    )
    assert dynamic_rectification._candidate_window_rows({
        **_base_request(), "birth_date": "2020-01-01",
    }) == []
