from scripts.minute_candidate_discriminability import analyze_candidate_rows, feature_fingerprint


def _row(time: str, points: float, rules: list[str] | None = None) -> dict:
    return {
        "time": time,
        "score": points,
        "evidence": [{
            "event_id": "event-1",
            "domain": "career",
            "candidate_time": time,
            "rule_ids": rules or ["same_rule"],
            "points": points,
        }],
        "missing_layers": [],
    }


def test_fingerprint_excludes_candidate_time_but_includes_evidence_features() -> None:
    assert feature_fingerprint(_row("10:00", 1.0)) == feature_fingerprint(_row("10:01", 1.0))
    assert feature_fingerprint(_row("10:00", 1.0)) != feature_fingerprint(_row("10:00", 2.0))


def test_diagnostic_reports_equivalent_adjacent_minutes() -> None:
    report = analyze_candidate_rows([
        _row("10:00", 1.0),
        _row("10:01", 1.0),
        _row("10:02", 2.0, ["different_rule"]),
    ])

    assert report["unique_feature_fingerprint_count"] == 2
    assert report["indistinguishable_adjacent_pair_count"] == 1
    assert report["adjacent_transitions"][0]["feature_changed"] is False
    assert report["adjacent_transitions"][0]["changed_event_ids"] == []
    assert report["top_candidate_feature_unique"] is True
    assert report["status"] == "minute_feature_unique"


def test_diagnostic_blocks_a_fully_equivalent_range() -> None:
    report = analyze_candidate_rows([_row("10:00", 1.0), _row("10:01", 1.0)])

    assert report["distinguishable_candidate_ratio"] == 0.5
    assert report["top_candidate_feature_unique"] is False
    assert report["status"] == "blocked_feature_equivalent_range"
