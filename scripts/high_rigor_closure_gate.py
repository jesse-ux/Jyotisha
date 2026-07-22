#!/usr/bin/env python3
"""Aggregate high-rigor closure gates.

This script is intentionally conservative: it reports what is blocked or
partial from existing governance artifacts. It does not compute predictions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "references/oracle"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _gap_items(path: str, domain: str) -> list[dict[str, Any]]:
    data = _load(ORACLE / path)
    return [
        {
            "domain": domain,
            "technique_id": item["technique_id"],
            "local_code_status": item["local_code_status"],
            "external_oracle_status": item["external_oracle_status"],
            "commercial_sync_status": item["commercial_sync_status"],
            "claim_boundary": item["claim_boundary"],
        }
        for item in data["items"]
    ]


def build_report() -> dict[str, Any]:
    kp_contract = _load(ORACLE / "kp_cusp_precision_contract_2026_07_19.json")
    prashna_packet = _load(ORACLE / "prashna_tajika_saham_gulika_sphuta_oracle_packet_2026_07_19.json")
    formula_kb = _load(ORACLE / "formula_source_knowledge_base_2026_07_19.json")
    raman_replay = _load(ORACLE / "raman_shadbala_raw_replay_and_input_drift_2026_07_22.json")
    shadbala_component_queue = _load(ORACLE / "shadbala_component_arbitration_queue_v2_2026_07_22.json")
    rectification_external_parity = _load(ORACLE / "ul_a7_a10_kp_cusp_three_engine_parity_gap_2026_07_22.json")
    rectification_same_input_probe = _load(ORACLE / "ul_a7_a10_kp_cusp_same_input_parity_probe_2026_07_22.json")
    holdout = _load(ROOT / "references/real_case_calibration/day_level_holdout_v3_human_annotation_packet_2026_07_19.json")

    full_scoring = []
    full_scoring.extend(_gap_items("kp_precision_timing_gap_registry_2026_07_19.json", "kp_precision_timing"))
    full_scoring.extend(_gap_items("muhurta_full_system_gap_registry_2026_07_19.json", "muhurta"))
    full_scoring.extend(_gap_items("ashtakavarga_advanced_usage_gap_registry_2026_07_19.json", "ashtakavarga_advanced_usage"))
    full_scoring.extend(_gap_items("compatibility_full_system_gap_registry_2026_07_19.json", "compatibility"))

    external_oracle_blockers = [
        {
            "artifact": "prashna_tajika_saham_gulika_sphuta_oracle_packet",
            "status": prashna_packet.get("status"),
            "claim_boundary": prashna_packet.get("boundary"),
        },
        {
            "artifact": "formula_source_knowledge_base",
            "status": formula_kb.get("status"),
            "claim_boundary": formula_kb.get("boundary"),
        },
    ]

    gates = [
        {
            "gate_id": "external_numeric_oracle",
            "status": "blocked",
            "evidence": external_oracle_blockers,
            "claim_boundary": "External numeric worked examples are incomplete for Prashna/Tajika/Saham/Gulika/Sphuta and formula/unit disputed components.",
        },
        {
            "gate_id": "independent_negative_holdout",
            "status": "blocked",
            "evidence": holdout,
            "claim_boundary": "Independent human-labeled negative windows are required before verified day/month timing claims.",
        },
        {
            "gate_id": "kp_exact_cusp",
            "status": "blocked",
            "evidence": kp_contract,
            "claim_boundary": kp_contract["claim_boundary"],
        },
        {
            "gate_id": "full_scoring_contracts",
            "status": "partial",
            "evidence": full_scoring,
            "claim_boundary": "KP, Muhurta, advanced Ashtakavarga and advanced compatibility have registries/probes, but full scoring remains blocked or partial.",
        },
        {
            "gate_id": "raman_shadbala_raw_identity",
            "status": "blocked",
            "evidence": raman_replay,
            "claim_boundary": "Raman Shadbala remains blocked because the declared 2026-06-27 stdout is absent and fresh replay proves input-contract drift.",
        },
        {
            "gate_id": "shadbala_component_arbitration",
            "status": "partial",
            "evidence": shadbala_component_queue,
            "claim_boundary": "Only Naisargika is same-unit closed; Chesta, Dig, Drik, Kala and Sthana remain component arbitration items.",
        },
        {
            "gate_id": "rectification_external_parity",
            "status": "blocked",
            "evidence": {
                "gap_packet": rectification_external_parity,
                "same_input_probe": rectification_same_input_probe,
            },
            "claim_boundary": "UL/A7/A10/KP cusp same-input external three-engine parity is not closed, so rectification can use these as local candidate signals only.",
        },
    ]

    return {
        "scope": "high_rigor_closure_gate",
        "created_at": "2026-07-19",
        "overall_status": "blocked",
        "production_tuning_allowed": False,
        "verified_day_month_timing_allowed": False,
        "birth_time_truth_allowed": False,
        "commercial_sync_allowed": False,
        "gates": gates,
        "next_actions": [
            {
                "action": "collect_public_numeric_oracle_packets",
                "blocked_by": ["external_numeric_oracle"],
                "target": "Prashna/Tajika/Saham/Gulika/Sphuta and Shadbala/AV disputed components",
            },
            {
                "action": "pre_register_independent_negative_holdout",
                "blocked_by": ["independent_negative_holdout"],
                "target": "day/month timing blind ranking",
            },
            {
                "action": "pin_exact_kp_cusp_oracle",
                "blocked_by": ["kp_exact_cusp"],
                "target": "KP cusp longitude + star/sub/sub-sub worked example",
            },
            {
                "action": "promote_full_scoring_only_after_oracle",
                "blocked_by": ["full_scoring_contracts", "external_numeric_oracle", "independent_negative_holdout"],
                "target": "KP/Muhurta/AV/compatibility scoring",
            },
            {
                "action": "recapture_or_replace_raman_shadbala_sample",
                "blocked_by": ["raman_shadbala_raw_identity"],
                "target": "raw-backed third Shadbala case for D3/Sapta/Sthana audits",
            },
            {
                "action": "arbitrate_shadbala_components",
                "blocked_by": ["shadbala_component_arbitration", "external_numeric_oracle"],
                "target": "Chesta mean-motion/retrograde/Seeghrochcha plus Dig/Drik/Kala/Sthana variants",
            },
            {
                "action": "capture_ul_a7_a10_kp_cusp_external_parity",
                "blocked_by": ["rectification_external_parity"],
                "target": "same-input UL/A7/A10/KP cusp external raw and field comparison",
            },
        ],
    }


def main() -> int:
    print(json.dumps(build_report(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
