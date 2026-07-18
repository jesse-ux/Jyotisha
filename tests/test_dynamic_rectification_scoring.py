from __future__ import annotations

from uuid import uuid4

import pytest

from scripts import dynamic_rectification
from scripts import jyotish_api_server as api_server


def _score_request() -> dict:
    return {
        "birth_date": "1990-01-01",
        "start_time": "05:30",
        "end_time": "05:33",
        "lat": 31.23,
        "lon": 121.47,
        "tz": 8.0,
        "choice_evidence": [],
    }


def _decisive_rows() -> list[dict]:
    return [
        {"time": "05:30", "score": 20.0},
        {"time": "05:31", "score": 20.0},
        {"time": "05:32", "score": 20.0},
        {"time": "05:33", "score": 10.0},
    ]


def _evidence(**changes) -> dict:
    return {
        "question_id": str(uuid4()),
        "opportunity_id": "career-window",
        "partition_id": "career-2020-2022",
        "dimension_code": "career",
        "candidate_scores": {"05:30": 0.0, "05:31": 1.0, "05:32": 1.0, "05:33": 0.0},
        "information_gain": 0.5,
        **changes,
    }


def _handler() -> api_server.JyotishAPIHandler:
    handler = api_server.JyotishAPIHandler.__new__(api_server.JyotishAPIHandler)
    handler.headers = {}
    return handler


def test_dynamic_routes_fail_closed_and_compare_wrong_bearers_in_constant_time(
    monkeypatch,
) -> None:
    handler = _handler()
    monkeypatch.delenv("JYOTISH_DYNAMIC_RECTIFICATION_TOKEN", raising=False)
    with pytest.raises(api_server.Forbidden, match="token"):
        handler._compute_dynamic_rectification_score({})

    calls: list[tuple[str, str]] = []
    original = api_server.secrets.compare_digest
    monkeypatch.setattr(
        api_server.secrets,
        "compare_digest",
        lambda supplied, configured: calls.append((supplied, configured))
        or original(supplied, configured),
    )
    monkeypatch.setenv("JYOTISH_DYNAMIC_RECTIFICATION_TOKEN", "server-secret")
    handler.headers = {"Authorization": "Bearer wrong-secret"}
    with pytest.raises(api_server.Forbidden, match="token"):
        handler._compute_dynamic_rectification_opportunities({})
    assert calls == [("wrong-secret", "server-secret")]


def test_unauthenticated_forged_scores_cannot_obtain_an_applicable_result(monkeypatch) -> None:
    monkeypatch.setenv("JYOTISH_DYNAMIC_RECTIFICATION_TOKEN", "server-secret")
    scores = {"05:30": 10_000.0, "05:31": 0.0, "05:32": 0.0, "05:33": 0.0}
    evidence = [
        _evidence(
            question_id=f"question-{index}",
            opportunity_id=f"opportunity-{index}",
            partition_id=f"partition-{index}",
            dimension_code=dimension,
            candidate_scores=scores,
            information_gain=1.0,
        )
        for index, dimension in enumerate(
            ["career", "relationship", "education", "career"], start=1
        )
    ]
    with pytest.raises(api_server.Forbidden, match="token"):
        _handler()._compute_dynamic_rectification_score({
            **_score_request(), "choice_evidence": evidence,
        })


def test_dynamic_routes_are_not_browser_runnable_technique_examples() -> None:
    endpoints = {
        "/api/dynamic_rectification_opportunities",
        "/api/dynamic_rectification_score",
    }
    assert endpoints.isdisjoint(api_server.TECHNIQUE_EXAMPLE_ENDPOINTS)
    assert endpoints.isdisjoint(api_server.API_COMMAND_MAP.values())
    for endpoint in endpoints:
        with pytest.raises(KeyError):
            _handler()._dispatch_technique_endpoint(endpoint, {})


def test_primary_choice_changes_rankings_and_returns_a_real_range() -> None:
    result = dynamic_rectification.score_choice_evidence(
        {**_score_request(), "choice_evidence": [_evidence()]}
    )

    assert result["effective_answer_count"] == 1
    assert result["winning_segment"] == {
        "start_time": "05:31",
        "end_time": "05:32",
        "representative_time": "05:31",
        "width_minutes": 2,
    }
    assert result["can_apply"] is False
    assert result["evidence"] == []


def test_score_accepts_candidate_membership_independent_of_json_key_order() -> None:
    scores = {"05:33": 0.0, "05:32": 1.0, "05:31": 1.0, "05:30": 0.0}
    result = dynamic_rectification.score_choice_evidence(
        {**_score_request(), "choice_evidence": [_evidence(candidate_scores=scores)]}
    )

    assert result["winning_segment"]["start_time"] == "05:31"


def test_cross_midnight_leaders_form_one_chronological_segment() -> None:
    scores = {"23:58": 0.0, "23:59": 1.0, "00:00": 1.0, "00:01": 0.0}
    evidence = [
        _evidence(
            question_id=f"question-{index}",
            opportunity_id=f"opportunity-{index}",
            partition_id=f"partition-{index}",
            dimension_code=dimension,
            candidate_scores=scores,
            information_gain=1.0,
        )
        for index, dimension in enumerate(
            ["career", "relationship", "education", "career"], start=1
        )
    ]
    result = dynamic_rectification.score_choice_evidence({
        **_score_request(),
        "start_time": "23:58",
        "end_time": "00:01",
        "choice_evidence": evidence,
    })

    assert result["confidence"] == "high"
    assert result["winning_segment"] == {
        "start_time": "23:59",
        "end_time": "00:00",
        "representative_time": "23:59",
        "width_minutes": 2,
    }


def test_opaque_trimmed_question_ids_are_valid_and_duplicates_remain_rejected() -> None:
    evidence = _evidence(question_id="  question-career-window  ")
    result = dynamic_rectification.score_choice_evidence(
        {**_score_request(), "choice_evidence": [evidence]}
    )
    assert result["effective_answer_count"] == 1

    with pytest.raises(ValueError, match="duplicate question"):
        dynamic_rectification.score_choice_evidence({
            **_score_request(),
            "choice_evidence": [
                evidence,
                {**evidence, "question_id": "question-career-window"},
            ],
        })


def test_unknown_and_unmatched_are_never_choice_evidence() -> None:
    with pytest.raises(ValueError, match="partition evidence"):
        dynamic_rectification.score_choice_evidence(
            {**_score_request(), "choice_evidence": [{"kind": "unknown"}]}
        )


def test_high_confidence_requires_versioned_hard_gates() -> None:
    result = dynamic_rectification.adjudicate_choice_rows(
        _decisive_rows(),
        effective_answer_count=4,
        dimension_count=3,
        missing_layers=[],
    )

    assert result["confidence"] == "high"
    assert result["can_apply"] is True
    assert result["winning_segment"]["width_minutes"] <= 5
    assert result["margin_percent"] >= 20
    assert result["algorithm_version"] == "birth-time-choice-scoring-v2"


def test_medium_and_missing_layers_never_allow_application() -> None:
    medium = dynamic_rectification.adjudicate_choice_rows(
        _decisive_rows(), effective_answer_count=3, dimension_count=2, missing_layers=[]
    )
    blocked = dynamic_rectification.adjudicate_choice_rows(
        _decisive_rows(),
        effective_answer_count=4,
        dimension_count=3,
        missing_layers=["D10"],
    )

    assert medium["confidence"] == "medium"
    assert medium["can_apply"] is False
    assert blocked["confidence"] == "low"
    assert blocked["can_apply"] is False


def test_score_rejects_client_fields_duplicates_caps_and_invalid_scores() -> None:
    evidence = _evidence()
    with pytest.raises(ValueError, match="option_id"):
        dynamic_rectification.score_choice_evidence({
            **_score_request(), "choice_evidence": [{**evidence, "option_id": "client"}],
        })
    with pytest.raises(ValueError, match="duplicate question"):
        dynamic_rectification.score_choice_evidence(
            {**_score_request(), "choice_evidence": [evidence, evidence]}
        )
    with pytest.raises(ValueError, match="at most 10"):
        dynamic_rectification.score_choice_evidence({
            **_score_request(),
            "choice_evidence": [
                {**evidence, "question_id": str(uuid4())} for _ in range(11)
            ],
        })
    with pytest.raises(ValueError, match="candidate scores"):
        dynamic_rectification.score_choice_evidence({
            **_score_request(),
            "choice_evidence": [_evidence(candidate_scores={
                **evidence["candidate_scores"], "05:34": 1.0,
            })],
        })
    with pytest.raises(ValueError, match="candidate scores"):
        dynamic_rectification.score_choice_evidence({
            **_score_request(),
            "choice_evidence": [_evidence(candidate_scores={
                **evidence["candidate_scores"], "05:30": -1.0,
            })],
        })
    with pytest.raises(ValueError, match="identifier"):
        dynamic_rectification.score_choice_evidence(
            {**_score_request(), "choice_evidence": [_evidence(partition_id="")]}
        )
