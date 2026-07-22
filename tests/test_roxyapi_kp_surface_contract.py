import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/roxyapi_kp_surface_contract_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_roxyapi_kp_surface_contract_is_not_oracle():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "roxyapi_kp_surface_contract"
    assert data["claim_status"] == "reference_only"
    assert data["truth_matrix_allowed"] is False
    assert data["api_surface"]["endpoint"] == "POST /vedic-astrology/kp/chart"
    assert {"starLord", "subLord", "subSubLord"} <= set(data["api_surface"]["cusp_fields"])
    assert data["oracle_status"] == "blocked_missing_same_input_numeric_replay"


def test_roxyapi_kp_surface_contract_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["roxyapi_kp_surface_contract_2026_07_21"]
    assert packet["claim_status"] == "reference_only"
    assert packet["consumer_policy"] == "research_observation_only"
