from scripts.pyjhora_multi_case_panchanga_gulika_replay import build_report


def test_pyjhora_multi_case_replay_is_observation_only() -> None:
    report = build_report()
    assert report["claim_status"] == "observation_only"
    assert report["production_tuning_allowed"] is False
    assert report["truth_matrix_allowed"] is False
    assert len(report["cases"]) == 3
    for case in report["cases"]:
        assert case["raw_sha256"]
        assert set(case["pyjhora_raw"]) >= {"gulika", "maandi", "tithi", "nakshatra", "yogam", "karana"}
        assert set(case["field_comparison"]) == {"tithi", "nakshatra", "yogam", "gulika"}
