import json
from pathlib import Path

from scripts.three_engine_mismatch_arbitrator import arbitrate_manifest


ROOT = Path(__file__).resolve().parents[1]


def test_arbitrator_classifies_every_mismatch_without_majority_truth() -> None:
    report = arbitrate_manifest(ROOT / "references/oracle/three_engine_parity_replay_manifest.json")

    assert report["mismatch_count"] == 60
    assert report["classified_count"] == 60
    assert report["unclassified_count"] == 0
    assert report["truth_policy"] == "no_majority_vote"
    assert sum(report["category_counts"].values()) == 60
    assert all(row["differing_engines"] for row in report["rows"])


def test_vedastro_only_d2_difference_is_endpoint_semantics(tmp_path: Path) -> None:
    manifest = {
        "engines": {name: {} for name in ("VedAstro", "PyJHora_JHora", "jyotishganit")},
        "comparison_rows": [{
            "section": "D2", "field": "Sun.sign", "local_value": "Leo",
            "oracle_values": {"VedAstro": "Gemini", "PyJHora_JHora": "Leo", "jyotishganit": "Leo"},
            "status": "mismatch",
        }],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    row = arbitrate_manifest(path)["rows"][0]
    assert row["category"] == "endpoint_or_varga_semantics"
    assert row["differing_engines"] == ["VedAstro"]
