#!/usr/bin/env python3
"""Build field-level Shadbala component closure tickets from same-unit rows."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SAME_UNIT = ROOT / "references/oracle/shadbala_same_unit_normalizer_2026_07_19.json"
SOURCE_KB = ROOT / "references/oracle/formula_source_knowledge_base_2026_07_19.json"


def stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def source_by_component() -> dict[str, dict[str, Any]]:
    raw = json.loads(SOURCE_KB.read_text(encoding="utf-8"))
    out: dict[str, dict[str, Any]] = {}
    for formula in raw.get("formulas", []):
        if formula.get("family") == "Shadbala" and formula.get("component") not in {"total", None}:
            out[formula["component"]] = formula
    return out


def owner_for(classification: str) -> str:
    if classification == "within_1_virupa_observation":
        return "ready_for_tolerance_freeze"
    if classification == "method_variant":
        return "method_variant_decision"
    if classification == "formula_or_unit_mismatch":
        return "formula_source_arbitration"
    return "worked_example_numeric_oracle"


def closure_for(classification: str) -> str:
    if classification == "within_1_virupa_observation":
        return "same_unit_observation_ready_tolerance_not_frozen"
    if classification == "method_variant":
        return "method_variant_unresolved"
    if classification == "formula_or_unit_mismatch":
        return "formula_or_unit_mismatch_unresolved"
    return "insufficient_numeric_sources"


def required_evidence(classification: str) -> list[str]:
    common = [
        "public numeric worked example with birth data/settings",
        "explicit Virupa/Rupa unit declaration",
    ]
    if classification == "method_variant":
        return common + ["variant selection note: preserve method_variant if authoritative sources diverge"]
    if classification == "formula_or_unit_mismatch":
        return common + ["component formula/source arbitration across local, jyotishganit, Xalen, VP Jain"]
    if classification == "within_1_virupa_observation":
        return common + ["freeze tolerance and add second public case before parity upgrade"]
    return common + ["recover missing numeric raw/hash"]


def build() -> dict[str, Any]:
    same_unit = json.loads(SAME_UNIT.read_text(encoding="utf-8"))
    sources = source_by_component()
    tickets: list[dict[str, Any]] = []

    for row in same_unit["rows"]:
        component = row["component"]
        source = sources.get(component, {})
        classification = row["classification"]
        tickets.append(
            {
                "ticket_id": f"shadbala.{row['planet'].lower()}.{component}",
                "planet": row["planet"],
                "component": component,
                "canonical_component": row["canonical_component"],
                "same_unit_classification": classification,
                "closure_status": closure_for(classification),
                "next_evidence_owner": owner_for(classification),
                "unit_contract": source.get("unit_contract", "Virupa/Rupa unit source required."),
                "known_variants": source.get("known_variants", []),
                "source_evidence": source.get("source_evidence", []),
                "required_evidence": required_evidence(classification),
                "normalized_values_virupa": {
                    "jyotishganit": row.get("jyotishganit_virupa"),
                    "xalen": row.get("xalen_virupa"),
                    "local": row.get("local_from_xalen_report_virupa"),
                    "vp_jain_published": row.get("vp_jain_published_virupa"),
                    "vp_jain_local": row.get("vp_jain_local_virupa"),
                },
                "claim_boundary": (
                    "Do not promote this component row to absolute parity until formula variant, "
                    "unit contract, and public numeric worked example all close."
                ),
            }
        )

    counts = Counter(ticket["same_unit_classification"] for ticket in tickets)
    by_component: dict[str, Counter[str]] = defaultdict(Counter)
    for ticket in tickets:
        by_component[ticket["component"]][ticket["same_unit_classification"]] += 1

    component_hotspots = []
    for component in sorted(by_component):
        c = by_component[component]
        component_hotspots.append(
            {
                "component": component,
                "ticket_count": sum(c.values()),
                "within_1_virupa_observation_count": c["within_1_virupa_observation"],
                "method_variant_count": c["method_variant"],
                "formula_or_unit_mismatch_count": c["formula_or_unit_mismatch"],
                "insufficient_numeric_sources_count": c["insufficient_numeric_sources"],
            }
        )

    return {
        "scope": "shadbala_component_closure_queue_v2",
        "created_at": "2026-07-19",
        "status": "field_level_queue_ready",
        "claim_status": "partial",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "sources": {
            "same_unit_matrix": str(SAME_UNIT.relative_to(ROOT)),
            "formula_source_knowledge_base": str(SOURCE_KB.relative_to(ROOT)),
        },
        "summary": {
            "ticket_count": len(tickets),
            "within_1_virupa_observation_count": counts["within_1_virupa_observation"],
            "method_variant_count": counts["method_variant"],
            "formula_or_unit_mismatch_count": counts["formula_or_unit_mismatch"],
            "insufficient_numeric_sources_count": counts["insufficient_numeric_sources"],
            "absolute_parity_ready_count": 0,
        },
        "queue_hash": hashlib.sha256(stable_json(tickets).encode("utf-8")).hexdigest(),
        "component_hotspots": component_hotspots,
        "tickets": tickets,
        "boundary": "Field-level Shadbala closure queue only; no majority-vote truth or production tuning upgrade.",
    }


def main() -> int:
    print(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
