from __future__ import annotations

from scripts.public_real_case_negative_controls import (
    generate_control_dates,
    rank_positive_against_controls,
    summarize_negative_control_rows,
)


def test_generate_control_dates_uses_fixed_offsets_without_positive_date() -> None:
    dates = generate_control_dates("2018-05-19", offsets=(-60, -30, 30, 60))

    assert dates == ["2018-03-20", "2018-04-19", "2018-06-18", "2018-07-18"]
    assert "2018-05-19" not in dates


def test_rank_positive_uses_conservative_tie_ordering() -> None:
    result = rank_positive_against_controls(5, [7, 5, 4])

    assert result == {
        "positive_score": 5,
        "positive_rank": 3,
        "candidate_count": 4,
        "reciprocal_rank": 1 / 3,
        "top_1": False,
        "top_3": True,
        "max_control_score": 7,
        "score_margin": -2,
    }


def test_negative_control_summary_reports_false_activations() -> None:
    summary = summarize_negative_control_rows(
        [
            {
                "ranking": {"top_1": True, "top_3": True, "reciprocal_rank": 1.0, "score_margin": 2},
                "controls": [{"score": 2}, {"score": 3}],
            },
            {
                "ranking": {"top_1": False, "top_3": True, "reciprocal_rank": 0.5, "score_margin": -1},
                "controls": [{"score": 4}, {"score": 7}],
            },
        ]
    )

    assert summary["case_count"] == 2
    assert summary["control_date_count"] == 4
    assert summary["control_activation_rate"] == 0.5
    assert summary["control_strong_activation_rate"] == 0.25
    assert summary["positive_top_1_rate"] == 0.5
    assert summary["positive_top_3_rate"] == 1.0
    assert summary["mean_reciprocal_rank"] == 0.75
    assert summary["mean_score_margin"] == 0.5
