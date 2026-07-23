from __future__ import annotations

import json
from pathlib import Path

from scripts.kp_significator_runtime_delta_2026_07_23 import build_report as build_kp_runtime_delta
from scripts.muhurta_factor_probe import build_probe as build_muhurta_probe


ROOT = Path(__file__).resolve().parents[1]
KP_RUNTIME_DELTA = ROOT / "references/oracle/kp_significator_runtime_delta_2026_07_23.json"
VEDICASTRO_RAW = ROOT / "references/oracle/vedicastro_kp_house_cusp_probe_steve_jobs_sf_runtime_2026_07_23.json"
MUHURTA_PROBE = ROOT / "references/oracle/muhurta_factor_probe_2026_07_23.json"


def test_kp_significator_runtime_delta_is_deterministic_and_observation_only() -> None:
    packet = json.loads(KP_RUNTIME_DELTA.read_text(encoding="utf-8"))

    assert packet == build_kp_runtime_delta()
    assert packet["claim_status"] == "observation_only"
    assert packet["truth_matrix_allowed"] is False
    assert packet["production_tuning_allowed"] is False
    assert packet["summary"]["workflow_step_count"] == 5
    assert packet["summary"]["workflow_blocked_steps"] == 5
    assert packet["summary"]["probe_exact_cusp_status"] == "blocked_missing_oracle"
    assert packet["summary"]["probe_significator_policy"] == "supporting_probe_only"


def test_vedicastro_kp_house_cusp_runtime_packet_is_stable_and_bounded() -> None:
    packet = json.loads(VEDICASTRO_RAW.read_text(encoding="utf-8"))

    assert packet["claim_status"] == "observation_only"
    assert packet["truth_matrix_allowed"] is False
    assert packet["production_tuning_allowed"] is False
    assert packet["dependency_identity"]["flatlib"] == "0.3.1.dev0"
    assert packet["dependency_identity"]["observed_pinned_flatlib_commit"] == "2618c348ce1ab2588548f935ff65f031630b4872"
    assert packet["schema_fingerprint"]["house_count"] == 12
    assert packet["raw"]["request"]["latitude"] == 37.7749
    assert packet["raw"]["request"]["longitude"] == -122.4194
    assert packet["raw_hash"].startswith("sha256:") is False


def test_muhurta_factor_probe_packet_is_deterministic_and_nonverdict() -> None:
    packet = json.loads(MUHURTA_PROBE.read_text(encoding="utf-8"))
    probe = build_muhurta_probe("2026-07-23", 16, 8)

    assert packet == probe
    assert packet["claim_status"] == "exploratory_muhurta_candidate"
    assert packet["production_tuning_allowed"] is False
    assert packet["full_scoring_status"] == "factor_only_scoring_observation"
    assert packet["final_muhurta_verdict_status"] == "blocked_until_oracle"
    assert packet["factor_scorecard"]["favorable_factor_count"] == 5
    assert packet["factor_scorecard"]["caution_factor_count"] == 2
    assert packet["factor_scorecard"]["score_cap"] == "low"
    assert packet["factor_scorecard"]["claim_status"] == "factor_only_not_final_muhurta_verdict"
    assert "observations only" in packet["boundary"]
