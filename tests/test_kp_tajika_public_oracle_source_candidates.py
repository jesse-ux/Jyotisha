import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/kp_tajika_public_oracle_source_candidates_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_public_candidates_are_not_numeric_oracles_yet():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "kp_tajika_public_oracle_source_candidates"
    assert data["claim_status"] == "open_queue"
    assert data["truth_matrix_allowed"] is False
    domains = {row["domain"] for row in data["candidates"]}
    assert {"kp_exact_cusp", "tajika_varshaphala"} <= domains
    for row in data["candidates"]:
        assert row["promotion_status"] in {"candidate_needs_numeric_extraction", "candidate_reference_only"}
        assert row["claim_upgrade"] == "none"


def test_candidates_record_why_steve_jobs_tajika_and_kp_are_still_open():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    by_id = {row["candidate_id"]: row for row in data["candidates"]}
    assert by_id["kp_249_sub_lord_table_candidate"]["missing_for_oracle"]
    assert by_id["tajika_varshaphala_worked_example_pdf_candidate"]["missing_for_oracle"]
    assert by_id["steve_jobs_1984_tajika_template"]["promotion_status"] == "candidate_reference_only"


def test_public_candidate_packet_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["kp_tajika_public_oracle_source_candidates_2026_07_21"]
    assert packet["claim_status"] == "open_queue"
    assert packet["consumer_policy"] == "research_observation_only"
