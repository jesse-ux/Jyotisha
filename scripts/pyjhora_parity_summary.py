#!/usr/bin/env python3
"""Summarize reviewable PyJHora comparison matrices without overstating coverage."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REQUIRED_FULL_PARITY = ("D1", "D9", "D10", "D2", "D4", "Vimshottari", "Shadbala", "Ashtakavarga")
MATRIX_SECTION_MAP = {"ascendant": "D1", "planet": "D1", "dasha": "Vimshottari", "D9": "D9", "D10": "D10"}


def summarize_matrix(path: str | Path, *, settings: dict[str, Any]) -> dict[str, Any]:
    path = Path(path)
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    status_counts = Counter(str(row.get("status") or "unknown") for row in rows)
    sections: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "match": 0, "mismatch": 0})
    covered = set()
    for row in rows:
        section = MATRIX_SECTION_MAP.get(str(row.get("section") or ""))
        if not section:
            continue
        covered.add(section)
        sections[section]["total"] += 1
        if row.get("status") == "match":
            sections[section]["match"] += 1
        elif row.get("status") == "mismatch":
            sections[section]["mismatch"] += 1
    missing = [field for field in REQUIRED_FULL_PARITY if field not in covered]
    return {
        "scope": "pyjhora_same_chart_parity_summary",
        "matrix_path": str(path),
        "tested": bool(rows),
        "settings": settings,
        "row_counts": dict(status_counts),
        "coverage": dict(sorted(sections.items())),
        "covered_outputs": sorted(covered),
        "missing_required_outputs": missing,
        "status": "partial_verified" if rows and not status_counts.get("mismatch") else "partial_mismatch",
        "full_parity_verified": not missing and not status_counts.get("mismatch"),
        "boundary": "Only covered outputs are compared. This summary cannot promote full parity while required outputs are absent.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix")
    parser.add_argument("--ayanamsa", default="lahiri")
    parser.add_argument("--node-mode", default="mean", choices=["mean", "true"])
    args = parser.parse_args()
    print(json.dumps(summarize_matrix(args.matrix, settings={"ayanamsa": args.ayanamsa, "node_mode": args.node_mode}), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
