#!/usr/bin/env python3
"""Build Shadbala/Ashtakavarga component provenance registry from mismatch arbitration."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


CATEGORY_POLICY = {
    "shadbala_formula_variant": {
        "component_family": "shadbala_components",
        "unit_contract": "Virupa/Rupa component unit must be explicit before parity claims.",
        "allowed_claim": "component_method_variant",
        "next_evidence_required": "worked example or source text for each six-force component formula and unit.",
    },
    "derived_total_from_component_variants": {
        "component_family": "shadbala_total",
        "unit_contract": "Total Rupa/Virupa cannot be arbitrated before component units close.",
        "allowed_claim": "derived_total_blocked_until_components_close",
        "next_evidence_required": "close sthana/dig/kala/chesta/naisargika/drik first, then recompute totals.",
    },
    "ashtakavarga_table_or_contributor_variant": {
        "component_family": "ashtakavarga",
        "unit_contract": "BAV/SAV tables must name contributor set, shodhana state, and Lagna inclusion.",
        "allowed_claim": "table_variant",
        "next_evidence_required": "public worked table with same contributor semantics and row/column schema.",
    },
    "endpoint_or_varga_semantics": {
        "component_family": "varga_endpoint",
        "unit_contract": "Sign values only; endpoint must prove requested varga/method semantics.",
        "allowed_claim": "current_target_observation_only",
        "next_evidence_required": "identified endpoint contract for D2/D4/D9/D10 ayanamsa/node/method.",
    },
}


def build_registry(arbitration_path: str | Path) -> dict[str, Any]:
    path = Path(arbitration_path)
    arbitration = json.loads(path.read_text(encoding="utf-8"))
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in arbitration.get("rows") or []:
        grouped[row["category"]].append(row)
    registry = []
    for category, rows in sorted(grouped.items()):
        policy = CATEGORY_POLICY.get(category, {
            "component_family": "unknown",
            "unit_contract": "unknown",
            "allowed_claim": "current_target_observation_only",
            "next_evidence_required": "manual provenance review required.",
        })
        registry.append({
            "category": category,
            "component_family": policy["component_family"],
            "row_count": len(rows),
            "sections": sorted({str(row.get("section")) for row in rows}),
            "sample_fields": [str(row.get("field")) for row in rows[:8]],
            "unit_contract": policy["unit_contract"],
            "allowed_claim": policy["allowed_claim"],
            "next_evidence_required": policy["next_evidence_required"],
            "truth_status": "classified_unresolved",
        })
    return {
        "scope": "shadbala_av_component_provenance_registry",
        "source_arbitration": str(path),
        "status": "classified_unresolved",
        "truth_policy": "method_variant_not_majority_vote",
        "production_tuning_allowed": False,
        "summary": {
            "source_mismatch_count": arbitration.get("mismatch_count", 0),
            "registry_count": len(registry),
            "category_counts": dict(Counter({row["category"]: row["row_count"] for row in registry})),
        },
        "registry": registry,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arbitration", nargs="?", default="references/oracle/three_engine_mismatch_arbitration_2026_07_19.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    registry = build_registry(args.arbitration)
    text = json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
