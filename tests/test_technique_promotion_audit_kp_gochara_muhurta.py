from __future__ import annotations

import json
from pathlib import Path

from scripts.technique_promotion_audit_kp_gochara_muhurta import build_audit

ROOT = Path(__file__).resolve().parents[1]


def test_kp_gochara_muhurta_audit_splits_runtime_presence() -> None:
    audit = build_audit(ROOT)
    statuses = {item["technique_id"]: item["current_call_status"] for item in audit["items"]}
    assert audit["scope"] == "technique_promotion_audit_kp_gochara_muhurta"
    assert audit["truth_policy"] == "runtime_presence_not_oracle_closure"
    assert statuses["panchanga_calendar"] == "partial"
    assert statuses["muhurta_dashaflow_candidate"] == "oss_reference_not_main_runtime"
    assert statuses["kp_astrology"] == "reference_only_not_main_runtime"
    assert statuses["gochara_event_timing_template"] == "template_reference_not_main_runtime"


def test_kp_gochara_muhurta_audit_records_reuse_boundaries() -> None:
    audit = build_audit(ROOT)
    for item in audit["items"]:
        assert item["reuse_decision"] in {"do_not_duplicate_runtime", "license_audit_before_reuse", "reference_only"}
        assert item["next_action"]
        assert item["claim_boundary"]
        assert item["source_or_license_boundary"]


def test_kp_gochara_muhurta_audit_artifact_exists() -> None:
    artifact = ROOT / "references/oracle/technique_promotion_audit_kp_gochara_muhurta_2026_07_19.json"
    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["summary"] == {
        "items_checked": 4,
        "formally_called_count": 0,
        "reference_only_count": 3,
    }
