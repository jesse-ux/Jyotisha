#!/usr/bin/env python3
"""Build Shadbala component arbitration queue v2 from same-unit joined rows."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
JOINED = ROOT / "references/oracle/shadbala_component_joined_closure_packet_2026_07_21.json"
OUTPUT = ROOT / "references/oracle/shadbala_component_arbitration_queue_v2_2026_07_22.json"


COMPONENT_POLICY = {
    "naisargika": {
        "status": "component_closed_same_unit",
        "next": "preserve regression coverage; no formula change",
    },
    "dig": {
        "status": "formula_model_arbitration_required",
        "next": "compare angular-distance, house-midpoint and bhava-madhya models against more raw-backed cases",
    },
    "drik": {
        "status": "aspect_model_arbitration_required",
        "next": "fix graha drishti/aspect strength scale and benefic-malefic aggregation source",
    },
    "kala": {
        "status": "subcomponent_arbitration_required",
        "next": "split natonnata, paksha, ayana, day/night and hora subcomponents before tuning",
    },
    "sthana": {
        "status": "saptavarga_dignity_arbitration_required",
        "next": "resolve Sapta/D3/D4/D7/D12/D30 dignity branches only with raw-backed third case",
    },
    "chesta": {
        "status": "method_variant_arbitration_required",
        "next": "compare mean-motion, retrograde/stationary and Seeghrochcha variants without copying AGPL code",
    },
}


def _stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build() -> dict[str, Any]:
    joined = json.loads(JOINED.read_text(encoding="utf-8"))
    rows = joined["joined_rows"]
    by_component: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_component[row["component"]].append(row)

    component_rows = []
    for component in sorted(by_component):
        component_items = by_component[component]
        buckets = Counter(row["closure_bucket"] for row in component_items)
        policy = COMPONENT_POLICY[component]
        unresolved = sum(
            count for bucket, count in buckets.items()
            if bucket not in {"within_tolerance", "component_closed_same_unit"}
        )
        component_rows.append({
            "component": component,
            "row_count": len(component_items),
            "closure_bucket_counts": dict(sorted(buckets.items())),
            "unresolved_row_count": unresolved,
            "arbitration_status": policy["status"],
            "next_evidence": policy["next"],
            "sample_tickets": [row["ticket_id"] for row in component_items[:3]],
        })

    summary = {
        "component_count": len(component_rows),
        "same_unit_row_count": len(rows),
        "component_closed_count": sum(
            1 for row in component_rows if row["arbitration_status"] == "component_closed_same_unit"
        ),
        "arbitration_required_count": sum(
            1 for row in component_rows if row["arbitration_status"] != "component_closed_same_unit"
        ),
        "absolute_truth_upgrade_count": 0,
    }
    report = {
        "scope": "shadbala_component_arbitration_queue_v2",
        "created_at": "2026-07-22",
        "claim_status": "partial",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "source_packet": str(JOINED.relative_to(ROOT)),
        "source_packet_sha256": hashlib.sha256(JOINED.read_bytes()).hexdigest(),
        "oss_reference_candidates": [
            {
                "id": "dashaflow_shadbala",
                "path": "references/open_source_sources/dashaflow/shadbala.py",
                "use": "permissive/reference candidate only",
                "boundary": "Simplified Chesta/Dig/Saptavarga model; do not treat as numeric oracle truth.",
            }
        ],
        "summary": summary,
        "component_rows": component_rows,
        "queue_hash": hashlib.sha256(_stable_json(component_rows).encode("utf-8")).hexdigest(),
        "boundary": (
            "This queue makes component-level blockers explicit. Naisargika is "
            "same-unit closed; Dig/Drik/Kala/Sthana/Chesta remain arbitration "
            "items and do not upgrade absolute Shadbala truth."
        ),
    }
    return report


def main() -> int:
    report = build()
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    OUTPUT.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
