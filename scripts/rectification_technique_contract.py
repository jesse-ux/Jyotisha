"""Commercial claim contract for birth-time rectification receipts."""
from __future__ import annotations

from typing import Any

try:
    from scripts.rectification_policy import (
        MIN_CONFIRMATION_DOMAINS,
        MIN_CONFIRMATION_EVENTS,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from rectification_policy import MIN_CONFIRMATION_DOMAINS, MIN_CONFIRMATION_EVENTS


def _gate(status: str, reason: str) -> dict[str, str]:
    return {"status": status, "reason": reason}


def build_rectification_technique_contract(
    *,
    event_count: int,
    domain_count: int,
    high_rigor: bool = False,
    local_candidate_ready: bool = False,
    stability_diagnostics: dict[str, Any] | None = None,
    required_layers_complete: bool = False,
    canonical_input_hash: str = "",
    missing_required_layers: list[str] | None = None,
    external_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    if event_count < MIN_CONFIRMATION_EVENTS:
        blockers.append("insufficient_events")
    if domain_count < MIN_CONFIRMATION_DOMAINS:
        blockers.append("insufficient_domains")
    neighbor = (stability_diagnostics or {}).get("neighbor_stability") or {}
    leave_one_out = (stability_diagnostics or {}).get("leave_one_event_out") or {}
    external = external_validation or {}
    external_status = str(external.get("status") or "not_evaluated")
    if not local_candidate_ready:
        blockers.append("local_candidate_not_ready")
    if not required_layers_complete:
        blockers.append("required_layers_incomplete")
    if not high_rigor:
        blockers.append("vedastro_validation_required")
    elif external_status != "pass":
        blockers.extend(external.get("blockers") or ["vedastro_validation_not_passed"])
    confirmation_allowed = (
        event_count >= MIN_CONFIRMATION_EVENTS
        and domain_count >= MIN_CONFIRMATION_DOMAINS
        and local_candidate_ready
        and required_layers_complete
        and high_rigor
        and external_status == "pass"
    )
    gates = {
        "event_quality": _gate("pass" if event_count >= MIN_CONFIRMATION_EVENTS else "fail", "requires_confirmation_event_count"),
        "cross_domain_coverage": _gate("pass" if domain_count >= MIN_CONFIRMATION_DOMAINS else "fail", "requires_confirmation_domain_count"),
        "local_candidate": _gate("pass" if local_candidate_ready else "fail", "requires_final_confirmation_width_and_margin_policy"),
        "required_layers": _gate("pass" if required_layers_complete else "fail", "all_event_required_layers_must_compute"),
        "neighbor_stability": _gate("pass" if neighbor.get("all_required_passed") else "diagnostic_fail", "diagnostic_only_unique_lead_at_plus_minus_1_2_5_minutes"),
        "leave_one_event_out": _gate("pass" if leave_one_out.get("status") == "pass" else "diagnostic_fail", "diagnostic_only_leader_survival_after_removing_each_event"),
        "three_engine_input_parity": _gate(
            "pass" if external.get("mismatch_count") == 0 and external.get("engine_status") else "fail" if high_rigor and external_status != "not_evaluated" else "not_evaluated",
            "local_pyjhora_and_jyotishganit_must_match_the_same_candidate_input",
        ),
        "vedastro_official_response": _gate(
            "pass" if external.get("vedastro_status") == "official_verified" else "fail" if high_rigor and external_status != "not_evaluated" else "not_evaluated",
            str(external.get("vedastro_reason") or "official_vedastro_response_required_before_minute_sensitive_validation"),
        ),
        "vedastro_minute_sensitive_validation": _gate(
            "pass" if (external.get("minute_sensitive_validation") or {}).get("status") == "pass" else "fail" if high_rigor and external_status != "not_evaluated" else "not_evaluated",
            "official_ascendant_house_D9_D10_and_dasha_candidate_identity_must_discriminate_the_local_winner_from_runner_up",
        ),
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
        "external_engines": {
            "status": external_status,
            "providers": ["pyjhora", "jyotishganit", "vedastro"],
            "validation": external,
        },
        "canonical_input_hash": canonical_input_hash,
        "gates": gates,
        "hard_blockers": list(dict.fromkeys(blockers)),
        "decision": "confirm_minute" if confirmation_allowed else "continue_rectification",
        "confirmation_allowed": confirmation_allowed,
        "can_narrow_to_minute": confirmation_allowed,
        "boundary": (
            "The narrow local candidate passed required-layer, three-engine, and official VedAstro minute-sensitive identity validation. SearchEvents is background evidence only. Neighbor and leave-one-event-out stability remain diagnostic confidence indicators. Explicit user confirmation is still required before replacing the stored birth time."
            if confirmation_allowed
            else "A candidate range is not a confirmed birth minute. Continue until local candidate calculation, required layers, three-engine parity, and official VedAstro minute-sensitive identity validation pass. SearchEvents remains background evidence only; neighbor and leave-one-event-out results are diagnostic rather than hard blockers."
        ),
    }
