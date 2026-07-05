#!/usr/bin/env python3
"""Acceptance guard for the final JHora/PDF evidence packet artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path

import scripts.sync_final_evidence_packet_status as sync_status


ROOT = Path(__file__).resolve().parents[1]
WORK_DIR = ROOT / "scratch" / "local" / "pdf_review_123456"
ERROR_LOG = ROOT / "docs" / "research" / "final_output_acceptance_error_log_2026_07_04.md"


def _latest_packet() -> tuple[int, Path, dict]:
    sync_status.main()
    packets: list[tuple[int, Path]] = []
    for path in WORK_DIR.glob("jhora_master_evidence_packet_REDACTED_DATE_REDACTED_TIME.v*.json"):
        match = re.search(r"\.v(\d+)\.json$", path.name)
        if match:
            packets.append((int(match.group(1)), path))
    assert packets, "no versioned JHora master evidence packets found"
    version, path = max(packets)
    return version, path, json.loads(path.read_text(encoding="utf-8"))


def test_latest_master_packet_has_consistent_final_status_and_version_metadata() -> None:
    version, path, packet = _latest_packet()
    metadata = packet["metadata"]

    assert version >= 24
    assert packet["status"] == "final_output_v1"
    assert metadata["status"] == "final_output_v1"
    assert metadata["current_version"] == f"v{version}"
    assert metadata["packet_version"] == f"v{version}"
    assert metadata["canonical_packet"] == path.name
    assert packet["structured_v13_final_integrated_report"]["status"] == "final_output_v1"


def test_latest_master_packet_links_all_final_report_artifacts() -> None:
    _, _, packet = _latest_packet()

    required_sections = {
        "structured_v21_raman_full_report_complete": ("source", "compiled-full-report-v1"),
        "structured_v22_raman_full_report_pdf_artifact": ("pdf", "pdf-rendered-qa-pass"),
        "structured_v23_raman_full_report_raw_data_appendix": ("source", "raw-data-appendix-v1"),
    }
    for section, (artifact_key, status) in required_sections.items():
        payload = packet[section]
        assert payload["status"] == status
        artifact = ROOT / payload[artifact_key]
        assert artifact.exists(), f"missing artifact for {section}: {artifact}"
        assert artifact.stat().st_size > 1000, f"artifact too small for {section}: {artifact}"

    pdf_payload = packet["structured_v22_raman_full_report_pdf_artifact"]
    for rel_path in pdf_payload["qa_rendered_pages"]:
        qa_page = WORK_DIR / rel_path
        assert qa_page.exists(), f"missing PDF QA render page: {qa_page}"
        assert qa_page.stat().st_size > 1000


def test_status_ledger_points_to_latest_packet_and_has_fresh_next_step() -> None:
    version, path, _ = _latest_packet()
    ledger = (WORK_DIR / "evidence_packet_status_ledger_REDACTED_DATE_REDACTED_TIME.md").read_text(
        encoding="utf-8"
    )

    assert path.name in ledger
    assert f"`{path.name}` | active" in ledger
    assert "Raman full report complete" in ledger
    assert "Raman full report PDF" in ledger
    assert "Raman full report raw data appendix" in ledger
    assert "Chapter 04 Parashari Dasha layer - Vimshottari" not in ledger
    assert "Acceptance/error-log gate" in ledger
    assert f"v{version}" in ledger


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


def test_sync_script_repairs_latest_packet_metadata_and_ledger(tmp_path, monkeypatch) -> None:
    for version in (2, 10):
        packet = {
            "status": "final_output_v1",
            "metadata": {
                "status": "final_output_v1",
                "current_version": "v1",
                "packet_version": f"v{version}",
                "canonical_packet": "jhora_master_evidence_packet_REDACTED_DATE_REDACTED_TIME.v1.json",
            },
            "structured_v13_final_integrated_report": {"status": "final_output_v1"},
        }
        (tmp_path / f"jhora_master_evidence_packet_REDACTED_DATE_REDACTED_TIME.v{version}.json").write_text(
            json.dumps(packet, ensure_ascii=False),
            encoding="utf-8",
        )
    ledger = tmp_path / "evidence_packet_status_ledger_REDACTED_DATE_REDACTED_TIME.md"
    ledger.write_text(
        "| Master evidence packet | `jhora_master_evidence_packet_REDACTED_DATE_REDACTED_TIME.v2.json` | active | Current canonical structured packet. |\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(sync_status, "WORK_DIR", tmp_path)

    assert sync_status.main() == 0
    latest = json.loads(
        (tmp_path / "jhora_master_evidence_packet_REDACTED_DATE_REDACTED_TIME.v10.json").read_text(
            encoding="utf-8"
        )
    )
    assert latest["metadata"]["current_version"] == "v10"
    assert latest["metadata"]["packet_version"] == "v10"
    assert (
        latest["metadata"]["canonical_packet"]
        == "jhora_master_evidence_packet_REDACTED_DATE_REDACTED_TIME.v10.json"
    )
    assert "jhora_master_evidence_packet_REDACTED_DATE_REDACTED_TIME.v10.json" in ledger.read_text(
        encoding="utf-8"
    )
