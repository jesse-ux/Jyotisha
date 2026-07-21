from scripts.minute_rectification_fact_blind_eval_v4 import _would_confirm


def test_v4_holdout_confirmation_requires_every_non_release_gate() -> None:
    result = {
        "confidence": "high",
        "winning_segment": {
            "start_time": "10:01",
            "end_time": "10:01",
            "representative_time": "10:01",
            "width_minutes": 1,
        },
        "reasons": ["fact_ranker_v4_holdout_not_ready"],
        "missing_layers": [],
    }

    assert _would_confirm(result) is True
    assert _would_confirm({**result, "reasons": [
        "leave_one_event_out_not_passed", "fact_ranker_v4_holdout_not_ready",
    ]}) is False
    assert _would_confirm({**result, "missing_layers": ["D10"]}) is False
