import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "references/oracle/research_web_skill_invocation_gap_matrix_2026_07_22.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_research_web_skill_invocation_gap_matrix_tracks_each_runtime_layer():
    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    assert data["scope"] == "research_web_skill_invocation_gap_matrix"
    assert data["claim_status"] == "open_queue"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert "not a truth upgrade matrix" in data["boundary"]

    required = {"technique", "code", "skill", "api", "ui", "oracle", "next_action", "commercial_sync"}
    for row in data["rows"]:
        assert required <= set(row)
        assert row["next_action"]
        assert row["commercial_sync"]


def test_kp_and_timing_rows_keep_observation_and_holdout_boundaries():
    rows = {row["technique"]: row for row in json.loads(MATRIX.read_text(encoding="utf-8"))["rows"]}

    kp = rows["KP exact cusp / star-sub-sub"]
    assert kp["api"] == "observation_endpoint_allowed"
    assert kp["oracle"] == "public_numeric_oracle_blocked"
    assert kp["commercial_sync"] == "sync_observation_contract_only"

    timing = rows["Day/month timing"]
    assert timing["oracle"] == "blocked_until_independent_labels"
    assert "blind ranking" in timing["next_action"]
    assert timing["commercial_sync"] == "sync_boundary_contract_only"


def test_shadbala_row_requires_component_level_display_not_single_label():
    rows = {row["technique"]: row for row in json.loads(MATRIX.read_text(encoding="utf-8"))["rows"]}
    shadbala = rows["Shadbala"]
    assert shadbala["oracle"] == "component_explanatory_partial"
    assert "same-unit component closure status" in shadbala["next_action"]


def test_research_web_skill_invocation_gap_matrix_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["research_web_skill_invocation_gap_matrix_2026_07_22"]
    assert packet["claim_status"] == "open_queue"
    assert packet["consumer_policy"] == "research_planning_only"
    assert "does not upgrade" in packet["claim_boundary"]
