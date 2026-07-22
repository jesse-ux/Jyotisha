import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/kp_public_source_candidate_update_2026_07_22.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_kp_public_source_update_keeps_oracle_blocked():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "kp_public_source_candidate_update"
    assert data["claim_status"] == "blocked_until_oracle"
    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False
    assert data["runtime_sync_policy"]["kp_status"] == "calculable_displayable_public_oracle_blocked"
    assert "verified precise event timing" in data["runtime_sync_policy"]["forbidden"]


def test_kp_public_source_update_records_reference_table_and_partial_cusp_sources():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    sources = {row["source_id"]: row for row in data["source_basis"]}
    assert "astrosage_sign_star_sub_table" in sources
    assert "astrosage_fundamental_principles" in sources
    partial = sources["archive_khullar_partial_cusp"]["observed_partial_fact"]
    assert partial == {
        "cusp": "11th",
        "sign": "Sagittarius",
        "degree_dms": "27°48'40\"",
    }
    for row in data["source_basis"]:
        assert row["missing_for_numeric_oracle"]


def test_kp_public_source_update_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["kp_public_source_candidate_update_2026_07_22"]
    assert packet["claim_status"] == "blocked_until_oracle"
    assert packet["consumer_policy"] == "research_observation_only"
