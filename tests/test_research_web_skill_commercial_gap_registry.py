import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "references/oracle/research_web_skill_commercial_gap_registry_2026_07_20.json"


def test_research_web_skill_commercial_gap_registry_separates_research_and_commercial_runtime():
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert data["scope"] == "research_web_skill_commercial_gap_registry"
    assert data["claim_status"] == "open_queue"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False

    commercial = data["current_state"]["commercial_repo_patterns_to_learn"]
    assert commercial["source_status"] == "read_only_dirty_worktree_do_not_copy_directly"
    blocked = set(commercial["must_not_import"])
    assert "Supabase runtime" in blocked
    assert "credits/payment/subscription logic" in blocked
    assert "commercial user data" in blocked


def test_research_web_skill_gap_registry_orders_numeric_packets_before_ui_truth_upgrade():
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    order = data["recommended_order"]
    assert order[:3] == [
        "worked_examples_to_numeric_packets",
        "component_closure",
        "claim_gate_upgrade",
    ]

    tracks = {row["track"]: row for row in data["delivery_queue"]}
    assert tracks["research_web_profile_flow"]["status"] == "planned"
    assert "localStorage only" in tracks["research_web_profile_flow"]["next_delivery"]
    assert "exploratory" in tracks["research_web_rectification_journey"]["gate_for_upgrade"]
    assert "skill_truth_overlay" in tracks["skill_to_web_sync"]["next_delivery"]
