from __future__ import annotations

import json
from pathlib import Path

from scripts.real_case_replay_validator import validate_manifest
from scripts.unified_consultation_orchestrator import UnifiedConsultationOrchestrator

ROOT = Path(__file__).resolve().parents[1]


def test_real_case_replay_manifest_contains_ten_research_grade_cases() -> None:
    result = validate_manifest(ROOT / "references/real_case_calibration/replay_manifest.json")

    assert result["status"] == "pass"
    assert result["case_count"] == 10
    assert result["replay_ready_count"] == 10
    assert result["domain_counts"] == {"career": 5, "marriage": 5}
    assert result["birth_time_ratings"] == {"A": 2, "AA": 8}


def test_holdout_manifest_contains_ten_new_balanced_cases() -> None:
    batch1_path = ROOT / "references/real_case_calibration/replay_manifest.json"
    holdout_path = ROOT / "references/real_case_calibration/replay_manifest_holdout_v2.json"
    result = validate_manifest(holdout_path)
    assert result["status"] == "pass"
    assert result["case_count"] == 10
    assert result["domain_counts"] == {"career": 5, "marriage": 5}
    assert result["birth_time_ratings"] == {"A": 5, "AA": 5}
    batch1 = json.loads(batch1_path.read_text(encoding="utf-8"))
    holdout = json.loads(holdout_path.read_text(encoding="utf-8"))
    assert {case["subject"]["name"] for case in batch1["cases"]}.isdisjoint(
        {case["subject"]["name"] for case in holdout["cases"]}
    )


def test_three_case_probe_is_aa_and_disjoint_from_prior_twenty() -> None:
    probe_path = ROOT / "references/real_case_calibration/replay_manifest_probe3_v2.json"
    result = validate_manifest(probe_path)

    assert result["status"] == "pass"
    assert result["case_count"] == 3
    assert result["replay_ready_count"] == 3
    assert result["domain_counts"] == {"career": 2, "marriage": 1}
    assert result["birth_time_ratings"] == {"AA": 3}

    prior_names = set()
    for path in (
        ROOT / "references/real_case_calibration/replay_manifest.json",
        ROOT / "references/real_case_calibration/replay_manifest_holdout_v2.json",
    ):
        payload = json.loads(path.read_text(encoding="utf-8"))
        prior_names.update(case["subject"]["name"] for case in payload["cases"])
    probe = json.loads(probe_path.read_text(encoding="utf-8"))
    assert prior_names.isdisjoint(case["subject"]["name"] for case in probe["cases"])


def test_real_case_replay_validator_accepts_one_structured_case(tmp_path: Path) -> None:
    manifest = {
        "schema_version": "1.0",
        "status": "ready",
        "case_schema": "references/real_case_calibration/catalog.schema.json",
        "cases": [
            {
                "case_id": "public_case_001",
                "subject": {
                    "name": "Public Case",
                    "year": 1970,
                    "month": 1,
                    "day": 1,
                    "hour": 12,
                    "minute": 0,
                    "lat": 0.0,
                    "lon": 0.0,
                    "tz": 0.0,
                    "node_mode": "mean",
                    "birth_source": {
                        "url": "https://example.com/birth-record",
                        "source_grade": "primary",
                        "time_accuracy_rating": "AA",
                        "evidence_basis": "birth_record_in_hand",
                    },
                },
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
                        "domain": "career",
                        "expected_label": "career_status",
                        "outcome": "public_success",
                        "source": {
                            "url": "https://example.com/event",
                            "source_grade": "verified_secondary",
                        },
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


def test_real_case_replay_validator_rejects_low_accuracy_birth_time_and_unsourced_event(tmp_path: Path) -> None:
    manifest = {
        "schema_version": "2.0",
        "status": "ready",
        "case_schema": "references/real_case_calibration/catalog.schema.json",
        "cases": [
            {
                "case_id": "weak_case",
                "subject": {
                    "name": "Weak Case",
                    "year": 1970,
                    "month": 1,
                    "day": 1,
                    "hour": 12,
                    "minute": 0,
                    "lat": 0.0,
                    "lon": 0.0,
                    "tz": 0.0,
                    "node_mode": "mean",
                    "birth_source": {
                        "url": "https://example.com/birth",
                        "source_grade": "unverified",
                        "time_accuracy_rating": "DD",
                        "evidence_basis": "conflicting_times",
                    },
                },
                "source": {
                    "url": "https://example.com/case",
                    "source_grade": "unverified",
                    "license_or_quote_boundary": "summary_only",
                },
                "chart_signature": {},
                "event_outcomes": [
                    {
                        "event_type": "legal_marriage",
                        "event_date": "2000-01-01",
                        "domain": "marriage",
                        "expected_label": "legal_marriage",
                        "outcome": "married",
                    }
                ],
                "similarity": {"score": 0.0, "matching_factors": [], "dissimilar_factors": []},
                "replay": {"outcome_replay_status": "replayed", "do_not_use_for_prediction": False},
            }
        ],
    }
    path = tmp_path / "replay_manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    result = validate_manifest(path)
    assert result["status"] == "invalid"
    assert {error["error"] for error in result["errors"]} >= {
        "birth_time_rating_below_A",
        "missing",
    }


def test_orchestrator_exposes_real_case_replay_manifest_status() -> None:
    orchestrator = UnifiedConsultationOrchestrator()
    route = {"question_type": "career", "primary_theme": "career"}

    packet = orchestrator.real_case_calibration_catalog(route_packet=route, machine_evidence_packet={})

    replay = packet["outcome_replay_manifest"]
    assert replay["status"] == "pass"
    assert replay["case_count"] == 10
    holdout = packet["holdout_replay_manifest"]
    assert holdout["status"] == "pass"
    assert holdout["case_count"] == 10
    benchmark = packet["public_outcome_benchmark"]
    assert benchmark["status"] == "used"
    assert benchmark["summary"]["total_events"] == 20
    assert benchmark["summary"]["positive_event_recall"] == 0.8
    assert benchmark["summary"]["exact_label_rate"] == 0.4
    assert benchmark["summary"]["balanced_accuracy"] is None
    assert benchmark["holdout_promotion"] == {"promote": True, "reason": "holdout_metrics_improved"}
    supplemental = packet["supplemental_public_probe"]
    assert supplemental["status"] == "used"
    assert supplemental["summary"]["total_events"] == 3
    assert supplemental["summary"]["positive_event_recall"] == 1 / 3
    assert supplemental["combined_observation"]["total_events"] == 23
    assert supplemental["combined_observation"]["positive_event_recall"] == 17 / 23
    corrected = packet["corrected_v21_observation"]
    assert corrected["status"] == "used"
    assert corrected["summary"]["total_events"] == 23
    assert corrected["summary"]["positive_event_recall_deprecated"] is True
    assert corrected["ashtakavarga_audit_status"] == "used_non_scoring"
    negative = packet["negative_control_pilot"]
    assert negative["status"] == "used"
    assert negative["summary"]["control_date_count"] == 24
    assert negative["summary"]["positive_top_1_rate"] == 0.0
    assert negative["summary"]["positive_top_3_rate"] == 0.0
    annual = packet["annual_control_pilot"]
    assert annual["status"] == "used"
    assert annual["summary"]["control_date_count"] == 12
    assert annual["summary"]["positive_top_1_rate"] == 1 / 3
    timing_gate = packet["timing_precision_gate"]
    assert timing_gate["status"] == "blocked"
    assert timing_gate["maximum_supported_precision"] == "unvalidated_broad_window"
    assert timing_gate["blocked_claims"] == ["exact_day", "exact_month_from_current_replay_score"]
    assert timing_gate["domain_support"] == {"career": "blocked", "marriage": "partial_candidate"}
    runtime_log = orchestrator.runtime_evidence_log(
        surface="api_web",
        entry_mode="direct_chart",
        route_packet=route,
        executed_steps=["compute_chart"],
        skipped_steps=[],
        real_case_calibration=packet,
    )
    assert "timing_precision_gate_blocked" in runtime_log["quality_gate"]["blocked_items"]
    timing_row = next(
        row for row in runtime_log["quality_gate"]["technique_audit_table"]
        if row["technique"] == "Timing Precision Gate"
    )
    assert timing_row["status"] == "blocked"
    assert timing_row["maximum_supported_precision"] == "unvalidated_broad_window"
    assert packet["required_replay_schema"] == "references/real_case_calibration/catalog.schema.json"
