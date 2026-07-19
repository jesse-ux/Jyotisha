import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/external_source_use_tier_registry_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_external_source_use_tier_registry_blocks_truth_upgrade():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/external_source_use_tier_registry.py", "--date", "2026-07-20"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "external_source_use_tier_registry"
    assert data["claim_status"] == "ready_contract"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert data["summary"]["oracle_truth_ready_count"] == 0


def test_external_source_use_tier_registry_has_required_tiers():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    tiers = {row["allowed_use_tier"] for row in data["sources"]}
    assert "permissive_adapter_or_formula_observation" in tiers
    assert "manual_oracle_candidate_queue" in tiers
    assert "case_reference_for_user_explanation" in tiers
    assert all(row["can_be_oracle_truth"] is False for row in data["sources"])


def test_evidence_index_registers_external_source_use_tier_registry():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    packet = packets["external_source_use_tier_registry_2026_07_20"]
    assert packet["claim_status"] == "ready_contract"
    assert packet["consumer_policy"] == "research_to_commercial_contract_only"
