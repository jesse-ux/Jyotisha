from scripts.vp_jain_shadbala_benchmark import build_report


def test_vp_jain_published_component_benchmark_is_fully_classified() -> None:
    report = build_report()

    assert report["case"]["name"] == "VP Jain published Shadbala example"
    assert report["source"] == {
        "upstream": "PyJHora V4.8.7 pvr_tests.py::shadbala_VPJainBook_tests",
        "upstream_commit": "ca22995709bd60e371e7820a1a5efc80ce4cf821",
        "upstream_url": "https://github.com/naturalstupid/PyJHora/blob/ca22995709bd60e371e7820a1a5efc80ce4cf821/src/jhora/tests/pvr_tests.py#L6853",
        "upstream_issue": None,
        "license_boundary": "AGPL-3.0 process-isolated numeric expectations only; no implementation copied.",
        "truth_status": "candidate_published_example_replay_not_independent_arbitration",
    }
    assert report["summary"]["row_count"] == 42
    assert report["summary"]["classified_count"] == 42
    assert report["summary"]["within_tolerance_count"] == 34
    assert report["summary"]["method_variant_count"] == 8


def test_vp_jain_benchmark_keeps_known_method_variants_explicit() -> None:
    rows = build_report()["rows"]
    variants = {(row["component"], row["planet"]): row for row in rows if row["status"] != "within_tolerance"}

    assert set(variants) == {
        ("sthana", "Sun"),
        ("sthana", "Mercury"),
        ("chesta", "Sun"),
        ("chesta", "Moon"),
        ("chesta", "Mars"),
        ("chesta", "Mercury"),
        ("chesta", "Jupiter"),
        ("chesta", "Saturn"),
    }
    assert variants[("sthana", "Sun")]["variant"] == "moolatrikona_degree_range_vs_whole_sign"
    assert variants[("chesta", "Moon")]["variant"] == "luminary_chesta_policy"
