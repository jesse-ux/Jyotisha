import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/workbuddy_round4_remaining_closure_packet_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_remaining_workbuddy_candidates_are_explicitly_classified():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "workbuddy_round4_remaining_closure_packet"
    assert data["claim_status"] == "open_queue"
    assert data["truth_matrix_allowed"] is False
    rows = {row["candidate_id"]: row for row in data["remaining_candidates"]}
    assert set(rows) == {
        "wb_round4_kp_practical_event_timing",
        "wb_round4_pyjhora_steve_jobs_shadbala_stdout",
        "wb_round4_tajika_steve_jobs_1984_first_packet",
    }
    assert rows["wb_round4_kp_practical_event_timing"]["classification"] == "privacy_scrubbed_reference_only"
    assert rows["wb_round4_pyjhora_steve_jobs_shadbala_stdout"]["classification"] == "parsed_observation_packet_ready"
    assert rows["wb_round4_tajika_steve_jobs_1984_first_packet"]["classification"] == "blank_template_not_oracle"


def test_remaining_candidates_do_not_upgrade_claims():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    for row in data["remaining_candidates"]:
        assert row["claim_upgrade"] == "none"
        assert row["next_action"]


def test_remaining_closure_packet_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["workbuddy_round4_remaining_closure_packet_2026_07_21"]
    assert packet["claim_status"] == "open_queue"
    assert packet["consumer_policy"] == "research_observation_only"
