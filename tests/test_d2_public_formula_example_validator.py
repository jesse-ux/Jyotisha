from __future__ import annotations

from scripts.d2_public_formula_example_validator import build_report


def test_public_d2_formula_examples_match_local_parashara_mapping() -> None:
    report = build_report()

    assert report["status"] == "secondary_formula_examples_support_local_parashara_mapping"
    assert report["claim_status"] == "observation_only"
    assert report["truth_matrix_allowed"] is False
    assert report["summary"] == {
        "example_count": 4,
        "local_parashara_match_count": 4,
        "jyotishyamitra_sequential_match_count": 0,
    }
    assert [row["expected_sign"] for row in report["examples"]] == ["Leo", "Leo", "Cancer", "Cancer"]
    assert {row["local_engine_source"] for row in report["examples"]} == {
        "scripts.divisional_charts_extended.DivisionalChartsCalculator._calculate_d2",
    }
    assert all(row["local_parashara_matches"] for row in report["examples"])
    assert not any(row["jyotishyamitra_sequential_matches"] for row in report["examples"])
