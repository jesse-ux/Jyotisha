from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKETS = {
    "kp": ROOT / "references/oracle/kp_exact_cusp_public_worked_example_hunt_v2_2026_07_22.json",
    "muhurta": ROOT / "references/oracle/muhurta_full_scoring_closure_queue_v2_2026_07_22.json",
    "prashna": ROOT / "references/oracle/prashna_tajika_saham_gulika_sphuta_numeric_packet_queue_v2_2026_07_22.json",
    "holdout": ROOT / "references/oracle/timing_rectification_holdout_freeze_contract_2026_07_22.json",
}


def read_packet(name: str) -> dict:
    return json.loads(PACKETS[name].read_text(encoding="utf-8"))


def test_kp_exact_cusp_v2_remains_blocked_without_complete_public_oracle() -> None:
    packet = read_packet("kp")
    assert packet["claim_status"] == "blocked"
    assert packet["summary"]["complete_numeric_oracle_count"] == 0
    assert packet["summary"]["runtime_observation_sync_allowed"] is True
    assert {"exact_cusp_longitudes", "cusp_sub_sub_lord"} <= set(packet["required_numeric_oracle_fields"])
    assert "no verified KP prediction claim" in packet["boundary"]


def test_muhurta_full_scoring_v2_exposes_factors_but_blocks_final_verdict() -> None:
    packet = read_packet("muhurta")
    factors = {row["factor"]: row for row in packet["factor_rows"]}
    for required in ["Tarabala", "Chandrabala", "Rahu Kalam", "Yamaganda", "Gulika Kalam", "Abhijit Muhurta", "Panchaka", "Sankranti"]:
        assert required in factors
    assert packet["summary"]["final_verdict_allowed"] is False
    assert factors["Panchaka"]["status"] == "blocked_gap"
    assert factors["Sankranti"]["status"] == "blocked_gap"
    assert "Full scoring" in packet["boundary"]


def test_prashna_tajika_v2_keeps_sensitive_points_out_of_truth_matrix() -> None:
    packet = read_packet("prashna")
    domains = {row["domain"]: row for row in packet["domain_rows"]}
    for required in ["Prashna", "Sphuta", "Gulika", "Saham", "Tajika/Varshaphala"]:
        assert required in domains
    assert packet["summary"]["numeric_oracle_ready_count"] == 0
    assert packet["truth_matrix_allowed"] is False
    assert "No Prashna/Tajika/Saham/Gulika/Sphuta domain is upgraded" in packet["boundary"]


def test_timing_holdout_freeze_contract_blocks_day_month_claims_until_labels() -> None:
    packet = read_packet("holdout")
    assert packet["claim_status"] == "blocked"
    assert packet["summary"]["frozen_label_count"] == 0
    assert packet["summary"]["day_month_claim_upgrade_allowed"] is False
    assert packet["allowed_runtime_output"]["candidate_windows"] == "exploratory_unvalidated"
    assert "birth-time truth from candidate score" in packet["blocked_output"]
