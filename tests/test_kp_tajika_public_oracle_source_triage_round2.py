import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/kp_tajika_public_oracle_source_triage_round2_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_round2_adds_kp_api_surface_and_steve_jobs_varshaphala_candidates():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "kp_tajika_public_oracle_source_triage_round2"
    assert data["claim_status"] == "open_queue"
    assert data["truth_matrix_allowed"] is False
    ids = {row["candidate_id"] for row in data["candidates"]}
    assert "roxyapi_kp_surface_candidate" in ids
    assert "steve_jobs_varshaphala_yumpu_candidate" in ids


def test_round2_keeps_sources_as_candidates_only():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    for row in data["candidates"]:
        assert row["promotion_status"] in {
            "api_surface_reference_only",
            "numeric_candidate_needs_source_review",
        }
        assert row["claim_upgrade"] == "none"
        assert row["missing_for_oracle"]


def test_round2_packet_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["kp_tajika_public_oracle_source_triage_round2_2026_07_21"]
    assert packet["claim_status"] == "open_queue"
    assert packet["consumer_policy"] == "research_observation_only"
