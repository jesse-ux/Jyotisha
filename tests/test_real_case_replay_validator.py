from __future__ import annotations

import json
from pathlib import Path

from scripts.real_case_replay_validator import validate_manifest
from scripts.unified_consultation_orchestrator import UnifiedConsultationOrchestrator

ROOT = Path(__file__).resolve().parents[1]


def test_real_case_replay_manifest_blocks_when_no_cases_are_imported() -> None:
    result = validate_manifest(ROOT / "references/real_case_calibration/replay_manifest.json")

    assert result["status"] == "blocked"
    assert result["case_count"] == 0
    assert result["replay_ready_count"] == 0
    assert result["blocked_reason"] == "no_structured_outcome_replay_cases_imported"


def test_real_case_replay_validator_accepts_one_structured_case(tmp_path: Path) -> None:
    manifest = {
        "schema_version": "1.0",
        "status": "ready",
        "case_schema": "references/real_case_calibration/catalog.schema.json",
        "cases": [
            {
                "case_id": "public_case_001",
                "source": {
                    "url": "https://example.com/public-case",
                    "source_grade": "verified_secondary",
                    "license_or_quote_boundary": "summary_only",
                },
                "chart_signature": {"lagna": "Leo", "notable_yogas": ["career_yoga"]},
                "event_outcomes": [
                    {
                        "event_type": "career_breakthrough",
                        "event_date": "2000-01",
                        "outcome": "public_success",
                    }
                ],
                "similarity": {
                    "score": 0.72,
                    "matching_factors": ["D10", "dasha"],
                    "dissimilar_factors": [],
                },
                "replay": {
                    "outcome_replay_status": "replayed",
                    "do_not_use_for_prediction": False,
                },
            }
        ],
    }
    path = tmp_path / "replay_manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_manifest(path)

    assert result["status"] == "pass"
    assert result["case_count"] == 1
    assert result["replay_ready_count"] == 1


def test_orchestrator_exposes_real_case_replay_manifest_status() -> None:
    orchestrator = UnifiedConsultationOrchestrator()
    route = {"question_type": "career", "primary_theme": "career"}

    packet = orchestrator.real_case_calibration_catalog(route_packet=route, machine_evidence_packet={})

    replay = packet["outcome_replay_manifest"]
    assert replay["status"] == "blocked"
    assert replay["case_count"] == 0
    assert packet["required_replay_schema"] == "references/real_case_calibration/catalog.schema.json"
