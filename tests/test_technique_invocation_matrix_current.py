import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "references/oracle/technique_invocation_matrix_current_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_invocation_matrix_tracks_code_skill_api_ui_gate_oracle():
    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    assert data["scope"] == "technique_invocation_matrix_current"
    rows = {row["technique"]: row for row in data["rows"]}
    for technique in ["Shadbala", "KP exact cusp", "Tajika/Varshaphala", "Birth-time rectification", "Day/month timing"]:
        row = rows[technique]
        assert {"code", "skill", "api", "ui", "claim_gate", "oracle_status"} <= set(row)
    assert rows["Shadbala"]["oracle_status"] == "component_explanatory_partial"
    assert rows["KP exact cusp"]["oracle_status"] == "calculable_displayable_public_oracle_blocked"
    assert rows["KP exact cusp"]["evidence"] == "references/oracle/kp_observation_sync_contract_2026_07_22.json"
    assert rows["Day/month timing"]["claim_gate"] == "exploratory_candidate_only"


def test_invocation_matrix_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["technique_invocation_matrix_current_2026_07_21"]
    assert packet["claim_status"] == "partial"
    assert packet["consumer_policy"] == "research_observation_only"
