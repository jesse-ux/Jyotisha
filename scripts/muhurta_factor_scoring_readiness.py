#!/usr/bin/env python3
"""Classify Muhurta factor-scoring readiness from existing OSS/local queues."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "references/oracle/muhurta_oss_factor_scoring_queue_2026_07_19.json"


def stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def readiness(status: str) -> tuple[str, list[str]]:
    if status == "oss_surface_present":
        return (
            "reference_surface_only",
            ["license verification", "formula weights", "public worked example", "same-input replay"],
        )
    if status == "local_probe_present_needs_oss_formula_alignment":
        return (
            "local_probe_needs_formula_alignment",
            ["OSS/public formula alignment", "factor weighting rule", "public worked example"],
        )
    if status == "local_probe_present_needs_public_interval_fixture":
        return (
            "local_probe_needs_public_interval_fixture",
            ["date/location fixture", "sunrise/sunset source", "expected public interval", "raw/hash"],
        )
    return ("blocked_unknown_status", ["manual review"])


def build() -> dict[str, Any]:
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    rows = []
    for item in queue["factor_rows"]:
        state, missing = readiness(item["status"])
        rows.append(
            {
                "factor": item["factor"],
                "source_status": item["status"],
                "claim": item["claim"],
                "readiness": state,
                "missing_for_scored_verdict": missing,
                "allowed_product_use": (
                    "supporting_context_only"
                    if state != "blocked_unknown_status"
                    else "hidden_until_review"
                ),
            }
        )
    summary = {
        "factor_count": len(rows),
        "supporting_context_only_count": sum(
            1 for row in rows if row["allowed_product_use"] == "supporting_context_only"
        ),
        "scored_verdict_ready_count": 0,
        "blocked_unknown_status_count": sum(
            1 for row in rows if row["readiness"] == "blocked_unknown_status"
        ),
    }
    return {
        "scope": "muhurta_factor_scoring_readiness",
        "created_at": "2026-07-19",
        "status": "readiness_ledger_ready",
        "claim_status": "partial",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "source_queue": str(QUEUE.relative_to(ROOT)),
        "summary": summary,
        "readiness_hash": hashlib.sha256(stable_json(rows).encode("utf-8")).hexdigest(),
        "rows": rows,
        "boundary": (
            "Muhurta factors may appear as supporting context only. No final "
            "scored Muhurta verdict is ready until formulas, weights, public "
            "worked examples, and raw/hash replay close."
        ),
    }


def main() -> int:
    print(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
