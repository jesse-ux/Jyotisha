import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENT = ROOT / "references/oracle/event_judgment_fragment_rule_family_registry_2026_07_21.json"
JOURNEY = ROOT / "references/oracle/research_birth_time_journey_ui_contract_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_event_judgment_fragment_registry_ports_rules_not_engine():
    data = json.loads(EVENT.read_text(encoding="utf-8"))
    assert data["source_policy"] == "rule_family_inventory_only_no_runtime_copy"
    assert data["claim_status"] == "ready_contract"
    routes = {row["route"]: row for row in data["route_families"]}
    assert {"relationship", "career", "wealth"} <= set(routes)
    relationship = {row["key"] for row in routes["relationship"]["required_families"]}
    assert {"d9_navamsa", "upapada_lagna", "vimshottari_current", "narayana_current"} <= relationship
    career = {row["key"] for row in routes["career"]["required_families"]}
    assert {"d10_dasamsa", "a10_karma_pada", "shadbala"} <= career
    wealth = {row["key"] for row in routes["wealth"]["required_families"]}
    assert {"d2_hora", "ashtakavarga_house_scores", "gains_convergence"} <= wealth
    assert any("Functional Benefic/Malefic" in item for item in data["global_requirements"])


def test_birth_time_journey_contract_ports_behavior_not_commercial_runtime():
    data = json.loads(JOURNEY.read_text(encoding="utf-8"))
    assert data["source_policy"] == "behavior_contract_only_no_commercial_code"
    contracts = {row["contract_id"]: row for row in data["contracts"]}
    assert {
        "profile_mode_hides_chat_overlay",
        "new_chat_restores_chat_surface",
        "candidate_claim_stays_exploratory",
        "local_resume_only",
        "user_error_contract",
    } <= set(contracts)
    assert "Supabase runtime" in data["forbidden_imports"]
    assert "credits/payment/subscription logic" in data["forbidden_imports"]


def test_fragment_migration_registries_are_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    assert packets["event_judgment_fragment_rule_family_registry_2026_07_21"]["claim_status"] == "ready_contract"
    assert packets["research_birth_time_journey_ui_contract_2026_07_21"]["claim_status"] == "ready_contract"
