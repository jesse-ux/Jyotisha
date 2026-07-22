#!/usr/bin/env python3
"""Build first-pass arbitration for stable Shadbala components."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
JOINED = ROOT / "references/oracle/shadbala_component_joined_closure_packet_2026_07_21.json"
FORMULA = ROOT / "references/oracle/formula_source_knowledge_base_2026_07_19.json"
OUTPUT = ROOT / "references/oracle/shadbala_priority_component_arbitration_2026_07_22.json"
TARGETS = ["naisargika", "dig", "drik"]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _formula_by_component() -> dict[str, dict[str, Any]]:
    data = _load(FORMULA)
    return {
        row["component"]: row
        for row in data["formulas"]
        if row.get("family") == "Shadbala" and row.get("component") in TARGETS
    }


def _status(component: str, bucket_counts: dict[str, int]) -> str:
    if component == "naisargika" and bucket_counts.get("within_tolerance") == 7:
        return "observation_tolerance_ready"
    if bucket_counts.get("formula_or_unit_mismatch"):
        return "formula_source_arbitration_required"
    if bucket_counts.get("method_variant"):
        return "method_variant_required"
    return "open_queue"


def _next_action(component: str, status: str) -> str:
    if status == "observation_tolerance_ready":
        return "Add second public case, then freeze fixed Virupa table/tolerance."
    if component == "dig":
        return "Pin house/cusp vs whole-house angular-distance policy and rerun component comparison."
    if component == "drik":
        return "Pin graha-drishti/aspect-strength model, positive/negative scale and benefic/malefic policy."
    return "Collect more numeric evidence."


def build() -> dict[str, Any]:
    joined = _load(JOINED)
    formulas = _formula_by_component()
    priorities = {row["component"]: row for row in joined["component_priority"]}
    rows = []
    for component in TARGETS:
        buckets = priorities[component]["bucket_counts"]
        status = _status(component, buckets)
        formula = formulas[component]
        rows.append(
            {
                "component": component,
                "closure_status": status,
                "bucket_counts": buckets,
                "source_formula": formula["formula_id"],
                "formula_summary": formula["formula_summary"],
                "unit_contract": formula["unit_contract"],
                "known_variants": formula["known_variants"],
                "claim_upgrade": "none",
                "next_action": _next_action(component, status),
            }
        )
    return {
        "scope": "shadbala_priority_component_arbitration",
        "created_at": "2026-07-22",
        "claim_status": "partial",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "source_joined_packet": str(JOINED.relative_to(ROOT)),
        "summary": {
            "component_count": len(rows),
            "observation_tolerance_ready_count": sum(1 for row in rows if row["closure_status"] == "observation_tolerance_ready"),
            "formula_source_arbitration_required_count": sum(1 for row in rows if row["closure_status"] == "formula_source_arbitration_required"),
            "absolute_truth_upgrade_count": 0,
        },
        "components": rows,
        "boundary": "Naisargika/Dig/Drik are prioritized for Shadbala closure. This packet explains current partial status; it does not select an absolute formula truth.",
    }


def main() -> int:
    packet = build()
    OUTPUT.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(packet, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
