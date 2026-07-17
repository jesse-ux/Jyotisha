from scripts.timing_negative_holdout_audit import build_report


def test_timing_negative_holdout_blocks_positive_only_sources() -> None:
    report = build_report(
        [
            {
                "name": "positive-only public timeline",
                "positive_events": True,
                "explicit_non_event_intervals": False,
                "independent_human_reviewed": False,
                "observed_before_preregistration": False,
            }
        ]
    )

    assert report["claim_status"] == "exploratory_unvalidated"
    assert report["production_tuning_allowed"] is False
    assert report["sources"][0]["usable_for_promotion"] is False
    assert "missing_explicit_non_event_intervals" in report["sources"][0]["blockers"]


def test_timing_negative_holdout_can_only_promote_locked_independent_labels() -> None:
    report = build_report(
        [
            {
                "name": "locked blind label packet",
                "positive_events": True,
                "explicit_non_event_intervals": True,
                "independent_human_reviewed": True,
                "observed_before_preregistration": False,
            }
        ]
    )

    assert report["claim_status"] == "ready_for_blind_holdout"
    assert report["production_tuning_allowed"] is True
    assert report["sources"][0]["blockers"] == []
