from scripts.dynamic_rectification_fact_priority import (
    EVENT_FACT_PRIORITY_VERSION,
    FACT_PRIORITY_VERSION,
    build_domain_fact_priorities,
    build_historical_event_priorities,
)


def test_real_domain_fact_priorities_are_shadow_only_and_bounded() -> None:
    priorities = build_domain_fact_priorities({
        "birth_date": "1993-04-17",
        "start_time": "14:29",
        "end_time": "14:31",
        "lat": 36.683333,
        "lon": 114.35,
        "tz": 8.0,
        "events": [],
    })

    assert set(priorities) == {
        "education", "relocation", "relationship", "career", "health_pressure",
    }
    assert all(item["fact_priority_version"] == FACT_PRIORITY_VERSION for item in priorities.values())
    assert all(0 <= item["selection_priority"] <= 1 for item in priorities.values())
    assert all(item["shadow_only"] is True for item in priorities.values())
    assert all(item["may_affect_candidate_score"] is False for item in priorities.values())


def test_historical_event_priority_preserves_vimshottari_actor_difference() -> None:
    priorities = build_historical_event_priorities({
        "birth_date": "1879-03-14",
        "start_time": "11:24",
        "end_time": "11:25",
        "lat": 48.4011,
        "lon": 9.9876,
        "tz": 0.66584,
        "historical_events": [{
            "id": "11111111-1111-4111-8111-111111111111",
            "domain": "career",
            "date": "1922",
            "precision": "year",
        }],
    })

    career = priorities["career"]
    assert career["event_fact_priority_version"] == EVENT_FACT_PRIORITY_VERSION
    assert career["selection_priority"] > 0
    assert career["discriminating_event_ids"] == ["11111111-1111-4111-8111-111111111111"]
    assert career["shadow_only"] is True
    assert career["may_affect_candidate_score"] is False
