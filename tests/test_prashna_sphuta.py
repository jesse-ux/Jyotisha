from scripts.prashna_sphuta import calculate_sphuta_evidence


def test_sphuta_formula_evidence_uses_exact_gulika_input() -> None:
    result = calculate_sphuta_evidence(
        ascendant_longitude=10,
        planet_longitudes={"Moon": 20, "Sun": 30, "Rahu": 40},
        gulika_longitude=50,
    )

    assert result["status"] == "partial"
    assert result["points"] == {"trisphuta": 80.0, "catusphuta": 110.0, "pancasphuta": 150.0}


def test_sphuta_evidence_blocks_missing_required_planet() -> None:
    result = calculate_sphuta_evidence(
        ascendant_longitude=10,
        planet_longitudes={"Moon": 20, "Sun": 30},
        gulika_longitude=50,
    )

    assert result["status"] == "blocked"
    assert result["missing"] == ["Rahu"]
