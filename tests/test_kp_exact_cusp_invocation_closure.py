import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/kp_exact_cusp_invocation_closure_2026_07_21.json"
RAW = ROOT / "references/oracle/vedicastro_kp_house_cusp_raw_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_kp_invocation_closes_exact_cusp_runtime_not_oracle():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "kp_exact_cusp_invocation_closure"
    assert data["claim_status"] == "observation_only"
    assert data["truth_matrix_allowed"] is False
    assert data["runtime_invocation_status"] == "exact_cusp_star_sub_sub_raw_available"
    assert data["public_numeric_oracle_status"] == "blocked_missing_public_worked_example"
    assert data["source_raw"] == str(RAW.relative_to(ROOT))


def test_kp_invocation_has_12_cusps_and_required_fields():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["summary"]["house_count"] == 12
    assert set(data["summary"]["required_fields"]) <= set(data["schema_fields"])
    first = data["sample_cusps"][0]
    assert first["HouseNr"] == 1
    assert {"LonDecDeg", "NakshatraLord", "SubLord", "SubSubLord"} <= set(first)


def test_kp_invocation_packet_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["kp_exact_cusp_invocation_closure_2026_07_21"]
    assert packet["claim_status"] == "observation_only"
    assert packet["consumer_policy"] == "research_observation_only"
