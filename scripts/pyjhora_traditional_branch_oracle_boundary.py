#!/usr/bin/env python3
"""Build a field-level boundary matrix for PyJHora traditional-branch reuse."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "references/oracle/pyjhora_traditional_branch_oracle_boundary_2026_07_23.json"

MATRICES: dict[str, list[dict[str, Any]]] = {
    "tajika": [
        {
            "field": "varsha_pravesha_datetime",
            "local_repo_can_calculate": True,
            "pyjhora_can_observe": True,
            "jyotishganit_or_vedicastro_can_reference": False,
            "public_worked_example_status": "partial_source_candidates_only",
            "commercial_output_allowed": "boundary_only",
        },
        {
            "field": "muntha",
            "local_repo_can_calculate": True,
            "pyjhora_can_observe": True,
            "jyotishganit_or_vedicastro_can_reference": False,
            "public_worked_example_status": "not_closed",
            "commercial_output_allowed": "allowed_with_variant_boundary",
        },
        {
            "field": "saham_day_night_formulas",
            "local_repo_can_calculate": True,
            "pyjhora_can_observe": True,
            "jyotishganit_or_vedicastro_can_reference": False,
            "public_worked_example_status": "formula_reference_not_numeric_oracle",
            "commercial_output_allowed": "allowed_as_reference_not_verdict",
        },
        {
            "field": "tajika_yogas",
            "local_repo_can_calculate": "partial",
            "pyjhora_can_observe": True,
            "jyotishganit_or_vedicastro_can_reference": False,
            "public_worked_example_status": "blocked_named_yoga_examples_missing",
            "commercial_output_allowed": "blocked_as_final_prediction",
        },
    ],
    "kp_exact_cusp": [
        {
            "field": "12_house_cusp_longitudes",
            "local_repo_can_calculate": "partial",
            "pyjhora_can_observe": "unknown_or_partial",
            "jyotishganit_or_vedicastro_can_reference": "VedicAstro_reference_candidate",
            "public_worked_example_status": "candidate_ezine159_not_full_truth",
            "commercial_output_allowed": "boundary_only",
        },
        {
            "field": "star_lord_sub_lord",
            "local_repo_can_calculate": True,
            "pyjhora_can_observe": "unknown_or_partial",
            "jyotishganit_or_vedicastro_can_reference": "VedicAstro_csv_reference",
            "public_worked_example_status": "partial_fixture_reference",
            "commercial_output_allowed": "allowed_with_reference_boundary",
        },
        {
            "field": "significator_workflow",
            "local_repo_can_calculate": "workflow_gate_only",
            "pyjhora_can_observe": "not_primary",
            "jyotishganit_or_vedicastro_can_reference": "public_workflow_reference_only",
            "public_worked_example_status": "no_complete_event_outcome_oracle",
            "commercial_output_allowed": "explain_method_not_claim_event_truth",
        },
    ],
    "advanced_ashtakavarga": [
        {
            "field": "bav_sav_totals",
            "local_repo_can_calculate": True,
            "pyjhora_can_observe": True,
            "jyotishganit_or_vedicastro_can_reference": "jyotishganit_candidate",
            "public_worked_example_status": "component_variants_not_fully_arbitrated",
            "commercial_output_allowed": "allowed_with_component_boundary",
        },
        {
            "field": "prastara_av",
            "local_repo_can_calculate": "partial_or_registry",
            "pyjhora_can_observe": True,
            "jyotishganit_or_vedicastro_can_reference": "not_closed",
            "public_worked_example_status": "not_closed",
            "commercial_output_allowed": "reference_only",
        },
        {
            "field": "trikona_ekadhipatya_shodhana",
            "local_repo_can_calculate": "partial_or_registry",
            "pyjhora_can_observe": True,
            "jyotishganit_or_vedicastro_can_reference": "not_closed",
            "public_worked_example_status": "formula_variant_gap",
            "commercial_output_allowed": "boundary_only",
        },
        {
            "field": "transit_kakshya_av_application",
            "local_repo_can_calculate": "partial",
            "pyjhora_can_observe": True,
            "jyotishganit_or_vedicastro_can_reference": "not_closed",
            "public_worked_example_status": "real_case_holdout_missing",
            "commercial_output_allowed": "blocked_as_precise_timing_truth",
        },
    ],
}


def build() -> dict[str, Any]:
    rows = [row for matrix in MATRICES.values() for row in matrix]
    return {
        "scope": "pyjhora_traditional_branch_oracle_boundary",
        "created_at": "2026-07-23",
        "claim_status": "observation_boundary_matrix",
        "consumer_policy": "sync_matrix_only_do_not_vendor_agpl_implementation",
        "license_boundary": "PyJHora/JHora traditional branch is AGPL/reference observation only; commercial repo may sync raw/hash/boundary matrices, not implementation.",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "matrices": MATRICES,
        "summary": {
            "domain_count": len(MATRICES),
            "field_count": len(rows),
            "commercial_final_truth_allowed_count": 0,
            "commercial_blocked_or_boundary_count": len(rows),
        },
        "boundary": "Use PyJHora as a traditional-technique radar and black-box observation source for Tajika, KP and advanced AV. Do not promote observed agreement to final truth without public worked examples, raw/hash replay and license-safe adapters.",
    }


def main() -> int:
    data = build()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
