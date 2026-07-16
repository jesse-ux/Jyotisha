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
