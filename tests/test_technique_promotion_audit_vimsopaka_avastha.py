from __future__ import annotations

import json
from pathlib import Path

from scripts.technique_promotion_audit_vimsopaka_avastha import build_audit

ROOT = Path(__file__).resolve().parents[1]


def test_vimsopaka_avastha_audit_corrects_call_status() -> None:
    audit = build_audit(ROOT)
    assert audit["scope"] == "technique_promotion_audit_vimsopaka_avastha"
    assert audit["truth_policy"] == "runtime_presence_not_oracle_closure"
    assert audit["production_tuning_allowed"] is False
    statuses = {item["technique_id"]: item["current_call_status"] for item in audit["items"]}
    assert statuses["vimsopaka_bala"] == "formally_called_in_full_reading"
    assert statuses["avastha_states"] == "formally_called_via_deep_varga_avastha_endpoint"


def test_vimsopaka_avastha_audit_records_entrypoints_and_boundaries() -> None:
    audit = build_audit(ROOT)
    for item in audit["items"]:
        assert item["main_artifacts"]
        assert item["entrypoints"]
        assert item["next_action"] in {
            "add_formula_source_and_oracle_packet",
            "add_display_contract_and_source_oracle_packet",
        }
        assert item["claim_boundary"]
        assert item["reuse_decision"] == "do_not_duplicate_runtime"


def test_vimsopaka_avastha_audit_artifact_exists() -> None:
    artifact = ROOT / "references/oracle/technique_promotion_audit_vimsopaka_avastha_2026_07_19.json"
    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["summary"] == {
        "items_checked": 2,
        "formally_called_count": 2,
        "duplicate_runtime_needed": 0,
    }

