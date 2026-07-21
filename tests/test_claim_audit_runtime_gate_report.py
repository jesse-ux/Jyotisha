import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_claim_gate_report_covers_all_index_domains_for_high_claim() -> None:
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/claim_audit_runtime_gate_report.py", "--claim", "production_ready"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "claim_audit_runtime_gate_report"
    assert data["requested_claim"] == "production_ready"
    assert data["summary"]["domain_count"] >= 20
    assert data["summary"]["blocked_count"] >= 1
    assert data["summary"]["degraded_count"] >= 1
    assert data["summary"]["production_tuning_allowed_count"] == 0


def test_claim_gate_report_keeps_known_blockers_and_partials_visible() -> None:
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/claim_audit_runtime_gate_report.py", "--claim", "production_ready"],
            cwd=ROOT,
            text=True,
        )
    )
    domains = {row["domain"]: row for row in data["domains"]}
    assert domains["timing_holdout"]["decision"] == "block"
    assert "day_level_holdout_readiness_ledger" in domains["timing_holdout"]["blocking_packets"]
    assert domains["shadbala_component_closure"]["decision"] == "degrade"
    assert domains["worked_example_collection"]["decision"] == "block"
