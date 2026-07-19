from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import production_e2e_monitor, profile_persistence_regression, answer_quality_audit, skill_sync_admission_gate, long_term_validation_dashboard

def test_governance_contract_lists_five_controls() -> None:
    data=json.loads((ROOT/"references/cross_project_contract/production_governance_controls_2026_07_19.json").read_text())
    assert [c["id"] for c in data["controls"]] == ["production_e2e_monitor","profile_persistence_regression","answer_quality_audit","skill_sync_admission_gate","long_term_validation_dashboard"]

def test_production_e2e_monitor_uses_existing_pass_context() -> None:
    assert production_e2e_monitor.run()["status"] == "pass"

def test_profile_persistence_blocks_without_credentials(monkeypatch) -> None:
    monkeypatch.delenv("JYOTISHA_PRODUCTION_BASE_URL", raising=False)
    monkeypatch.delenv("JYOTISHA_PRODUCTION_COOKIE", raising=False)
    assert profile_persistence_regression.run()["status"] == "blocked"

def test_answer_quality_blocks_forbidden_claims() -> None:
    assert answer_quality_audit.audit_answer("保证发财")["status"] == "fail"
    assert answer_quality_audit.audit_answer("给出候选窗口，不保证具体日期")["status"] == "pass"

def test_sync_gate_and_dashboard_are_safe() -> None:
    assert skill_sync_admission_gate.run()["status"] == "pass"
    dash = long_term_validation_dashboard.run()
    assert dash["items"]["commercial_e2e"] == "pass"
    assert dash["items"]["day_month_holdout"] == "awaiting_independent_labels"
