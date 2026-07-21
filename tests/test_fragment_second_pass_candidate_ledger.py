import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "references/oracle/fragment_second_pass_candidate_ledger_2026_07_21.json"


def test_second_pass_fragment_ledger_has_only_allowed_decisions():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert data["scope"] == "fragment_second_pass_candidate_ledger"
    assert data["claim_status"] == "open_queue"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    allowed = set(data["allowed_decisions"])
    assert allowed == {
        "migrate_to_research_test_or_registry",
        "reference_only",
        "forbidden_private_or_obsolete",
    }
    assert len(data["candidates"]) == 5
    assert all(row["decision"] in allowed for row in data["candidates"])


def test_private_handan_packets_are_forbidden_not_migrated():
    rows = {
        row["candidate_id"]: row
        for row in json.loads(LEDGER.read_text(encoding="utf-8"))["candidates"]
    }
    for candidate_id in [
        "workbuddy_shadbala_handan_operator_card",
        "workbuddy_first_shadbala_packet_assistant",
    ]:
        assert rows[candidate_id]["decision"] == "forbidden_private_or_obsolete"
        assert "Do not migrate" in rows[candidate_id]["migration_plan"]


def test_reusable_fragments_become_tests_or_registries_not_runtime_copy():
    rows = {
        row["candidate_id"]: row
        for row in json.loads(LEDGER.read_text(encoding="utf-8"))["candidates"]
    }
    assert rows["workbuddy_event_judgment_engine"]["decision"] == "migrate_to_research_test_or_registry"
    assert "Do not copy old engine" in rows["workbuddy_event_judgment_engine"]["migration_plan"]
    assert rows["commercial_birth_time_journey_tests"]["decision"] == "migrate_to_research_test_or_registry"
    assert "Copy no code" in rows["commercial_birth_time_journey_tests"]["risk"]
    assert rows["vedicastro_kp_source_table_candidate"]["decision"] == "reference_only"
