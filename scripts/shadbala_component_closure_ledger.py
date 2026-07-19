#!/usr/bin/env python3
"""Build a Shadbala component closure ledger from the same-unit matrix.

This does not change Shadbala math. It only turns existing normalized
local/Xalen/jyotishganit/VP Jain observations into auditable closure states.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SAME_UNIT = ROOT / "references/oracle/shadbala_same_unit_normalizer_2026_07_19.json"


def stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def closure_state(classification: str) -> str:
    if classification == "within_1_virupa_observation":
        return "closed_observation_same_unit"
    if classification == "method_variant":
        return "closed_as_method_variant"
    if classification == "formula_or_unit_mismatch":
        return "open_formula_or_unit_mismatch"
    return "open_insufficient_numeric_sources"


def build() -> dict[str, Any]:
    matrix = json.loads(SAME_UNIT.read_text(encoding="utf-8"))
    rows = []
    for row in matrix["rows"]:
        state = closure_state(row["classification"])
        rows.append(
            {
                "planet": row["planet"],
                "component": row["component"],
                "canonical_component": row["canonical_component"],
                "classification": row["classification"],
                "closure_state": state,
                "normalization_unit": row["normalization_unit"],
                "jyotishganit_virupa": row["jyotishganit_virupa"],
                "xalen_virupa": row["xalen_virupa"],
                "local_from_xalen_report_virupa": row["local_from_xalen_report_virupa"],
                "vp_jain_published_virupa": row["vp_jain_published_virupa"],
                "required_next_evidence": (
                    []
                    if state in {"closed_observation_same_unit", "closed_as_method_variant"}
                    else [
                        "component formula variant source",
                        "public worked example",
                        "field-level replay comparison",
                    ]
                ),
                "claim_boundary": (
                    "Closed means row-level evidence is classified, not that an "
                    "absolute Shadbala formula truth has been selected."
                ),
            }
        )
    summary = {
        "row_count": len(rows),
        "closed_observation_same_unit_count": sum(
            1 for row in rows if row["closure_state"] == "closed_observation_same_unit"
        ),
        "closed_as_method_variant_count": sum(
            1 for row in rows if row["closure_state"] == "closed_as_method_variant"
        ),
        "open_formula_or_unit_mismatch_count": sum(
            1 for row in rows if row["closure_state"] == "open_formula_or_unit_mismatch"
        ),
        "open_insufficient_numeric_sources_count": sum(
            1 for row in rows if row["closure_state"] == "open_insufficient_numeric_sources"
        ),
    }
    return {
        "scope": "shadbala_component_closure_ledger",
        "created_at": "2026-07-19",
        "status": "row_closure_ledger_ready",
        "claim_status": "partial",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "source_matrix": str(SAME_UNIT.relative_to(ROOT)),
        "source_matrix_hash": matrix["matrix_hash"],
        "summary": summary,
        "ledger_hash": hashlib.sha256(stable_json(rows).encode("utf-8")).hexdigest(),
        "rows": rows,
        "boundary": (
            "This ledger closes classification work for same-unit rows only. "
            "Open rows still require worked examples and formula-variant arbitration."
        ),
    }


def main() -> int:
    print(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
