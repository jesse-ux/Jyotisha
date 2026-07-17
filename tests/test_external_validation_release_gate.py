"""Regression coverage for the public external-validation release boundary."""

from __future__ import annotations

import json
from pathlib import Path

import scripts.external_validation_release_gate as gate


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "references" / "evidence_manifests" / "commercial_external_validation_release.v1.json"


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _copy_manifest_with_one_bad_digest(tmp_path: Path) -> Path:
    manifest = _manifest()
    manifest["assets"][0]["sha256"] = "0" * 64
    path = tmp_path / "release.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_release_manifest_declares_public_assets_and_external_boundaries() -> None:
    manifest = _manifest()
    assert manifest["schema_version"] == 1
    assert manifest["release_scope"] == "public_research_evidence_snapshot"
    assert manifest["engines"]["PyJHora"]["status"] == "available"
    assert manifest["engines"]["jyotishganit"]["status"] == "available"
    assert manifest["engines"]["VedAstro"]["status"] == "blocked"
    assert manifest["engines"]["JHora"]["official_raw_status"] != "verified"


def test_evaluate_manifest_accepts_current_public_release() -> None:
    report = gate.evaluate_manifest(MANIFEST)
    assert report["status"] == "pass"
    assert report["summary"]["assets_verified"] == report["summary"]["assets_total"]
    assert report["summary"]["production_tuning_allowed"] is False
    assert report["engines"]["VedAstro"]["status"] == "blocked"


def test_evaluate_manifest_reports_digest_drift(tmp_path: Path) -> None:
    report = gate.evaluate_manifest(_copy_manifest_with_one_bad_digest(tmp_path))
    assert report["status"] == "blocked"
    assert report["assets"][0]["integrity"] == "mismatch"


def test_runtime_truth_profile_runs_external_validation_release_gate() -> None:
    text = (ROOT / "scripts" / "run_quality_gate.py").read_text(encoding="utf-8")
    assert "external_validation_release_gate.py" in text
