#!/usr/bin/env python3
"""Classify D1-D60 source candidates for name/use readiness."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "references/oracle/d1_d60_public_source_candidate_queue_2026_07_19.json"
REGISTRY = ROOT / "references/oracle/d1_d60_varga_mapping_registry_2026_07_19.json"


def stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def source_readiness(source: dict[str, Any]) -> str:
    if source["oracle_status"] == "observation_only":
        return "implementation_observation_only"
    return "source_text_candidate_not_numeric_oracle"


def build() -> dict[str, Any]:
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    sources = [
        {
            "url": source["url"],
            "candidate_use": source["candidate_use"],
            "readiness": source_readiness(source),
            "allowed_update": "names_and_use_notes_only",
            "blocked_update": "numeric_formula_or_truth_without_variant_review",
        }
        for source in queue["candidate_sources"]
    ]
    generic_only = [
        row
        for row in registry.get("rows", [])
        if row.get("status") == "generic_only"
    ]
    summary = {
        "candidate_source_count": len(sources),
        "generic_only_count": len(generic_only),
        "numeric_oracle_ready_count": 0,
        "allowed_scope": "names_and_use_notes_only",
    }
    return {
        "scope": "d1_d60_source_use_readiness",
        "created_at": "2026-07-19",
        "status": "source_use_readiness_ready",
        "claim_status": "partial",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "source_queue": str(QUEUE.relative_to(ROOT)),
        "source_registry": str(REGISTRY.relative_to(ROOT)),
        "summary": summary,
        "source_hash": hashlib.sha256(stable_json(sources).encode("utf-8")).hexdigest(),
        "sources": sources,
        "boundary": (
            "D1-D60 public/OSS sources can only improve names and use notes here. "
            "Generic-only divisions stay hidden from final claims until source, "
            "formula variant, and numeric oracle gates close."
        ),
    }


def main() -> int:
    print(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
