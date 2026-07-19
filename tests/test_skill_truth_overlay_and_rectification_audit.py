from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "references/oracle/skill_truth_overlay_2026_07_19.json"
RECT = ROOT / "references/oracle/rectification_technique_usage_audit_2026_07_19.json"


def test_skill_truth_overlay_corrects_overclaimed_registry_items() -> None:
    data = json.loads(OVERLAY.read_text(encoding="utf-8"))
    assert data["scope"] == "skill_truth_overlay"
    assert data["status"] == "truth_overlay_v1"
    corrected = {row["technique_id"]: row["corrected_status"] for row in data["overrides"]}
    assert corrected["kp_system"] == "reference_only"
    assert corrected["muhurta"] == "reference_only"
    assert corrected["gochara_event_timing"] == "reference_only"
    assert corrected["sahams"] == "blocked"
    assert corrected["sphuta_trisphuta_family"] == "blocked"
    assert corrected["tajika_yogas"] == "partial"


def test_rectification_audit_identifies_used_and_guarded_layers() -> None:
    data = json.loads(RECT.read_text(encoding="utf-8"))
    used = {row["technique_id"]: row for row in data["used_layers"]}
    assert {"candidate_time_sweep", "vimshottari_event_scoring", "varga_change_scoring", "d60_late_reference"}.issubset(used)
    assert {
        "narayana_dasha_rectification",
        "jaimini_karaka_rectification",
        "shadbala_av_rectification",
        "vimsopaka_avastha_rectification",
        "gochara_transit_rectification",
    }.issubset(used)
    assert used["shadbala_av_rectification"]["status"] == "partial_observation_low_weight_gate"
    assert used["gochara_transit_rectification"]["status"] == "partial_observation_holdout_blocked"
    assert data["claim_boundary"] == "rectification_candidate_scoring_not_birth_time_truth"


def test_rectification_audit_keeps_all_partial_layers_guarded() -> None:
    data = json.loads(RECT.read_text(encoding="utf-8"))
    assert data["not_yet_used_layers"] == []
    for row in data["used_layers"]:
        assert row["claim_boundary"]
    guarded = [row for row in data["used_layers"] if "rectification" in row["technique_id"]]
    assert guarded
    assert all("truth" in row["claim_boundary"] or "proof" in row["claim_boundary"] or "correction" in row["claim_boundary"] or "confidence" in row["claim_boundary"] for row in guarded)
