import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/muhurta_observation_factor_packet_2026_07_22.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_muhurta_observation_packet_captures_requested_factors_without_verdict():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "muhurta_observation_factor_packet"
    assert data["claim_status"] == "observation_only"
    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False
    assert data["verified_muhurta_verdict"] is False
    assert data["observed_factor_keys"] == [
        "tarabala",
        "chandrabala",
        "rahu_kalam",
        "abhijit_muhurta",
    ]
    assert data["full_scoring_status"] == "blocked_until_oracle"
    assert "No final Muhurta scoring" in data["boundary"]


def test_muhurta_observation_packet_has_replay_hash_and_raw_observation():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert len(data["raw_sha256"]) == 64
    assert data["canonical_request"]["date"] == "2026-07-19"
    assert data["factor_status"]["tarabala"] == "computed_rule_probe"
    assert data["factor_status"]["chandrabala"] == "computed_rule_probe"
    assert data["factor_status"]["rahu_kalam"] == "present"
    assert data["factor_status"]["abhijit_muhurta"] == "present"
    assert data["raw_observation"]["claim_status"] == "exploratory_muhurta_candidate"


def test_muhurta_observation_packet_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["muhurta_observation_factor_packet_2026_07_22"]
    assert packet["claim_status"] == "observation_only"
    assert packet["consumer_policy"] == "research_observation_only"
