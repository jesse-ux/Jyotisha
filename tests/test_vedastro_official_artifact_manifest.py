import json
from pathlib import Path


def test_official_full_snapshot_artifact_manifest_lists_raw_response(tmp_path, monkeypatch):
    from scripts import vedastro_service_adapter as adapter

    monkeypatch.setattr(adapter, "ARTIFACT_DIR", tmp_path)
    artifact = tmp_path / "official_full_snapshot-abc-def.json"
    artifact.write_text(
        json.dumps(
            {
                "status": "ok",
                "operation": "official_full_snapshot",
                "raw_response": {"source": "vedastro_official_full_snapshot", "sections": {"ok": True}},
                "request_manifest": {"case_id": "synthetic"},
                "snapshot_sections": {"chart_core": {"Status": "Pass"}},
            }
        ),
        encoding="utf-8",
    )

    manifest = adapter.list_official_full_snapshot_artifacts()
    assert manifest["artifact_count"] == 1
    assert manifest["artifacts"][0]["official_raw_response_available"] is True
    assert manifest["artifacts"][0]["path"] == str(artifact)
