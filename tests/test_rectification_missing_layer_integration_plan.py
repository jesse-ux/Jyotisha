from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "references/oracle/rectification_missing_layer_integration_plan_2026_07_19.json"


def test_rectification_plan_covers_all_missing_layers() -> None:
    data = json.loads(PLAN.read_text(encoding="utf-8"))
    assert data["scope"] == "rectification_missing_layer_integration_plan"
    assert data["status"] == "implementation_plan_v1"
    assert data["production_tuning_allowed"] is False
    assert data["claim_boundary"] == "candidate_rectification_not_birth_time_truth"
    layers = {row["layer_id"] for row in data["layers"]}
    assert layers == {
        "narayana_dasha_cross_score",
        "jaimini_karaka_sensitivity",
        "shadbala_av_delta_score",
        "vimsopaka_avastha_state_score",
        "gochara_transit_trigger_score",
    }


def test_rectification_plan_has_tests_and_gate_for_each_layer() -> None:
    data = json.loads(PLAN.read_text(encoding="utf-8"))
    allowed_statuses = {
        "partial_runtime_cross_gate",
        "partial_observation_low_weight_gate",
        "partial_observation_holdout_blocked",
    }
    for row in data["layers"]:
        assert row["implementation_status"] in allowed_statuses
        assert row["entry_gate"]
        assert row["test_targets"]
        assert row["claim_boundary"]
        assert row["output_status"] in {"exploratory", "exploratory_observation_only"}


def test_rectification_plan_prioritizes_safe_order() -> None:
    data = json.loads(PLAN.read_text(encoding="utf-8"))
    assert [row["layer_id"] for row in data["layers"]] == [
        "narayana_dasha_cross_score",
        "jaimini_karaka_sensitivity",
        "vimsopaka_avastha_state_score",
        "shadbala_av_delta_score",
        "gochara_transit_trigger_score",
    ]
