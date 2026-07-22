import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/truth_source_runtime_identity_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_truth_source_runtime_identity_packet_is_governance_only():
    packet = json.loads(PACKET.read_text(encoding="utf-8"))

    assert packet["scope"] == "truth_source_runtime_identity"
    assert packet["truth_source"]["path"] == "/Users/wuyongnaren/Documents/印度占星"
    assert packet["truth_source"]["role"] == "sole_main_research_truth_source"
    assert len(packet["truth_source"]["git_commit"]) == 40
    assert packet["oracle_summary"]["truth_matrix_allowed"] is False
    assert packet["oracle_summary"]["production_tuning_allowed"] is False
    assert packet["claim_boundary"] == "identity_ready_governance_only_not_oracle_truth"


def test_truth_source_runtime_identity_is_registered_in_evidence_index():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    entry = next(
        row for row in index["packets"]
        if row["packet_id"] == "truth_source_runtime_identity"
    )

    assert entry["path"] == "references/oracle/truth_source_runtime_identity_2026_07_21.json"
    assert entry["domain"] == "truth_source_governance"
    assert entry["claim_status"] == "ready_contract"


def test_workbuddy_old_copy_is_quarantined_as_fragment_only():
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    quarantine = packet["fragment_quarantine"]["workbuddy_old_copies"]

    assert quarantine["status"] == "quarantined"
    assert set(quarantine["labels"]) == {
        "not_for_truth_source",
        "privacy_review_required",
        "artifact_incomplete",
        "historical_fragment_only",
    }
    assert all("/WorkBuddy/" in path or "/.workbuddy/" in path for path in quarantine["paths"])
