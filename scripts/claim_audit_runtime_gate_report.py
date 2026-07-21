#!/usr/bin/env python3
"""Evaluate a requested claim against every indexed evidence domain."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.claim_audit_runtime_gate import evaluate_claim


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def build(index_path: Path, requested_claim: str) -> dict[str, Any]:
    index = json.loads(index_path.read_text(encoding="utf-8"))
    domains = sorted({row["domain"] for row in index["packets"]})
    rows = [evaluate_claim(index_path, domain, requested_claim) for domain in domains]
    decisions = {name: sum(1 for row in rows if row["decision"] == name) for name in {"allow", "block", "degrade"}}
    return {
        "scope": "claim_audit_runtime_gate_report",
        "created_at": "2026-07-19",
        "requested_claim": requested_claim,
        "source_index": str(index_path.relative_to(ROOT)) if index_path.is_relative_to(ROOT) else str(index_path),
        "summary": {
            "domain_count": len(rows),
            "blocked_count": decisions["block"],
            "degraded_count": decisions["degrade"],
            "allowed_count": decisions["allow"],
            "production_tuning_allowed_count": sum(1 for row in rows if row["production_tuning_allowed"] is True),
        },
        "domains": rows,
        "boundary": "Batch gate report only; every high claim still resolves through per-domain evidence packets.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--claim", default="production_ready")
    args = parser.parse_args()
    print(json.dumps(build(args.index, args.claim), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
