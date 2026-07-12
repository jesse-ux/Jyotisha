from pathlib import Path

import pytest

from scripts.external_oracle_raw_import import build_raw_oracle_import


def _metadata(**overrides):
    value = {
        "case_id": "public_case",
        "license_boundary": "external benchmark only",
        "collection_method": "manual export",
        "birth_data_policy": "public_case_only",
    }
    value.update(overrides)
    return value


def test_raw_import_requires_reviewable_public_case_artifact(tmp_path: Path):
    artifact = tmp_path / "oracle.json"
    artifact.write_text('{"raw": true}', encoding="utf-8")

    result = build_raw_oracle_import("VedAstro", artifact, _metadata())

    assert result["status"] == "raw_imported_uncompared"
    assert result["source_artifact_sha256"]
    assert result["comparison_ready"] is False


def test_raw_import_rejects_non_public_birth_policy(tmp_path: Path):
    artifact = tmp_path / "oracle.json"
    artifact.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="public_case_only"):
        build_raw_oracle_import("VedAstro", artifact, _metadata(birth_data_policy="private"))
