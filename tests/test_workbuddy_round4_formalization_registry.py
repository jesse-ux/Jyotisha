import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "references/oracle/workbuddy_round4_formalization_registry_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"
ROUND4 = ROOT / "references/oracle/workbuddy_round4_candidate_ledger_2026_07_21.json"


def test_round4_formalization_promotes_four_domains_without_truth_upgrade():
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert data["scope"] == "workbuddy_round4_formalization_registry"
    assert data["claim_status"] == "ready_contract"
    assert data["truth_matrix_allowed"] is False
    assert data["source_ledger"] == str(ROUND4.relative_to(ROOT))
    domains = {row["domain"]: row for row in data["formalized_domains"]}
    assert {
        "event_judgment",
        "birth_time_rectification",
        "muhurta",
        "tajika_saham",
    } <= set(domains)
    for domain in domains.values():
        assert domain["formalization_type"] in {"registry", "test_contract", "registry_and_test_contract"}
        assert domain["runtime_copy_allowed"] is False
        assert domain["claim_upgrade"] == "none"
        assert domain["round4_candidate_ids"]
        assert domain["formal_outputs"]


def test_round4_formalization_links_specific_high_value_candidates():
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    linked = {
        cid
        for domain in data["formalized_domains"]
        for cid in domain["round4_candidate_ids"]
    }
    assert "wb_round4_event_judgment_examples" in linked
    assert "wb_round4_birth_time_rectification_cases" in linked
    assert "wb_round4_muhurta_complete_guide" in linked
    assert "wb_round4_saham_rules" in linked
    round4 = json.loads(ROUND4.read_text(encoding="utf-8"))
    round4_ids = {entry["candidate_id"] for entry in round4["entries"]}
    assert linked <= round4_ids


def test_round4_formalization_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["workbuddy_round4_formalization_registry_2026_07_21"]
    assert packet["claim_status"] == "ready_contract"
    assert packet["consumer_policy"] == "research_observation_only"
