from scripts.vp_jain_shadbala_benchmark import build_report


def test_vp_jain_published_component_benchmark_is_fully_classified() -> None:
    report = build_report()

    assert report["case"]["name"] == "VP Jain published Shadbala example"
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

