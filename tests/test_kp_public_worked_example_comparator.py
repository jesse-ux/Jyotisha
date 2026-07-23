from __future__ import annotations

from scripts.kp_public_worked_example_comparator import build_report


def test_ezine_159_fifth_cusp_matches_vedicastro_with_declared_tolerance() -> None:
    report = build_report({
        "HouseNr": 5,
        "LonDecDeg": 69.132,
        "Rasi": "Gemini",
        "RasiLord": "Mercury",
        "Nakshatra": "Ardra",
        "NakshatraLord": "Rahu",
        "SubLord": "Jupiter",
        "SubSubLord": "Saturn",
    }, observed_ayanamsa_degrees=23.529441857)

    assert report["status"] == "public_kp_worked_example_partial_field_match"
    assert report["claim_status"] == "observation_only"
    assert report["truth_matrix_allowed"] is False
    assert report["summary"]["matched_field_count"] == 6
    assert report["summary"]["mismatched_field_count"] == 0
    assert report["summary"]["longitude_within_tolerance"] is True
    assert report["comparison"]["longitude_delta_arcseconds"] == 41.2
    assert report["comparison"]["ayanamsa_delta_arcseconds"] == 43.0
