#!/usr/bin/env python3
"""Merge Shadbala row-level closure packets into one 42-row display manifest."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BATCH1 = ROOT / "references/oracle/shadbala_component_closure_batch1_2026_07_23.json"
BATCH2 = ROOT / "references/oracle/shadbala_component_closure_batch2_2026_07_23.json"
CHESTA = ROOT / "references/oracle/shadbala_chesta_variant_packet_2026_07_20.json"
OUTPUT = ROOT / "references/oracle/shadbala_component_closure_all_rows_2026_07_23.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _chesta_rows() -> list[dict[str, Any]]:
    data = _load(CHESTA)
    rows = []
    for row in data["rows"]:
        rows.append(
            {
                "ticket_id": row["ticket_id"],
                "planet": row["planet"],
                "component": "chesta",
                "canonical_component": row["canonical_component"],
                "unit_contract": row["unit_contract"],
                "source_formula": "shadbala_chesta_bala",
                "source_evidence": row["source_evidence"],
                "known_variants": row["known_variants"],
                "normalized_values_virupa": row["normalized_values_virupa"],
                "max_delta_virupa": row["max_delta_virupa"],
                "source_bucket": row["closure_classification"],
                "closure_status": (
                    "formula_mismatch_chesta_exception_unresolved"
                    if row["closure_classification"] == "formula_or_unit_mismatch"
                    else "method_variant_chesta_policy_unresolved"
                ),
                "variant_family": row["variant_family"],
                "claim_upgrade": "none",
                "truth_matrix_allowed": False,
                "production_tuning_allowed": False,
                "next_evidence": "Pin mean-motion/retrograde/Seeghrochcha/luminary policy against source-cited public numeric examples.",
                "claim_boundary": row["claim_boundary"],
            }
        )
    return rows


def build() -> dict[str, Any]:
    batch1 = _load(BATCH1)
    batch2 = _load(BATCH2)
    rows = batch1["rows"] + batch2["rows"] + _chesta_rows()
    rows = sorted(rows, key=lambda row: (row["component"], row["planet"]))
    component_counts = Counter(row["component"] for row in rows)
    status_counts = Counter(row["closure_status"] for row in rows)
    packet = {
        "scope": "shadbala_component_closure_all_rows",
        "created_at": "2026-07-23",
        "claim_status": "component_explanatory_partial",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "source_packets": {
            "batch1": str(BATCH1.relative_to(ROOT)),
            "batch2": str(BATCH2.relative_to(ROOT)),
            "chesta_variant": str(CHESTA.relative_to(ROOT)),
        },
        "source_packet_hashes": {
            "batch1_sha256": hashlib.sha256(BATCH1.read_bytes()).hexdigest(),
            "batch2_sha256": hashlib.sha256(BATCH2.read_bytes()).hexdigest(),
            "chesta_variant_sha256": hashlib.sha256(CHESTA.read_bytes()).hexdigest(),
        },
        "summary": {
            "row_count": len(rows),
            "component_counts": dict(sorted(component_counts.items())),
            "closure_status_counts": dict(sorted(status_counts.items())),
            "closed_observation_row_count": status_counts.get("within_tolerance_observation_closed", 0),
            "absolute_truth_upgrade_count": 0,
            "truth_ready": False,
        },
        "rows": rows,
        "packet_hash": hashlib.sha256(_stable_json(rows).encode("utf-8")).hexdigest(),
        "boundary": "All 42 Shadbala rows now have row-level explanatory closure status; this is not absolute Virupa parity and cannot tune production prediction.",
    }
    return packet


def main() -> int:
    packet = build()
    OUTPUT.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(packet, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
