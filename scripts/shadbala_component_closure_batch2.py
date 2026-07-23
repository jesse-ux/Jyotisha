#!/usr/bin/env python3
"""Build row-level Shadbala closure packet for Sthana and Kala.

This packet explains formula/unit blockers. It deliberately does not select an
absolute school variant or tune runtime scoring.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
JOINED = ROOT / "references/oracle/shadbala_component_joined_closure_packet_2026_07_21.json"
FORMULA = ROOT / "references/oracle/formula_source_knowledge_base_2026_07_19.json"
HARD = ROOT / "references/oracle/shadbala_hard_component_arbitration_2026_07_22.json"
OUTPUT = ROOT / "references/oracle/shadbala_component_closure_batch2_2026_07_23.json"

TARGETS = ("sthana", "kala")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _formula_map() -> dict[str, dict[str, Any]]:
    data = _load(FORMULA)
    return {
        row["component"]: row
        for row in data["formulas"]
        if row.get("family") == "Shadbala" and row.get("component") in TARGETS
    }


def _hard_map() -> dict[str, dict[str, Any]]:
    data = _load(HARD)
    return {row["component"]: row for row in data.get("components", []) if row.get("component") in TARGETS}


def _max_delta(values: dict[str, Any]) -> float | None:
    numbers = [float(v) for v in values.values() if isinstance(v, (int, float))]
    if len(numbers) < 2:
        return None
    return round(max(numbers) - min(numbers), 6)


def _closure_status(component: str, source_bucket: str) -> str:
    if component == "sthana":
        if source_bucket == "method_variant":
            return "method_variant_dignity_policy_unresolved"
        return "formula_mismatch_sthana_subcomponent_unresolved"
    if component == "kala":
        return "formula_mismatch_kala_subcomponent_unresolved"
    return source_bucket


def _subcomponent_queue(component: str) -> list[str]:
    if component == "sthana":
        return [
            "moolatrikona_degree_range",
            "own/exaltation/debilitation dignity table",
            "saptavargaja/varga dignity inclusion",
            "ojayugmarasyamsa odd-even sign rule",
            "kendradi/drekkana subcomponent inclusion",
        ]
    if component == "kala":
        return [
            "natonnata/day-night strength",
            "paksha bala",
            "tribhaga/day-part strength",
            "year/month/day/hora lord strength",
            "ayana bala",
            "sunrise/sunset and local apparent time contract",
        ]
    return []


def _next_evidence(component: str) -> str:
    if component == "sthana":
        return "Split Sthana into named subcomponents, pin dignity/Moolatrikona/varga tables, then compare public numeric worked examples subcomponent-by-subcomponent."
    if component == "kala":
        return "Split Kala into sunrise/day-night/paksha/tribhaga/lord/ayana subcomponents and compare with raw-backed examples using the same local-time contract."
    return "Collect more source-cited numeric evidence."


def build() -> dict[str, Any]:
    joined = _load(JOINED)
    formulas = _formula_map()
    hard = _hard_map()
    rows = []

    for source in joined["joined_rows"]:
        component = source.get("component")
        if component not in TARGETS:
            continue
        formula = formulas[component]
        hard_component = hard[component]
        values = source.get("normalized_values_virupa", {})
        rows.append(
            {
                "ticket_id": source["ticket_id"],
                "planet": source["planet"],
                "component": component,
                "canonical_component": source["canonical_component"],
                "unit_contract": formula["unit_contract"],
                "source_formula": formula["formula_id"],
                "source_evidence": formula["source_evidence"],
                "known_variants": formula["known_variants"],
                "subcomponent_queue": _subcomponent_queue(component),
                "normalized_values_virupa": values,
                "max_delta_virupa": _max_delta(values),
                "source_bucket": source["closure_bucket"],
                "closure_status": _closure_status(component, source["closure_bucket"]),
                "dominant_issue": hard_component["dominant_issue"],
                "blocked_reason": hard_component["blocked_reason"],
                "claim_upgrade": "none",
                "truth_matrix_allowed": False,
                "production_tuning_allowed": False,
                "next_evidence": _next_evidence(component),
                "claim_boundary": "Row-level explanatory partial only; do not select an absolute Sthana/Kala Shadbala formula from this packet.",
            }
        )

    by_component = Counter(row["component"] for row in rows)
    by_status = Counter(row["closure_status"] for row in rows)
    packet = {
        "scope": "shadbala_component_closure_batch2",
        "created_at": "2026-07-23",
        "claim_status": "component_explanatory_partial",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "source_packets": {
            "joined_closure": str(JOINED.relative_to(ROOT)),
            "formula_source_knowledge_base": str(FORMULA.relative_to(ROOT)),
            "hard_component_arbitration": str(HARD.relative_to(ROOT)),
        },
        "source_packet_hashes": {
            "joined_closure_sha256": hashlib.sha256(JOINED.read_bytes()).hexdigest(),
            "formula_source_knowledge_base_sha256": hashlib.sha256(FORMULA.read_bytes()).hexdigest(),
            "hard_component_arbitration_sha256": hashlib.sha256(HARD.read_bytes()).hexdigest(),
        },
        "summary": {
            "target_components": list(TARGETS),
            "row_count": len(rows),
            "component_counts": dict(sorted(by_component.items())),
            "closure_status_counts": dict(sorted(by_status.items())),
            "absolute_truth_upgrade_count": 0,
            "blocked_or_unresolved_row_count": len(rows),
        },
        "rows": rows,
        "packet_hash": hashlib.sha256(_stable_json(rows).encode("utf-8")).hexdigest(),
        "boundary": (
            "Batch 2 advances Sthana/Kala from hard-component summary to row-level "
            "formula blocker explanations. All rows remain unresolved until "
            "subcomponent formula sources and numeric worked examples close."
        ),
    }
    return packet


def main() -> int:
    packet = build()
    OUTPUT.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(packet, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
