from pathlib import Path

from scripts.jyotishyamitra_adapter_probe import (
    build_report,
    build_varga_comparison,
    canonical_request,
    compare_with_existing_oracles,
    extract_local_varga_signs,
    extract_varga_signs,
    extract_xalen_varga_signs,
    normalize_raw,
    schema_fingerprint,
)


WHEEL = Path("/tmp/jyotishyamitra_probe/jyotishyamitra-1.4.0-py3-none-any.whl")
WHEEL_SHA256 = "4f1a16facfa86ef01cb44de505c6de2e66b2f8d2c8b5e125c090e3f8485c6a9d"


def test_jyotishyamitra_probe_contract_uses_pinned_identity_fixture(tmp_path: Path) -> None:
    wheel = WHEEL
    assert wheel.exists(), "fixture_missing: run pinned wheel download outside CI; tests must not fetch network"
    report = build_report(
        wheel_path=wheel,
        commit="86f7eb610a66b06b3f0817d2c53355bec8b3bf8d",
        raw={"D1": {"Sun": "Aquarius"}, "metadata": {"ayanamsa": "Lahiri"}},
    )

    assert report["oracle"] == "jyotishyamitra"
    assert report["license"] == "MIT"
    assert report["version"] == "1.4.0"
    assert report["source_commit"] == "86f7eb610a66b06b3f0817d2c53355bec8b3bf8d"
    assert report["wheel_sha256"]
    assert report["wheel_sha256"] == WHEEL_SHA256
    assert report["raw_sha256"]
    assert report["normalized_raw_sha256"]
    assert report["package_metadata"]["version"] == "1.4.0"
    assert report["package_metadata"]["requires_python"] == ">=3.7"
    assert report["package_metadata"]["license"] is None
    assert report["package_metadata"]["license_file_spdx_inferred"] == "MIT"
    assert report["python_runtime"]["version"]
    assert report["schema_fingerprint"]["sha256"]
    assert report["isolated_subprocess"]["used"] is False
    assert report["truth_policy"] == "independent_observation_not_truth"


def test_jyotishyamitra_missing_wheel_is_explicitly_blocked(tmp_path: Path) -> None:
    report = build_report(tmp_path / "missing.whl")

    assert report["status"] == "blocked"
    assert report["blocked_reason"] == "fixture_missing"
    assert report["promotion_allowed"] is False


def test_jyotishyamitra_canonical_request_records_defaults() -> None:
    request = canonical_request(
        {
            "name": "Steve Jobs",
            "gender": "male",
            "place": "San Francisco",
            "longitude": -122.4194,
            "latitude": 37.7749,
            "timezone": -8.0,
            "birth": {"year": 1955, "month": 2, "day": 24, "hour": 19, "minute": 15},
        }
    )

    assert request["ayanamsa"] == "package_default"
    assert request["node_mode"] == "package_default"
    assert request["returnval"] == "ASTRODATA_DICTIONARY"
    assert request["birth"]["second"] == 0


def test_jyotishyamitra_schema_fingerprint_is_stable() -> None:
    fp = schema_fingerprint({"D1": {"Sun": "Aquarius"}, "scores": [1, 2]})

    assert fp["path_count"] == 3
    assert fp["sha256"]
    assert "$.D1.Sun:str" in fp["sample_paths"]


def test_jyotishyamitra_normalizes_volatile_current_dasha_timestamp() -> None:
    a = {"Dashas": {"Vimshottari": {"current": {"date": "run-a", "lord": "Sun"}}}}
    b = {"Dashas": {"Vimshottari": {"current": {"date": "run-b", "lord": "Sun"}}}}

    assert normalize_raw(a) == normalize_raw(b)


def test_jyotishyamitra_field_comparison_is_observation_not_promotion() -> None:
    comparison = compare_with_existing_oracles(
        {"D1": {"Sun": "Aquarius"}, "D9": {"Moon": "Cancer"}},
        {"D1": {"Sun": "Aquarius"}, "D9": {"Moon": "Leo"}},
        {"D1": {"Sun": "Aquarius"}, "D9": {"Moon": "Cancer"}},
    )

    assert comparison["row_count"] == 2
    assert comparison["match_counts"]["local"] == 1
    assert comparison["match_counts"]["xalen"] == 2
    assert comparison["promotion_allowed"] is False


def test_extract_varga_signs_keeps_only_supported_planet_signs() -> None:
    raw = {
        "D1": {"planets": {"Sun": {"sign": "Aquarius"}, "Rahu": {"sign": "Saggitarius"}}},
        "D9": {"planets": {"Moon": {"sign": "Cancer"}, "Mars": {"sign": None}}},
        "Balas": {"Shadbala": {}},
    }

    assert extract_varga_signs(raw) == {
        "D1": {"Sun": "Aquarius", "Rahu": "Sagittarius"},
        "D9": {"Moon": "Cancer"},
    }


def test_existing_oracle_sign_adapters_share_the_same_surface() -> None:
    local = {
        "planets": {"Sun": {"sign": "Aquarius"}},
        "varga": {"D9": {"Moon": {"sign": "Cancer"}}},
    }
    xalen = {"varga": {"D1": {"Sun": "Kumbha"}, "D9": {"Moon": "Karka"}}}

    assert extract_local_varga_signs(local) == {
        "D1": {"Sun": "Aquarius"},
        "D9": {"Moon": "Cancer"},
    }
    assert extract_xalen_varga_signs(xalen) == {
        "D1": {"Sun": "Aquarius"},
        "D9": {"Moon": "Cancer"},
    }


def test_varga_comparison_never_promotes_the_new_oracle() -> None:
    jyotishyamitra = {"D1": {"planets": {"Sun": {"sign": "Aquarius"}}}}
    local = {"planets": {"Sun": {"sign": "Aquarius"}}}
    xalen = {"varga": {"D1": {"Sun": "Kumbha"}}}

    comparison = build_varga_comparison(jyotishyamitra, local, xalen)

    assert comparison["row_count"] == 1
    assert comparison["match_counts"] == {"local": 1, "xalen": 1}
    assert comparison["promotion_allowed"] is False


def test_varga_comparison_marks_missing_engine_fields_not_comparable() -> None:
    comparison = compare_with_existing_oracles(
        {"D1": {"Rahu": "Leo"}},
        {"D1": {"Rahu": "Leo"}},
        {"D1": {}},
    )

    assert comparison["rows"][0]["local_status"] == "match"
    assert comparison["rows"][0]["xalen_status"] == "not_comparable"
