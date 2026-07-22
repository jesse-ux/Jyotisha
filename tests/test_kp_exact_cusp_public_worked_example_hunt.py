import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/kp_exact_cusp_public_worked_example_hunt_2026_07_22.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_kp_exact_cusp_hunt_keeps_oracle_blocked_when_required_fields_missing():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "kp_exact_cusp_public_worked_example_hunt"
    assert data["claim_status"] == "blocked_until_oracle"
    assert data["truth_matrix_allowed"] is False
    assert data["search_status"] == "no_complete_public_numeric_worked_example_found"
    for field in ["exact_cusp_longitude", "star_lord", "sub_lord", "sub_sub_lord"]:
        assert field in data["required_fields"]
    assert "observation-only" in data["next_action"]


def test_kp_exact_cusp_hunt_records_reviewed_sources_as_candidates_only():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    sources = {row["source_id"]: row for row in data["sources_reviewed"]}
    assert "astrosage_sign_star_sub_table" in sources
    assert "indiadivine_horary_cuspal_sublord_fragment" in sources
    for source in sources.values():
        assert source["missing"]


def test_kp_exact_cusp_hunt_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["kp_exact_cusp_public_worked_example_hunt_2026_07_22"]
    assert packet["claim_status"] == "blocked_until_oracle"
    assert packet["consumer_policy"] == "research_observation_only"
