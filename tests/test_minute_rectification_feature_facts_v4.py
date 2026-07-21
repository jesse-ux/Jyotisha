from datetime import datetime

from scripts.minute_rectification_feature_facts_v4 import (
    FEATURE_CONTRACT_VERSION,
    analyze_feature_fact_rows,
    build_fact_difference_opportunities,
    build_feature_fact_rows,
    feature_fact_fingerprint,
)


def _fact_row(time: str, ad_lord: str) -> dict:
    return {
        "time": time,
        "feature_contract_version": FEATURE_CONTRACT_VERSION,
        "event_facts": [{
            "event_id": "career-event",
            "domain": "career",
            "vimshottari": {"md": "Sun", "ad": ad_lord, "pd": "Mercury"},
        }],
        "missing_layers": [],
    }


def test_fact_fingerprint_ignores_time_but_preserves_dasha_actor_identity() -> None:
    assert feature_fact_fingerprint(_fact_row("10:00", "Moon")) == feature_fact_fingerprint(
        _fact_row("10:01", "Moon")
    )
    assert feature_fact_fingerprint(_fact_row("10:00", "Moon")) != feature_fact_fingerprint(
        _fact_row("10:00", "Mars")
    )


def test_fact_audit_exposes_change_hidden_by_generic_rule_name() -> None:
    report = analyze_feature_fact_rows([
        _fact_row("10:00", "Moon"),
        _fact_row("10:01", "Mars"),
    ])

    assert report["unique_feature_fingerprint_count"] == 2
    assert report["indistinguishable_adjacent_pair_count"] == 0
    assert report["adjacent_transitions"][0]["changed_event_ids"] == ["career-event"]
    assert report["shadow_only"] is True
    assert report["may_affect_candidate_score"] is False

    opportunities = build_fact_difference_opportunities([
        _fact_row("10:00", "Moon"),
        _fact_row("10:01", "Mars"),
    ])
    assert len(opportunities) == 1
    assert opportunities[0]["event_id"] == "career-event"
    assert [item["candidate_times"] for item in opportunities[0]["partitions"]] == [
        ["10:00"], ["10:01"],
    ]
    assert opportunities[0]["may_score_candidates"] is False
    assert opportunities[0]["question_ready"] is True
    assert opportunities[0]["requires_partition_coalescing"] is False


def test_real_fact_rows_include_dual_dasha_varga_arudha_av_and_shadbala() -> None:
    rows = build_feature_fact_rows({
        "birth_date": "1993-04-17",
        "start_time": "14:29",
        "end_time": "14:30",
        "lat": 36.683333,
        "lon": 114.35,
        "tz": 8.0,
        "events": [{
            "id": "career-event",
            "domain": "career",
            "date": "2019-07-01",
            "precision": "day",
        }],
    }, candidates=[datetime(1993, 4, 17, 14, 29), datetime(1993, 4, 17, 14, 30)])

    fact = rows[0]["event_facts"][0]
    assert set(fact["vimshottari"]) == {"md", "ad", "pd"}
    assert set(fact["narayana"]) == {"md_sign", "ad_sign"}
    assert fact["vargas"][0]["chart"] == "D10"
    assert "A10" in fact["arudha_signs"]
    assert "10" in fact["ashtakavarga_target_house_scores"]
    assert isinstance(fact["verified_shadbala_state"], list)
    assert all(row["feature_contract_version"] == FEATURE_CONTRACT_VERSION for row in rows)
