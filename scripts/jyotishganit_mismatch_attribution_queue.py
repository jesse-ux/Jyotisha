#!/usr/bin/env python3
"""Classify local vs jyotishganit comparison mismatches without resolving truth."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "references/oracle/jyotishganit_vs_local_field_comparison_steve_jobs_2026_07_19.json"


def classify(row: dict) -> dict:
    section = row["section"]
    body = row["body"]
    reason = "needs_formula_variant_review"
    owner = "varga_formula_attribution"
    if section == "D4":
        reason = "schema_alias_or_formula_variant"
        owner = "D4_Turyamsa_Chaturthamsa_alias_and_formula"
    if section == "D10" and body in {"Rahu", "Ketu"}:
        reason = "node_mode_or_shadow_planet_handling"
        owner = "node_mode_mapping"
    return {
        **row,
        "attribution_status": "queued",
        "probable_reason": reason,
        "next_evidence_owner": owner,
        "claim_boundary": "Do not tune local formula to jyotishganit until source formula, ayanamsa, node mode, and schema aliases are pinned.",
    }


def build(path: Path = DEFAULT) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    mismatches = [classify(r) for r in data["rows"] if r["status"] == "mismatch"]
    return {
        "scope": "jyotishganit_mismatch_attribution_queue",
        "created_at": "2026-07-19",
        "status": "queue_ready",
        "claim_status": "partial",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "source_comparison": str(path.relative_to(ROOT)),
        "summary": {
            "mismatch_count": len(mismatches),
            "by_reason": {
                reason: sum(1 for r in mismatches if r["probable_reason"] == reason)
                for reason in sorted({r["probable_reason"] for r in mismatches})
            },
        },
        "rows": mismatches,
        "boundary": "This queue classifies mismatch work; it does not settle formula truth.",
    }


def main() -> int:
    print(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
