#!/usr/bin/env python3
"""Build row-level Shadbala closure packet for the first stable components.

This is an evidence/governance artifact only. It does not change runtime
Shadbala formulas and must not be used as production tuning input.
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
DIG_AUDIT = ROOT / "references/oracle/shadbala_dig_source_of_truth_audit_2026_07_22.json"
OUTPUT = ROOT / "references/oracle/shadbala_component_closure_batch1_2026_07_23.json"

TARGETS = ("naisargika", "dig", "drik")
VISIBLE_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


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


def _dig_model_notes() -> dict[str, dict[str, Any]]:
    if not DIG_AUDIT.exists():
        return {}
    audit = _load(DIG_AUDIT)
    notes: dict[str, dict[str, Any]] = {}
    for row in audit.get("rows", []):
        planet = row.get("planet")
        if not planet:
            continue
        diffs = row.get("abs_diffs", {})
        best_model = min(diffs, key=diffs.get) if diffs else None
        notes[planet] = {
            "best_local_candidate_model": best_model,
            "best_abs_diff_rupa": diffs.get(best_model) if best_model else None,
            "candidate_models": sorted(diffs),
            "diagnostic_boundary": "Two-case diagnostic only; a best local candidate model is not a selected absolute formula truth.",
        }
    return notes


def _max_delta(values: dict[str, Any]) -> float | None:
    numbers = [float(v) for v in values.values() if isinstance(v, (int, float))]
    if len(numbers) < 2:
        return None
    return round(max(numbers) - min(numbers), 6)


def _closure_status(component: str, row: dict[str, Any]) -> str:
    bucket = row["closure_bucket"]
    if component == "naisargika" and bucket == "within_tolerance":
        return "within_tolerance_observation_closed"
    if component == "dig":
        return "formula_mismatch_angular_reference_unresolved"
    if component == "drik":
        return "formula_mismatch_aspect_model_unresolved"
    return bucket


def _next_evidence(component: str) -> str:
    if component == "naisargika":
        return "Replay at least one more public raw-backed case, then freeze the fixed seven-planet Virupa table as observation-ready."
    if component == "dig":
        return "Use public worked examples to choose house-cusp, bhava-madhya or whole-house angular reference; do not tune by majority vote."
    if component == "drik":
        return "Pin graha drishti/aspect strength, orb/interpolation and benefic-malefic sign convention against source-cited numeric examples."
    return "Collect more source-cited numeric evidence."


def build() -> dict[str, Any]:
    joined = _load(JOINED)
    formulas = _formula_map()
    dig_notes = _dig_model_notes()
    source_rows = [
        row for row in joined["joined_rows"]
        if row.get("component") in TARGETS
    ]

    rows: list[dict[str, Any]] = []
    for row in source_rows:
        component = row["component"]
        formula = formulas[component]
        values = row.get("normalized_values_virupa", {})
        item: dict[str, Any] = {
            "ticket_id": row["ticket_id"],
            "planet": row["planet"],
            "component": component,
            "canonical_component": row["canonical_component"],
            "unit_contract": formula["unit_contract"],
            "source_formula": formula["formula_id"],
            "source_evidence": formula["source_evidence"],
            "known_variants": formula["known_variants"],
            "normalized_values_virupa": values,
            "max_delta_virupa": _max_delta(values),
            "source_bucket": row["closure_bucket"],
            "closure_status": _closure_status(component, row),
            "claim_upgrade": "none",
            "truth_matrix_allowed": False,
            "production_tuning_allowed": False,
            "next_evidence": _next_evidence(component),
            "claim_boundary": "Component-level explanatory closure only; no absolute Shadbala truth or production tuning upgrade.",
        }
        if component == "dig":
            item["dig_model_diagnostic"] = dig_notes.get(row["planet"], {})
        rows.append(item)

    by_component = Counter(row["component"] for row in rows)
    by_status = Counter(row["closure_status"] for row in rows)
    packet = {
        "scope": "shadbala_component_closure_batch1",
        "created_at": "2026-07-23",
        "claim_status": "component_explanatory_partial",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "source_packets": {
            "joined_closure": str(JOINED.relative_to(ROOT)),
            "formula_source_knowledge_base": str(FORMULA.relative_to(ROOT)),
            "dig_source_of_truth_audit": str(DIG_AUDIT.relative_to(ROOT)),
        },
        "source_packet_hashes": {
            "joined_closure_sha256": hashlib.sha256(JOINED.read_bytes()).hexdigest(),
            "formula_source_knowledge_base_sha256": hashlib.sha256(FORMULA.read_bytes()).hexdigest(),
            "dig_source_of_truth_audit_sha256": hashlib.sha256(DIG_AUDIT.read_bytes()).hexdigest(),
        },
        "summary": {
            "target_components": list(TARGETS),
            "visible_planets": list(VISIBLE_PLANETS),
            "row_count": len(rows),
            "component_counts": dict(sorted(by_component.items())),
            "closure_status_counts": dict(sorted(by_status.items())),
            "absolute_truth_upgrade_count": 0,
            "closed_observation_row_count": by_status.get("within_tolerance_observation_closed", 0),
            "blocked_or_unresolved_row_count": len(rows) - by_status.get("within_tolerance_observation_closed", 0),
        },
        "rows": rows,
        "packet_hash": hashlib.sha256(_stable_json(rows).encode("utf-8")).hexdigest(),
        "boundary": (
            "Batch 1 advances Naisargika/Dig/Drik from component-level queues to "
            "row-level closure explanations. Naisargika is same-unit observation "
            "closed for this public case; Dig and Drik remain formula/method "
            "arbitration items."
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
