import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUND4 = ROOT / "references/oracle/workbuddy_round4_candidate_ledger_2026_07_21.json"
FORMAL = ROOT / "references/oracle/workbuddy_round4_formalization_registry_2026_07_21.json"
QUEUE = ROOT / "references/oracle/workbuddy_round4_usage_closure_queue_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_every_round4_migrate_candidate_has_usage_status():
    round4 = json.loads(ROUND4.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    migrate_ids = {
        entry["candidate_id"]
        for entry in round4["entries"]
        if entry["decision"] in {"migrate_to_registry", "migrate_to_test"}
    }
    queued_ids = {row["candidate_id"] for row in queue["candidate_status"]}
    assert migrate_ids <= queued_ids


def test_usage_queue_separates_used_from_deferred_without_truth_upgrade():
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    assert queue["claim_status"] == "open_queue"
    assert queue["truth_matrix_allowed"] is False
    statuses = {row["usage_status"] for row in queue["candidate_status"]}
    assert {"formalized", "deferred_pending_oracle"} <= statuses
    for row in queue["candidate_status"]:
        assert row["usage_status"] in {
            "formalized",
            "deferred_pending_oracle",
            "deferred_pending_invocation_audit",
        }
        assert row["claim_upgrade"] == "none"


def test_formalized_ids_are_consistent_with_formalization_registry():
    formal = json.loads(FORMAL.read_text(encoding="utf-8"))
    formalized_ids = {
        cid
        for domain in formal["formalized_domains"]
        for cid in domain["round4_candidate_ids"]
    }
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    for row in queue["candidate_status"]:
        if row["usage_status"] == "formalized":
            assert row["candidate_id"] in formalized_ids


def test_usage_queue_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["workbuddy_round4_usage_closure_queue_2026_07_21"]
    assert packet["claim_status"] == "open_queue"
    assert packet["consumer_policy"] == "research_observation_only"
