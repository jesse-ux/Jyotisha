from __future__ import annotations

from datetime import datetime

from scripts import active_rectification_event_engine as event_engine
from scripts.active_rectification_events import (
    CandidateScoreRow,
    adjudicate_candidate_rows,
    precision_weight,
    score_life_events,
)
from scripts.rectification.scoring_service import build_event_contribution_matrix


def _row(time: str, score: float) -> CandidateScoreRow:
    return {
        "time": time,
        "score": score,
        "evidence": [],
        "missing_layers": [],
    }


def test_locally_stable_high_evidence_candidate_can_enter_external_validation() -> None:
    result = adjudicate_candidate_rows(
        [_row(f"14:{minute:02d}", 20 if minute == 25 else 10) for minute in range(20, 31)],
        event_count=4,
        domain_count=3,
        request_fingerprint="high-fixture",
        leave_one_event_out={"status": "pass", "runs": []},
    )

    assert result["confidence"] == "high"
    assert result["can_apply"] is True
    assert result["winning_segment"] == {
        "start_time": "14:25",
        "end_time": "14:25",
        "representative_time": "14:25",
        "width_minutes": 1,
    }
    assert result["margin_percent"] == 50.0
    assert result["stability_diagnostics"]["neighbor_stability"]["all_required_passed"] is True
    assert result["candidate_ranking_summary"][:2] == [
        {"rank": 1, "time": "14:25", "score": 20, "tied_minute_count": 1},
        {"rank": 2, "time": "14:24", "score": 10, "tied_minute_count": 10},
    ]


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


def test_neighbor_diagnostics_require_both_sides_at_1_2_and_5_minutes() -> None:
    rows = [_row(f"10:{minute:02d}", 20 if minute == 5 else 10) for minute in range(11)]
    result = adjudicate_candidate_rows(
        rows,
        event_count=4,
        domain_count=3,
        request_fingerprint="two-sided-neighbor-fixture",
        leave_one_event_out={"status": "pass", "runs": []},
    )

    diagnostics = result["stability_diagnostics"]["neighbor_stability"]
    assert diagnostics["all_required_passed"] is True
    assert [item["radius_minutes"] for item in diagnostics["neighborhoods"]] == [1, 2, 5]


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


def test_matrix_legacy_adapter_preserves_event_kind() -> None:
    seen = []

    def rows(value):
        event = value["events"][0]
        seen.append(event["event_kind"])
        return [{
            "time": "05:13",
            "score": 1.0,
            "evidence": [{
                "event_id": event["id"],
                "domain": event["domain"],
                "candidate_time": "05:13",
                "rule_ids": [f"event_kind:{event['event_kind']}"],
                "points": 1.0,
            }],
            "missing_layers": [],
        }]

    build_event_contribution_matrix({
        "birth_date": "1993-04-17",
        "start_time": "05:13",
        "end_time": "05:13",
        "lat": 36.683333,
        "lon": 114.35,
        "tz": 8.0,
        "events": [{
            "id": "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
            "domain": "relationship",
            "event_kind": "relationship_end",
            "date_start": "2021-01-01",
            "date_end": "2021-01-01",
            "precision": "day",
        }],
    }, row_provider=rows)

    assert seen == ["relationship_end"]


def test_relationship_event_kinds_have_distinct_traceable_contributions(monkeypatch) -> None:
    monkeypatch.setattr(
        event_engine.functional_benefics,
        "derive_functional_benefic_malefic",
        lambda _sign: {"functional_benefics": [], "functional_malefics": []},
    )
    common = {
        "candidate_time": "05:13",
        "natal_chart": {"ascendant": {"lon": 0.0, "sign": "Aries"}, "planets": {}},
        "varga_charts": [],
        "vimshottari": ("Sun", "Moon", "Mars"),
        "narayana": (None, None),
        "arudha_padas": {},
    }

    evidence = {
        kind: event_engine._score_event(
            **common,
            event={
                "id": kind,
                "domain": "relationship",
                "event_kind": kind,
                "date": "2021-01-01",
                "precision": "day",
            },
        )
        for kind in ("relationship_start", "relationship_end", "relationship_change")
    }

    assert {item["points"] for item in evidence.values()} == {0.001, 0.002, 0.003}
    for kind, item in evidence.items():
        assert f"event_kind:{kind}" in item["rule_ids"]


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
    assert result["algorithm_version"] == "birth-time-event-scoring-v2"
    assert result["confidence"] in {"low", "medium"}
    assert result["canonical_input_hash"]
    assert result["calculation_contract"]["calculation"] == {
        "ayanamsa": "lahiri",
        "node_mode": "mean",
        "ephemeris_source": "swisseph_calc_ut",
    }
    assert len(result["stability_diagnostics"]["leave_one_event_out"]["runs"]) == 3


def test_event_summary_is_fingerprinted_without_unlocking_minute_application() -> None:
    base_request = {
        "birth_date": "1993-04-17",
        "start_time": "14:29",
        "end_time": "14:30",
        "lat": 36.683333,
        "lon": 114.35,
        "tz": 8.0,
        "events": [{
            "id": "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
            "domain": "career",
            "event_kind": "career_change",
            "date": "2019-07",
            "precision": "month",
            "summary": "2019 年 7 月第一次承担团队管理职责",
        }],
    }
    changed_request = {
        **base_request,
        "events": [{
            **base_request["events"][0],
            "summary": "2019 年 7 月离开原公司并开始独立创业",
        }],
    }

    contract, input_hash = event_engine._canonical_input_contract(base_request)
    _, changed_hash = event_engine._canonical_input_contract(changed_request)
    result = event_engine.adjudicate_event_candidate_rows(
        base_request,
        [_row("14:29", 10), _row("14:30", 8)],
    )

    assert contract["schema_version"] == "rectification-candidate-input-v2"
    assert contract["events"][0]["event_kind"] == "career_change"
    assert contract["events"][0]["summary"] == "2019 年 7 月第一次承担团队管理职责"
    assert changed_hash != input_hash
    assert result["canonical_input_hash"] == input_hash
    assert result["can_apply"] is False
    assert "insufficient_events" in result["reasons"]


def test_finance_events_use_d2_d11_and_recompute_both_dashas_per_minute(monkeypatch) -> None:
    calls = {"vimshottari": 0, "narayana": 0, "varga_counts": []}
    original_score_event = event_engine._score_event

    def vimshottari(*_args):
        calls["vimshottari"] += 1
        return "Sun", "Moon", "Mars"

    def narayana(*_args):
        calls["narayana"] += 1
        return 0, 1

    def score_event(**kwargs):
        calls["varga_counts"].append(len(kwargs["varga_charts"]))
        return original_score_event(**kwargs)

    monkeypatch.setattr(event_engine, "_active_vimshottari", vimshottari)
    monkeypatch.setattr(event_engine, "_active_narayana", narayana)
    monkeypatch.setattr(event_engine, "_score_event", score_event)
    result = event_engine.compute_event_candidate_result({
        "birth_date": "1993-04-17",
        "start_time": "14:29",
        "end_time": "14:31",
        "lat": 36.683333,
        "lon": 114.35,
        "tz": 8.0,
        "events": [{
            "id": "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
            "domain": "finance",
            "date": "2020-08",
            "precision": "month",
        }],
    })

    assert result["event_count"] == 1
    assert calls == {"vimshottari": 3, "narayana": 3, "varga_counts": [2, 2, 2]}


def test_missing_narayana_blocks_the_candidate_event_instead_of_using_partial_timing(monkeypatch) -> None:
    monkeypatch.setattr(event_engine, "_active_narayana", lambda *_args: (None, None))
    request = {
        "birth_date": "1993-04-17",
        "start_time": "14:29",
        "end_time": "14:29",
        "lat": 36.683333,
        "lon": 114.35,
        "tz": 8.0,
        "events": [{
            "id": "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
            "domain": "career",
            "date": "2019-07-01",
            "precision": "day",
        }],
    }
    context = event_engine.build_candidate_static_context(request, datetime(1993, 4, 17, 14, 29))
    row = event_engine._candidate_row(request, context)

    assert row["evidence"] == []
    assert row["score"] == 0
    assert "Narayana_MD_AD" in row["missing_layers"]

    result = event_engine.compute_event_candidate_result({
        "birth_date": "1993-04-17",
        "start_time": "14:29",
        "end_time": "14:30",
        "lat": 36.683333,
        "lon": 114.35,
        "tz": 8.0,
        "events": [{
            "id": "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
            "domain": "career",
            "date": "2019-07-01",
            "precision": "day",
        }],
    })
    assert "Narayana_MD_AD" in result["missing_layers"]
    assert "missing_mandatory_layers" in result["reasons"]


def test_relationship_scoring_receives_computed_ul(monkeypatch) -> None:
    seen_ul = []
    original_score_event = event_engine._score_event

    def score_event(**kwargs):
        seen_ul.append(kwargs["arudha_padas"].get("UL"))
        return original_score_event(**kwargs)

    monkeypatch.setattr(event_engine, "_score_event", score_event)
    request = {
        "birth_date": "1993-04-17",
        "start_time": "14:29",
        "end_time": "14:29",
        "lat": 36.683333,
        "lon": 114.35,
        "tz": 8.0,
        "events": [{
            "id": "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
            "domain": "relationship",
            "date": "2021",
            "precision": "year",
        }],
    }
    context = event_engine.build_candidate_static_context(request, datetime(1993, 4, 17, 14, 29))
    event_engine._candidate_row(request, context)

    assert seen_ul and seen_ul[0]["sign_idx"] >= 0
