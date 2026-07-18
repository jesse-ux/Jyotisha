from scripts.western_real_case_calibration import build_case


def test_jobs_public_case_replays_progressed_angles_and_parans() -> None:
    report = build_case("jobs_iphone_2007")

    assert report["status"] == "calculated_not_predictive_validation"
    assert report["event"]["source"]["source_grade"] == "primary"
    assert report["birth_source"]["time_accuracy_rating"] == "AA"
    assert report["layers"]["secondary_progressions"]["progressed_angles"]["status"] == "used"
    assert report["layers"]["parans"]["status"] == "used"
    assert report["summary"]["paran_event_count"] > 0
    assert "cannot establish" in report["boundary"]


def test_unknown_case_is_blocked() -> None:
    assert build_case("missing")["reason"] == "case_id_not_found"
