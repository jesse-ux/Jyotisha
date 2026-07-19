#!/usr/bin/env python3
"""Locate KP star/sub/sub-sub/cusp surface in local VedicAstro source.

Observation-only. Does not execute or vendor VedicAstro.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "references/open_source_sources/VedicAstro"
TARGET = SRC / "vedicastro/VedicAstro.py"
PATTERNS = {
    "rl_nl_sl_function": "def get_rl_nl_sl_data",
    "planet_sub_lord": "planet_sub_lord",
    "planet_sub_sub_lord": "planet_ss_lord",
    "house_sub_lord": "house_sub_lord",
    "house_sub_sub_lord": "house_ss_lord",
    "houses_data_function": "def get_houses_data_from_chart",
}


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def locate(text: str, pattern: str) -> list[int]:
    return [i for i, line in enumerate(text.splitlines(), 1) if pattern in line]


def main() -> int:
    if not TARGET.exists():
        payload = {
            "scope": "vedicastro_kp_surface_locator",
            "status": "source_missing",
            "claim_status": "blocked_source_missing",
            "production_tuning_allowed": False,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    text = TARGET.read_text(encoding="utf-8", errors="ignore")
    findings = {
        key: {"pattern": pattern, "lines": locate(text, pattern)}
        for key, pattern in PATTERNS.items()
    }
    table_candidates = [
        str(p.relative_to(ROOT))
        for p in SRC.rglob("*")
        if p.is_file() and any(token in p.name.lower() for token in ["kp", "sub", "lord", "division"])
    ]
    payload = {
        "scope": "vedicastro_kp_surface_locator",
        "created_at": "2026-07-19",
        "status": "complete",
        "claim_status": "observation_only",
        "production_tuning_allowed": False,
        "truth_upgrade_allowed": False,
        "source_path": str(TARGET.relative_to(ROOT)),
        "source_sha256": sha256(TARGET),
        "findings": findings,
        "external_table_candidates": table_candidates,
        "kp_table_status": "fixture_missing" if not table_candidates else "candidate_paths_found",
        "boundary": "VedicAstro exposes KP RL/NL/SL/SSL and house cusp fields in source, but no external numeric worked example is validated here.",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
