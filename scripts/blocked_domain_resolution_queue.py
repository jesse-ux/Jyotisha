#!/usr/bin/env python3
"""Build an actionable queue for domains blocked by production-ready claim gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.claim_audit_runtime_gate_report import build as build_gate_report


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"

RESOLUTION = {
    "closure_governance": ("gate_snapshot_refresh", "blocked_subgates", False),
    "high_rigor_governance": ("refresh_snapshot_after_subgate_changes", "blocked_subgates", False),
    "external_oracle_identity": ("archive_self_host_or_upstream_identity_metadata", "upstream_build_identity", False),
    "timing_holdout": ("prepare_blind_eval_after_labels", "independent_human_labels", False),
    "three_engine_parity": ("continue_field_level_attribution", "field_source_oracle_arbitration", True),
    "kp_precision_timing": ("collect_exact_cusp_numeric_packet", "public_kp_worked_example", True),
    "worked_example_collection": ("promote_field_complete_candidates_to_numeric_packets", "public_numeric_worked_examples", True),
    "horary_annual_sensitive_points": ("collect_prashna_tajika_saham_gulika_sphuta_packets", "public_numeric_worked_examples", True),
    "varga_mapping": ("promote_d1_d60_sources_to_verified_packets", "public_varga_formula_sources", True),
    "conception_chart": ("keep_research_registry_until_source_oracle", "classical_source_and_oracle", False),
}

CODE_ONLY_CLOSABLE_DEPENDENCIES = {"blocked_subgates"}


def build(date: str) -> dict[str, Any]:
    gate = build_gate_report(INDEX, "production_ready")
    blocked = [row for row in gate["domains"] if row["decision"] == "block"]
    domains = []
    for row in blocked:
        local_next_action, hard_dependency, code_can_progress = RESOLUTION.get(
            row["domain"], ("triage_blocked_domain", "unknown_dependency", True)
        )
        domains.append(
            {
                "domain": row["domain"],
                "blocking_packets": row["blocking_packets"],
                "local_next_action": local_next_action,
                "hard_dependency": hard_dependency,
                "code_can_progress_without_truth_upgrade": code_can_progress,
                "claim_boundary": "Do not change claim status until blocking packets close with reproducible evidence.",
            }
        )
    return {
        "scope": "blocked_domain_resolution_queue",
        "created_at": date,
        "status": "open_queue",
        "claim_status": "open_queue",
        "production_tuning_allowed": False,
        "source_gate_report_summary": gate["summary"],
        "summary": {
            "blocked_domain_count": len(domains),
            "code_can_progress_count": sum(1 for row in domains if row["code_can_progress_without_truth_upgrade"]),
            "cannot_be_closed_by_code_only_count": sum(
                1 for row in domains if row["hard_dependency"] not in CODE_ONLY_CLOSABLE_DEPENDENCIES
            ),
        },
        "domains": domains,
        "boundary": "Resolution queue prioritizes work; it does not unblock production-ready claims.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-07-20")
    args = parser.parse_args()
    print(json.dumps(build(args.date), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
