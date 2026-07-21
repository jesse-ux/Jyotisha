import json

from scripts.three_engine_parity_replay_validator import validate_manifest


def test_verified_oracle_requires_raw_artifact_hash_and_settings(tmp_path):
    manifest = {
        "engines": {
            "VedAstro": {"status": "official_verified"},
            "PyJHora_JHora": {"status": "blocked"},
            "jyotishganit": {"status": "blocked"},
        },
        "comparison_rows": [],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_manifest(path)

    assert result["status"] == "invalid"
    assert any(error["error"] == "required_for_verified_status" for error in result["errors"])


def test_high_rigor_parity_requires_non_d1_and_shadbala_component_rows(tmp_path):
    manifest = {
        "engines": {
            "VedAstro": {"status": "blocked"},
            "PyJHora_JHora": {"status": "blocked"},
            "jyotishganit": {"status": "blocked"},
        },
        "comparison_rows": [
            {
                "section": "D1",
                "field": "Sun.sign",
                "local_value": "Aquarius",
                "oracle_values": {},
                "status": "match",
            }
        ],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_manifest(path)

    assert result["status"] == "partial"
    assert result["blocked_reason"] == "missing_high_rigor_sections"
    assert "D2" in result["missing_high_rigor_sections"]
    assert "shadbala_components" in result["missing_high_rigor_sections"]


def test_high_rigor_parity_passes_only_when_required_sections_are_present(tmp_path):
    rows = [
        {
            "section": section,
            "field": "sample",
            "local_value": 1,
            "oracle_values": {"PyJHora_JHora": 1},
            "status": "match",
        }
        for section in [
            "D1",
            "D2",
            "D4",
            "D9",
            "D10",
            "ashtakavarga_bav",
            "ashtakavarga_sav",
            "shadbala_total",
            "shadbala_components",
        ]
    ]
    manifest = {
        "engines": {
            "VedAstro": {"status": "blocked"},
            "PyJHora_JHora": {"status": "blocked"},
            "jyotishganit": {"status": "blocked"},
        },
        "comparison_rows": rows,
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_manifest(path)

    assert result["status"] == "pass"
    assert result["missing_high_rigor_sections"] == []
