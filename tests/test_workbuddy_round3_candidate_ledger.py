import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/workbuddy_round3_candidate_ledger_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_workbuddy_round3_candidate_ledger_is_triage_only():
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    assert packet["scope"] == "workbuddy_round3_candidate_ledger"
    assert packet["claim_status"] == "open_queue"
    assert packet["status"] == "candidate_triage_not_runtime_truth"
    assert packet["summary"]["candidate_count"] == len(packet["entries"])
    assert packet["summary"] == {
        "candidate_count": 30,
        "migrate_to_registry": 14,
        "migrate_to_test": 7,
        "reference_only": 8,
        "forbidden_private_or_obsolete": 1,
    }
    flags = {flag for entry in packet["entries"] for flag in entry["risk_flags"]}
    assert {
        "stale_workbuddy_snapshot_review_required",
        "privacy_or_fixture_review_required",
        "external_license_boundary",
        "oracle_claim_must_not_upgrade_without_current_hash",
    } <= flags
    assert all(entry["risk_flags"] for entry in packet["entries"])
    assert all("Do not bulk copy WorkBuddy text" in entry["migration_boundary"] for entry in packet["entries"])


def test_workbuddy_round3_candidate_ledger_is_indexed_without_truth_upgrade():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    rows = [row for row in index["packets"] if row["packet_id"] == "workbuddy_round3_candidate_ledger_2026_07_21"]
    assert len(rows) == 1
    row = rows[0]
    assert row["claim_status"] == "open_queue"
    assert row["consumer_policy"] == "research_observation_only"
    assert "no runtime truth" in row["claim_boundary"]
    assert "no commercial technique upgrade" in row["claim_boundary"]
    assert index["summary"]["packet_count"] == len(index["packets"])
