#!/usr/bin/env python3
"""Join same-unit Shadbala queue with parsed PyJHora WorkBuddy component rows."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "references/oracle/shadbala_component_closure_queue_v2_2026_07_19.json"
PYJHORA = ROOT / "references/oracle/pyjhora_steve_jobs_shadbala_stdout_components_2026_07_21.json"
OUTPUT = ROOT / "references/oracle/shadbala_component_joined_closure_packet_2026_07_21.json"

CLASSIFICATION_BUCKET = {
    "within_1_virupa_observation": "within_tolerance",
    "formula_or_unit_mismatch": "formula_or_unit_mismatch",
    "method_variant": "method_variant",
    "insufficient_numeric_sources": "insufficient_numeric_sources",
}
PRIORITY = ["naisargika", "dig", "drik", "chesta", "sthana", "kala"]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _next_action(component: str, buckets: Counter[str]) -> str:
    if component == "naisargika" and buckets["within_tolerance"]:
        return "freeze_observation_tolerance_after_second_case"
    if component in {"chesta", "sthana"}:
        return "preserve_method_variant"
    if buckets["formula_or_unit_mismatch"]:
        return "formula_source_arbitration"
    return "collect_second_public_case"


def build() -> dict[str, Any]:
    queue = _load(QUEUE)
    pyjhora = _load(PYJHORA)
    pyjhora_rows = {
        (row["planet"], row["component"]): row
        for row in pyjhora["component_rows"]
    }
    joined: list[dict[str, Any]] = []
    by_component: dict[str, Counter[str]] = defaultdict(Counter)
    for ticket in queue["tickets"]:
        key = (ticket["planet"], ticket["component"])
        py_row = pyjhora_rows.get(key)
        bucket = CLASSIFICATION_BUCKET.get(ticket["same_unit_classification"], "insufficient_numeric_sources")
        by_component[ticket["component"]][bucket] += 1
        joined.append(
            {
                "ticket_id": ticket["ticket_id"],
                "planet": ticket["planet"],
                "component": ticket["component"],
                "canonical_component": ticket["canonical_component"],
                "closure_bucket": bucket,
                "same_unit_classification": ticket["same_unit_classification"],
                "pyjhora_workbuddy_virupa": py_row["virupa"] if py_row else None,
                "pyjhora_workbuddy_rupa": py_row["rupa"] if py_row else None,
                "pyjhora_source_artifact_sha256": py_row["source_artifact_sha256"] if py_row else None,
                "normalized_values_virupa": ticket["normalized_values_virupa"],
                "next_evidence_owner": ticket["next_evidence_owner"],
                "claim_upgrade": "none",
                "claim_boundary": "Component-level explanatory partial only; no absolute Shadbala truth upgrade.",
            }
        )
    component_priority = []
    for component in PRIORITY:
        buckets = by_component[component]
        component_priority.append(
            {
                "component": component,
                "bucket_counts": dict(buckets),
                "recommended_next_action": _next_action(component, buckets),
            }
        )
    return {
        "scope": "shadbala_component_joined_closure_packet",
        "created_at": "2026-07-21",
        "claim_status": "partial",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "source_queue": str(QUEUE.relative_to(ROOT)),
        "pyjhora_component_packet": str(PYJHORA.relative_to(ROOT)),
        "summary": {
            "joined_ticket_count": len(joined),
            "pyjhora_component_rows_joined": sum(1 for row in joined if row["pyjhora_workbuddy_virupa"] is not None),
            "absolute_truth_upgrade_count": 0,
            "closure_bucket_counts": dict(Counter(row["closure_bucket"] for row in joined)),
        },
        "component_priority": component_priority,
        "joined_rows": joined,
        "boundary": "Joined PyJHora WorkBuddy component rows to existing same-unit closure tickets. This improves explanation and prioritization only; absolute parity remains unclaimed.",
    }


def main() -> int:
    packet = build()
    OUTPUT.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(packet, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
