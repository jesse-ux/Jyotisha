import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/workbuddy_round5_transfer_status_2026_07_22.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_workbuddy_round5_accounts_for_all_round4_candidates():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "workbuddy_round5_transfer_status"
    assert data["claim_status"] == "ready_contract"
    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False
    assert data["summary"]["candidate_count"] == 20
    assert data["summary"]["transferred_to_research_registry_or_test"] == 12
    assert data["summary"]["reference_only_not_runtime"] == 6
    assert data["summary"]["forbidden_private_or_obsolete"] == 2
    assert "not all copied" in data["answer_to_user"]


def test_workbuddy_round5_links_high_value_transfers_to_current_research_packets():
    rows = {row["candidate_id"]: row for row in json.loads(PACKET.read_text(encoding="utf-8"))["rows"]}
    assert rows["wb_round4_pyjhora_steve_jobs_shadbala_stdout"]["research_target"] == (
        "references/oracle/shadbala_component_closure_rollup_2026_07_22.json"
    )
    assert rows["wb_round4_kp_practical_event_timing"]["research_target"] == (
        "references/oracle/kp_observation_sync_contract_2026_07_22.json"
    )
    assert rows["wb_round4_muhurta_complete_guide"]["research_target"] == (
        "references/oracle/muhurta_observation_factor_packet_2026_07_22.json"
    )
    assert rows["wb_round4_tajika_steve_jobs_1984_first_packet"]["research_target"] == (
        "references/oracle/tajika_steve_jobs_1984_extraction_contract_2026_07_21.json"
    )


def test_workbuddy_round5_keeps_private_pending_packets_forbidden():
    rows = {row["candidate_id"]: row for row in json.loads(PACKET.read_text(encoding="utf-8"))["rows"]}
    for candidate_id in [
        "wb_round4_user_1993_shadbala_pending_packet",
        "wb_round4_handan_shadbala_pending_packet",
    ]:
        row = rows[candidate_id]
        assert row["round5_status"] == "forbidden_private_or_obsolete"
        assert row["research_target"] is None
        assert "not for truth source" in row["boundary"]


def test_workbuddy_round5_status_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["workbuddy_round5_transfer_status_2026_07_22"]
    assert packet["claim_status"] == "ready_contract"
    assert packet["consumer_policy"] == "research_governance_only"
