from scripts.tajika_kernel import calculate_tajika_interactions


def _seven():
    return {
        "Sun": {"longitude": 0, "speed": 1.0}, "Moon": {"longitude": 49, "speed": 13.0},
        "Mars": {"longitude": 180, "speed": 0.5}, "Mercury": {"longitude": 260, "speed": 1.2},
        "Jupiter": {"longitude": 310, "speed": 0.08}, "Venus": {"longitude": 130, "speed": 1.0},
        "Saturn": {"longitude": 220, "speed": 0.03}, "Rahu": {"longitude": 60, "speed": -0.05},
    }


def test_kernel_detects_cross_sign_aspect_and_excludes_nodes():
    result = calculate_tajika_interactions(_seven())

    pair = next(row for row in result["interactions"] if row["planets"] == ["Sun", "Moon"])
    assert pair["aspect"] == 60.0
    assert pair["motion"] == "applying"
    candidate = next(row for row in result["candidate_yogas"] if row["planets"] == ["Sun", "Moon"])
    assert candidate["name"] == "Ithasala_candidate"
    assert candidate["status"] == "partial"
    assert result["nodes_excluded"] is True
    assert all("Rahu" not in row["planets"] for row in result["interactions"])


def test_kernel_blocks_missing_speed_instead_of_guessing_motion():
    planets = _seven()
    del planets["Venus"]["speed"]

    result = calculate_tajika_interactions(planets)

    assert result["status"] == "blocked"
    assert "Venus" in result["missing"]
