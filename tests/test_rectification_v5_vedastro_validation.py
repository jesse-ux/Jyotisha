from __future__ import annotations

import pytest

from scripts.jyotish_api_server import (
    API_COMMAND_MAP,
    TECHNIQUE_EXAMPLE_ENDPOINTS,
    BadRequest,
    JyotishAPIHandler,
)


def request(candidate_times=None):
    events = [
        {
            "id": "00000000-0000-4000-8000-000000000001",
            "domain": "education",
            "event_kind": "education_milestone",
            "date_start": "2016-09-01",
            "date_end": "2016-09-30",
            "precision": "month",
            "summary": "private education summary that must not be returned",
        },
        {
            "id": "00000000-0000-4000-8000-000000000002",
            "domain": "career",
            "event_kind": "career_change",
            "date_start": "2020-05-01",
            "date_end": "2020-05-01",
            "precision": "day",
            "summary": "private career summary that must not be returned",
        },
        {
            "id": "00000000-0000-4000-8000-000000000003",
            "domain": "career",
            "event_kind": "career_change",
            "date_start": "2021-06-01",
            "date_end": "2021-06-01",
            "precision": "day",
            "summary": "newer career event wins the bounded selection",
        },
        {
            "id": "00000000-0000-4000-8000-000000000004",
            "domain": "relationship",
            "event_kind": "relationship_change",
            "date_start": "2022-01-01",
            "date_end": "2022-12-31",
            "precision": "year",
            "summary": "private relationship summary that must not be returned",
        },
        {
            "id": "00000000-0000-4000-8000-000000000005",
            "domain": "finance",
            "event_kind": "finance_change",
            "date_start": "2023-03-01",
            "date_end": "2023-03-31",
            "precision": "month",
            "summary": "private finance summary that must not be returned",
        },
        {
            "id": "00000000-0000-4000-8000-000000000006",
            "domain": "health_pressure",
            "event_kind": "self_health_event",
            "date_start": "2024-04-01",
            "date_end": "2024-04-30",
            "precision": "month",
            "summary": "private health summary that must not be returned",
        },
    ]
    return {
        "birth_date": "1997-08-08",
        "start_time": "05:00",
        "end_time": "05:30",
        "lat": 36.419,
        "lon": 114.213,
        "tz": 8,
        "events": events,
        "candidate_times": candidate_times if candidate_times is not None else ["05:13", "05:14"],
    }


def minute_snapshot(case, *, same=False):
    minute = case["minute"]
    suffix = "same" if same else str(minute)
    return {
        "available": True,
        "status": "ok",
        "source": "vedastro_official",
        "layers": {
            "ascendant_house_boundaries": {
                "status": "ok",
                "fingerprint": f"asc-{suffix}",
                "ascendant": {"sign": "Leo", "degree_in_sign": minute / 10},
                "houses": {"House1": {}},
            },
            "D9": {"status": "ok", "fingerprint": f"d9-{suffix}", "houses": {"House1": {}}, "planets": {}},
            "D10": {"status": "ok", "fingerprint": f"d10-{suffix}", "houses": {"House1": {}}, "planets": {}},
            "dasha_boundaries": {"status": "ok", "fingerprint": f"dasha-{suffix}", "boundary_count": 3},
            "kp_cusp_sub_lord": {"status": "unsupported", "reason": "not available"},
        },
        "raw_request": {"api_key": "secret"},
        "raw_response": {"private": True},
    }


def test_registry_exposes_independent_vedastro_validation_endpoint():
    endpoint = "/api/rectification/v5/vedastro-validate"
    assert API_COMMAND_MAP["rectification-v5-vedastro-validate"] == endpoint
    assert endpoint in TECHNIQUE_EXAMPLE_ENDPOINTS


def test_requires_exactly_two_distinct_candidate_times_before_running_vedastro():
    handler = object.__new__(JyotishAPIHandler)
    for candidate_times in ([], ["05:13"], ["05:13", "05:14", "05:15"], ["05:13", "05:13"]):
        with pytest.raises(BadRequest, match="candidate_times"):
            handler._compute_rectification_v5_vedastro_validate(request(candidate_times))


def test_passes_only_when_official_layers_discriminate_and_primary_is_strictly_better(monkeypatch):
    range_calls = []

    class Adapter:
        @staticmethod
        def run_rectification_minute_snapshot_for_case(case, case_id="user_chart"):
            return minute_snapshot(case)

        @staticmethod
        def run_range_scan_for_case(case, domain, start, end, case_id="user_chart"):
            range_calls.append((case["minute"], domain, start, end))
            lift = 3 if case["minute"] == 13 else 1
            return {
                "available": True,
                "status": "ok",
                "event_count": lift,
                "top_event": {"event_id": f"event-{domain}"},
                "evidence_ledger": [{"signal_lift": lift}],
                "raw_response": {"must_not": "leak"},
            }

    monkeypatch.setattr("scripts.jyotish_api_server._load_local_module", lambda name: Adapter)
    monkeypatch.setenv("VEDASTRO_API_KEY", "must-not-leak")

    result = object.__new__(JyotishAPIHandler)._compute_rectification_v5_vedastro_validate(request())

    assert result["status"] == "pass"
    assert result["passed"] is True
    assert result["can_confirm_exact_minute"] is False
    assert result["candidate_times"] == {"primary": "05:13", "runner_up": "05:14"}
    assert result["minute_sensitive_validation"]["discriminated"] is True
    assert result["event_validation"]["search_events_primary_supports_local_winner"] is True
    assert result["event_validation"]["supported_event_count"] == 3
    assert len(range_calls) == 6
    assert {call[1] for call in range_calls} == {"career", "marriage", "wealth"}
    serialized = str(result)
    assert "private" not in serialized
    assert "raw_request" not in serialized
    assert "raw_response" not in serialized
    assert "must-not-leak" not in serialized


@pytest.mark.parametrize("mutation", ["missing_source", "missing_layer"])
def test_missing_official_minute_response_cannot_pass(monkeypatch, mutation):
    class Adapter:
        @staticmethod
        def run_rectification_minute_snapshot_for_case(case, case_id="user_chart"):
            report = minute_snapshot(case)
            if mutation == "missing_source":
                report.pop("source")
            else:
                report["layers"].pop("D10")
            return report

        @staticmethod
        def run_range_scan_for_case(case, domain, start, end, case_id="user_chart"):
            lift = 3 if case["minute"] == 13 else 1
            return {
                "available": True,
                "status": "ok",
                "event_count": lift,
                "top_event": {"event_id": f"event-{domain}"},
                "evidence_ledger": [{"signal_lift": lift}],
            }

    monkeypatch.setattr("scripts.jyotish_api_server._load_local_module", lambda name: Adapter)
    result = object.__new__(JyotishAPIHandler)._compute_rectification_v5_vedastro_validate(request())

    assert result["status"] == "fail"
    assert result["passed"] is False
    assert result["can_confirm_exact_minute"] is False
    assert "vedastro_official_response_missing" in result["blockers"]


def test_identical_minute_layers_cannot_pass(monkeypatch):
    class Adapter:
        @staticmethod
        def run_rectification_minute_snapshot_for_case(case, case_id="user_chart"):
            return minute_snapshot(case, same=True)

        @staticmethod
        def run_range_scan_for_case(case, domain, start, end, case_id="user_chart"):
            return {
                "available": True,
                "status": "ok",
                "event_count": 1,
                "top_event": {"event_id": f"event-{domain}"},
                "evidence_ledger": [{"signal_lift": 1}],
            }

    monkeypatch.setattr("scripts.jyotish_api_server._load_local_module", lambda name: Adapter)
    result = object.__new__(JyotishAPIHandler)._compute_rectification_v5_vedastro_validate(request())

    assert result["status"] == "fail"
    assert result["passed"] is False
    assert result["can_confirm_exact_minute"] is False
    assert "vedastro_minute_sensitive_layers_not_discriminated" in result["blockers"]


def test_search_events_disagreement_is_diagnostic_and_cannot_reverse_local_winner(monkeypatch):
    class Adapter:
        @staticmethod
        def run_rectification_minute_snapshot_for_case(case, case_id="user_chart"):
            return minute_snapshot(case)

        @staticmethod
        def run_range_scan_for_case(case, domain, start, end, case_id="user_chart"):
            lift = 1 if case["minute"] == 13 else 3
            return {
                "available": True,
                "status": "ok",
                "event_count": lift,
                "top_event": {"event_id": f"event-{domain}"},
                "evidence_ledger": [{"signal_lift": lift}],
            }

    monkeypatch.setattr("scripts.jyotish_api_server._load_local_module", lambda name: Adapter)
    result = object.__new__(JyotishAPIHandler)._compute_rectification_v5_vedastro_validate(request())

    assert result["status"] == "pass"
    assert result["passed"] is True
    assert result["event_validation"]["search_events_primary_supports_local_winner"] is False
    assert result["blockers"] == []
    assert result["can_confirm_exact_minute"] is False


def test_timeout_is_returned_as_safe_failure(monkeypatch):
    class Adapter:
        @staticmethod
        def run_rectification_minute_snapshot_for_case(case, case_id="user_chart"):
            raise TimeoutError("secret upstream URL and key")

        @staticmethod
        def run_range_scan_for_case(case, domain, start, end, case_id="user_chart"):
            raise RuntimeError("secret raw response")

    monkeypatch.setattr("scripts.jyotish_api_server._load_local_module", lambda name: Adapter)
    result = object.__new__(JyotishAPIHandler)._compute_rectification_v5_vedastro_validate(request())

    assert result["status"] == "fail"
    assert result["passed"] is False
    assert result["can_confirm_exact_minute"] is False
    assert "vedastro_timeout" in result["blockers"]
    assert "vedastro_exception" in result["blockers"]
    assert "secret" not in str(result)
