from scripts.minute_rectification_pairwise_v3 import rank_candidate_rows, score_pairwise_v3


def _events() -> list[dict]:
    return [
        {"id": "career-1", "domain": "career", "date": "2000", "precision": "year"},
        {"id": "career-2", "domain": "career", "date": "2001", "precision": "year"},
        {"id": "relationship-1", "domain": "relationship", "date": "2002", "precision": "year"},
    ]


def _row(time: str, values: dict[str, float]) -> dict:
    domains = {event["id"]: event["domain"] for event in _events()}
    return {
        "time": time,
        "score": sum(values.values()),
        "evidence": [
            {
                "event_id": event_id,
                "domain": domains[event_id],
                "candidate_time": time,
                "rule_ids": [f"rule-{event_id}"],
                "points": points,
            }
            for event_id, points in values.items()
        ],
        "missing_layers": [],
    }


def test_constant_event_contributes_zero_to_every_candidate() -> None:
    events = [{"id": "career-1", "domain": "career", "date": "2000", "precision": "year"}]
    rows = [
        _row("10:00", {"career-1": 5.0}),
        _row("10:01", {"career-1": 5.0}),
    ]

    ranked, contract = rank_candidate_rows(rows, events)

    assert [row["score"] for row in ranked] == [0.0, 0.0]
    assert contract["constant_event_ids"] == ["career-1"]
    assert contract["discriminating_event_ids"] == []


def test_repeated_career_events_do_not_outvote_relationship_domain() -> None:
    rows = [
        _row("10:00", {"career-1": 10, "career-2": 10, "relationship-1": 0}),
        _row("10:01", {"career-1": 0, "career-2": 0, "relationship-1": 10}),
    ]

    ranked, contract = rank_candidate_rows(rows, _events())

    assert [row["score"] for row in ranked] == [50.0, 50.0]
    assert contract["candidate_domain_scores"]["10:00"] == {"career": 1.0, "relationship": 0.0}
    assert contract["candidate_domain_scores"]["10:01"] == {"career": 0.0, "relationship": 1.0}


def test_v3_never_opens_confirmation_without_new_holdout() -> None:
    rows = [
        _row("09:55", {"career-1": 0, "career-2": 0, "relationship-1": 0}),
        _row("09:56", {"career-1": 1, "career-2": 1, "relationship-1": 1}),
        _row("09:57", {"career-1": 2, "career-2": 2, "relationship-1": 2}),
        _row("09:58", {"career-1": 3, "career-2": 3, "relationship-1": 3}),
        _row("09:59", {"career-1": 4, "career-2": 4, "relationship-1": 4}),
        _row("10:00", {"career-1": 10, "career-2": 10, "relationship-1": 10}),
        _row("10:01", {"career-1": 4, "career-2": 4, "relationship-1": 4}),
        _row("10:02", {"career-1": 3, "career-2": 3, "relationship-1": 3}),
        _row("10:03", {"career-1": 2, "career-2": 2, "relationship-1": 2}),
        _row("10:04", {"career-1": 1, "career-2": 1, "relationship-1": 1}),
        _row("10:05", {"career-1": 0, "career-2": 0, "relationship-1": 0}),
    ]

    result = score_pairwise_v3(rows, _events())

    assert result["winning_segment"]["representative_time"] == "10:00"
    assert result["can_apply"] is False
    assert "pairwise_v3_holdout_not_ready" in result["reasons"]
