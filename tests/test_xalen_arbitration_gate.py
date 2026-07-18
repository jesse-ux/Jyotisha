import json

from scripts.xalen_arbitration_gate import build_report


def test_xalen_arbitration_gate_blocks_unresolved_method_variants(tmp_path) -> None:
    attribution = tmp_path / "attr.json"
    public_batch = tmp_path / "batch.json"
    ephemeris = tmp_path / "ephem.json"
    attribution.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "field": "Sun.chesta",
                        "truth_status": "method_variant_unresolved",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    public_batch.write_text(json.dumps({"case_count": 5}), encoding="utf-8")
    ephemeris.write_text(
        json.dumps({"maximum_absolute_longitude_delta_deg": 0.001, "varga_difference_count": 0}),
        encoding="utf-8",
    )

    report = build_report(attribution, public_batch, ephemeris)

    assert report["multi_case_replay_status"] == "ready"
    assert report["independent_ephemeris_status"] == "ready"
    assert report["truth_status"] == "blocked"
    assert report["promotion_allowed"] is False


def test_xalen_arbitration_gate_allows_only_when_variants_are_arbitrated(tmp_path) -> None:
    attribution = tmp_path / "attr.json"
    public_batch = tmp_path / "batch.json"
    ephemeris = tmp_path / "ephem.json"
    attribution.write_text(json.dumps({"rows": [{"truth_status": "external_worked_example_match"}]}), encoding="utf-8")
    public_batch.write_text(json.dumps({"case_count": 5}), encoding="utf-8")
    ephemeris.write_text(
        json.dumps({"maximum_absolute_longitude_delta_deg": 0.001, "varga_difference_count": 0}),
        encoding="utf-8",
    )

    report = build_report(attribution, public_batch, ephemeris)

    assert report["truth_status"] == "ready"
    assert report["promotion_allowed"] is True
