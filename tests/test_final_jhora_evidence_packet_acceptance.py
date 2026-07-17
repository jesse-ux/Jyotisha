#!/usr/bin/env python3
"""Acceptance guard for the versioned public JHora evidence manifest."""

from __future__ import annotations

import json
from pathlib import Path

import scripts.sync_final_evidence_packet_status as sync_status


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "references" / "evidence_manifests" / "jhora_master_evidence_manifest.json"
ERROR_LOG = ROOT / "docs" / "research" / "final_output_acceptance_error_log_2026_07_04.md"


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_versioned_manifest_declares_public_release_boundary() -> None:
    manifest = _manifest()

    assert manifest["schema_version"] == 1
    assert manifest["artifact_id"] == "jhora_master_evidence"
    assert manifest["source_scope"] == "public_release"
    assert manifest["release_gate"]["local_scratch_required"] is False
    assert manifest["release_gate"]["external_raw_required_for_official_verified"] is True


def test_manifest_keeps_external_jhora_raw_state_honest() -> None:
    evidence = _manifest()["evidence"]

    assert evidence["engine"] == "JHora"
    assert evidence["raw_status"] in {"not_collected", "partial", "verified"}
    assert evidence["raw_status"] != "verified"
def test_acceptance_error_log_records_known_failures_and_prevention_rules() -> None:
    text = ERROR_LOG.read_text(encoding="utf-8")

    required_phrases = [
        "status metadata drift",
        "canonical packet drift",
        "stale next-step ledger",
        "blank PDF artifact",
        "read this log before editing",
        "test_final_jhora_evidence_packet_acceptance.py",
    ]
    for phrase in required_phrases:
        assert phrase in text


def test_sync_script_repairs_latest_packet_metadata_only_when_explicitly_requested(tmp_path, monkeypatch) -> None:
    for version in (2, 10):
        packet = {
            "status": "final_output_v1",
            "metadata": {
                "status": "final_output_v1",
                "current_version": "v1",
                "packet_version": f"v{version}",
                "canonical_packet": "jhora_master_evidence_packet_public_sample_19550224_1915.v1.json",
            },
            "structured_v13_final_integrated_report": {"status": "final_output_v1"},
        }
        (tmp_path / f"jhora_master_evidence_packet_public_sample_19550224_1915.v{version}.json").write_text(
            json.dumps(packet, ensure_ascii=False),
            encoding="utf-8",
        )
    ledger = tmp_path / "evidence_packet_status_ledger_public_sample_19550224_1915.md"
    ledger.write_text(
        "| Master evidence packet | `jhora_master_evidence_packet_public_sample_19550224_1915.v2.json` | active | Current canonical structured packet. |\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(sync_status, "LOCAL_EVIDENCE_DIR", tmp_path)

    assert sync_status.main(["--sync-local"]) == 0
    latest = json.loads(
        (tmp_path / "jhora_master_evidence_packet_public_sample_19550224_1915.v10.json").read_text(
            encoding="utf-8"
        )
    )
    assert latest["metadata"]["current_version"] == "v10"
    assert latest["metadata"]["packet_version"] == "v10"
    assert (
        latest["metadata"]["canonical_packet"]
        == "jhora_master_evidence_packet_public_sample_19550224_1915.v10.json"
    )
    assert "jhora_master_evidence_packet_public_sample_19550224_1915.v10.json" in ledger.read_text(
        encoding="utf-8"
    )


def test_sync_script_succeeds_without_local_scratch(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(sync_status, "LOCAL_EVIDENCE_DIR", tmp_path)

    assert sync_status.main([]) == 0
