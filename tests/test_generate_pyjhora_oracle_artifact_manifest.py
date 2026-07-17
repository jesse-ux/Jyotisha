"""The PyJHora artifact inventory must be safe to read during verification."""

from __future__ import annotations

import scripts.generate_pyjhora_oracle_artifact_manifest as manifest


def test_build_manifest_does_not_write_tracked_output(monkeypatch) -> None:
    output = manifest.ROOT / "references" / "oracle" / "artifacts" / ".pytest-manifest.json"
    output.unlink(missing_ok=True)
    monkeypatch.setattr(manifest, "OUTPUT_PATH", output)

    try:
        report = manifest.build_manifest()
        assert not output.exists()
    finally:
        output.unlink(missing_ok=True)

    assert report["scope"] == "pyjhora_oracle_artifact_manifest"
