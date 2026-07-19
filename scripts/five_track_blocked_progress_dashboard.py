#!/usr/bin/env python3
"""Dashboard for the five blocked domains that can still make code progress."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "references/oracle"


def load(name: str) -> dict[str, Any]:
    return json.loads((ORACLE / name).read_text(encoding="utf-8"))


def build(date: str) -> dict[str, Any]:
    three = load("three_engine_owner_track_batch_plan_2026_07_20.json")
    worked = load("worked_example_numeric_packet_eligibility_2026_07_20.json")
    kp = load("kp_cusp_precision_contract_2026_07_19.json")
    horary = load("prashna_tajika_saham_gulika_sphuta_oracle_packet_2026_07_19.json")
    varga = load("d1_d60_source_use_readiness_2026_07_19.json")
    tracks = [
        {
            "domain": "three_engine_parity",
            "claim_status": three["claim_status"],
            "progress": three["summary"],
            "next_action": "process owner-track batches: endpoint_contract, formula_source, unit_schema, worked_example",
            "source_packets": [str((ORACLE / "three_engine_owner_track_batch_plan_2026_07_20.json").relative_to(ROOT))],
        },
        {
            "domain": "kp_precision_timing",
            "claim_status": "blocked",
            "progress": {"exact_cusp_status": kp["exact_cusp_status"], "runtime_policy": kp["kp_significator_runtime_policy"]},
            "next_action": "collect exact KP cusp numeric worked example with input/settings/raw hash",
            "source_packets": [str((ORACLE / "kp_cusp_precision_contract_2026_07_19.json").relative_to(ROOT))],
        },
        {
            "domain": "worked_example_collection",
            "claim_status": worked["claim_status"],
            "progress": worked["summary"],
            "next_action": "capture raw/hash for candidate pages and promote only field-complete numeric packets",
            "source_packets": [str((ORACLE / "worked_example_numeric_packet_eligibility_2026_07_20.json").relative_to(ROOT))],
        },
        {
            "domain": "horary_annual_sensitive_points",
            "claim_status": "blocked",
            "progress": {"packet_status": horary["status"], "technique_count": len(horary.get("techniques", []))},
            "next_action": "collect public numeric worked examples for Prashna/Tajika/Saham/Gulika/Sphuta",
            "source_packets": [str((ORACLE / "prashna_tajika_saham_gulika_sphuta_oracle_packet_2026_07_19.json").relative_to(ROOT))],
        },
        {
            "domain": "varga_mapping",
            "claim_status": varga["claim_status"],
            "progress": varga["summary"],
            "next_action": "promote D1-D60 public source candidates from names/use notes to verified formula packets only when numeric oracle exists",
            "source_packets": [str((ORACLE / "d1_d60_source_use_readiness_2026_07_19.json").relative_to(ROOT))],
        },
    ]
    return {
        "scope": "five_track_blocked_progress_dashboard",
        "created_at": date,
        "status": "progress_dashboard_ready",
        "claim_status": "open_queue",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "summary": {
            "track_count": len(tracks),
            "oracle_ready_count": 0,
            "blocked_track_count": sum(1 for row in tracks if row["claim_status"] == "blocked"),
            "open_queue_or_partial_count": sum(1 for row in tracks if row["claim_status"] != "blocked"),
        },
        "tracks": tracks,
        "boundary": "Dashboard only; tracks remain blocked/open until their source packets close with reproducible evidence.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-07-20")
    args = parser.parse_args()
    print(json.dumps(build(args.date), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
