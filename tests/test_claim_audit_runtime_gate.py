from __future__ import annotations

from pathlib import Path

from scripts.claim_audit_runtime_gate import evaluate_claim

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_claim_gate_blocks_verified_claims_for_blocked_domain() -> None:
    result = evaluate_claim(INDEX, "timing_holdout", "verified_precise_prediction")
    assert result["decision"] == "block"
    assert result["allowed_claim_status"] == "exploratory_unvalidated"
    assert result["production_tuning_allowed"] is False
    assert set(result["blocking_packets"]) == {
        "day_level_human_annotation_packet",
        "day_level_holdout_readiness_ledger",
    }


def test_claim_gate_degrades_partial_domains() -> None:
    result = evaluate_claim(INDEX, "shadbala_ashtakavarga", "complete_absolute_truth")
    assert result["decision"] == "degrade"
    assert result["allowed_claim_status"] == "partial_method_variant"
    assert result["blocking_packets"] == ["xalen_shadbala_av_delta_report"]
    assert "formulas/units/school variants remain open" in result["boundaries"][0]


def test_claim_gate_allows_ready_contract_but_not_prediction_truth() -> None:
    result = evaluate_claim(INDEX, "profile_schema", "ready_contract")
    assert result["decision"] == "allow"
    assert result["allowed_claim_status"] == "ready_contract"
    assert result["blocking_packets"] == []


def test_claim_gate_blocks_unknown_domain() -> None:
    result = evaluate_claim(INDEX, "unknown_domain", "complete")
    assert result["decision"] == "block"
    assert result["allowed_claim_status"] == "blocked_unknown_domain"
