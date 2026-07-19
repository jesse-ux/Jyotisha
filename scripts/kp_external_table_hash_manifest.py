#!/usr/bin/env python3
"""Report hash status for the external KP sub-lord division table."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "references/open_source_sources/VedicAstro/vedicastro/data/KP_SL_Divisions.csv"


def build_report() -> dict:
    base = {
        "scope": "kp_external_table_hash_manifest",
        "created_at": "2026-07-19",
        "production_tuning_allowed": False,
        "table_id": "VedicAstro_KP_SL_Divisions",
        "expected_path": str(TABLE.relative_to(ROOT)),
        "source_candidate": "https://github.com/diliprk/VedicAstro",
        "claim_boundary": "This manifest fixes or blocks the external KP sub/sub-lord table hash; it does not prove exact KP cusp or timing truth.",
    }
    if not TABLE.exists():
        return {
            **base,
            "status": "fixture_missing",
            "claim_status": "blocked_fixture_missing",
            "sha256": None,
            "row_count": 0,
        }
    raw = TABLE.read_bytes()
    text = raw.decode("utf-8-sig")
    rows = [line for line in text.splitlines() if line.strip()]
    return {
        **base,
        "status": "fixed_hash",
        "claim_status": "oracle_fixture_hash_fixed_not_truth",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "row_count": max(0, len(rows) - 1),
    }


def main() -> int:
    print(json.dumps(build_report(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
