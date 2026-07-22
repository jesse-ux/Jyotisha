"""Commercial claim contract for birth-time rectification receipts."""
from __future__ import annotations

from typing import Any


def _gate(status: str, reason: str) -> dict[str, str]:
    return {"status": status, "reason": reason}


def build_rectification_technique_contract(
    *,
    event_count: int,
    domain_count: int,
    high_rigor: bool = False,
    stability_diagnostics: dict[str, Any] | None = None,
    required_layers_complete: bool = False,
    canonical_input_hash: str = "",
    missing_required_layers: list[str] | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    if event_count < 3:
        blockers.append("insufficient_events")
    if domain_count < 2:
        blockers.append("insufficient_domains")
    if high_rigor:
        blockers.append("three_engine_parity_not_passed")
    neighbor = (stability_diagnostics or {}).get("neighbor_stability") or {}
    leave_one_out = (stability_diagnostics or {}).get("leave_one_event_out") or {}
    if not neighbor.get("all_required_passed"):
        blockers.append("neighbor_stability_not_passed")
    if leave_one_out.get("status") != "pass":
        blockers.append("leave_one_event_out_not_passed")
    if not required_layers_complete:
        blockers.append("required_layers_incomplete")
    blockers.append("minute_holdout_not_ready")
    gates = {
        "event_quality": _gate("pass" if event_count >= 3 else "fail", "requires_at_least_three_dated_events"),
        "cross_domain_coverage": _gate("pass" if domain_count >= 2 else "fail", "requires_at_least_two_event_domains"),
        "required_layers": _gate("pass" if required_layers_complete else "fail", "all_event_required_layers_must_compute"),
        "neighbor_stability": _gate("pass" if neighbor.get("all_required_passed") else "fail", "requires_unique_lead_at_plus_minus_1_2_5_minutes"),
        "leave_one_event_out": _gate("pass" if leave_one_out.get("status") == "pass" else "fail", "leader_must_survive_removing_each_event"),
        "three_engine_input_parity": _gate("fail" if high_rigor else "not_evaluated", "same_normalized_input_and_domain_parity_required"),
        "public_holdout_release": _gate("blocked", "frozen_public_AA_minute_holdout_is_below_20_cases"),
    }
    reported_missing_layers = list(dict.fromkeys([
        *(missing_required_layers or []),
        "shadbala_kala_dig_chesta_total",
    ]))
    return {
        "schema_version": 2,
        "calculation_status": "not_started" if event_count == 0 else "evaluated",
        "used_divisional_charts": ["D2", "D4", "D9", "D10", "D11", "D24", "D30"],
        "used_arudha": ["A7", "UL", "A10"],
        "dasha_tracks": ["vimshottari_md_ad_pd", "narayana_md_ad"],
        "missing_layers": reported_missing_layers,
        "partial_layers": ["shadbala_sthana_drik_naisargika"],
        "auxiliary_layers": ["functional_benefic_malefic", "controlled_transit", "ashtakavarga", "shadbala_verified_components"],
        "external_engines": {"status": "required_not_run" if high_rigor else "not_run", "providers": ["pyjhora", "jyotishganit", "vedastro"]},
        "canonical_input_hash": canonical_input_hash,
        "gates": gates,
        "hard_blockers": list(dict.fromkeys(blockers)),
        "decision": "continue_rectification",
        "confirmation_allowed": False,
        "can_narrow_to_minute": False,
        "boundary": "A candidate range is not a confirmed birth minute. Minute confirmation is disabled until the frozen public AA holdout release gate passes.",
    }
