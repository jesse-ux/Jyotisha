import json
from pathlib import Path


LEDGER = Path("references/oracle/workbuddy_round4_candidate_ledger_2026_07_21.json")
ALLOWED = {
    "migrate_to_registry",
    "migrate_to_test",
    "reference_only",
    "forbidden_private_or_obsolete",
}


def _load():
    return json.loads(LEDGER.read_text())


def test_round4_ledger_records_non_exhaustive_workbuddy_scan():
    data = _load()
    assert data["claim_status"] == "fragment_audit_only"
    assert data["status"] == "partial_non_exhaustive"
    assert data["summary"]["round3_indexed_entries"] == 30
    assert data["summary"]["unindexed_filename_signal_total"] >= 858
    assert len(data["entries"]) == data["summary"]["round4_entries"]


def test_round4_decisions_are_bounded():
    data = _load()
    decisions = [entry["decision"] for entry in data["entries"]]
    assert set(decisions) <= ALLOWED
    for decision, expected in data["summary"]["decisions"].items():
        assert decisions.count(decision) == expected


def test_private_or_source_insufficient_packets_are_quarantined():
    data = _load()
    quarantined = [
        entry
        for entry in data["entries"]
        if entry["decision"] == "forbidden_private_or_obsolete"
    ]
    assert quarantined
    for entry in quarantined:
        lowered = (entry["source_path"] + " " + entry["reason"]).lower()
        assert "private" in lowered or "source-insufficient" in lowered
        assert entry["current_repo_same_name"] is None
