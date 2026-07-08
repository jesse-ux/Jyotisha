#!/usr/bin/env python3
"""Report traditional Jyotish maturity gaps beyond technique-name coverage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = ROOT / "references" / "traditional_maturity_gap_matrix.json"


def build_report(matrix_path: str) -> dict[str, Any]:
    matrix = json.loads(Path(matrix_path).read_text(encoding="utf-8"))
    priorities = sorted(matrix["priorities"], key=lambda item: item.get("rank", 999))
    counts: dict[str, int] = {}
    for item in priorities:
        counts[item["priority"]] = counts.get(item["priority"], 0) + 1
    return {
        "scope": matrix["scope"],
        "boundary": matrix["boundary"],
        "execution_phases": matrix.get("execution_phases", []),
        "summary": counts,
        "ordered_priorities": [{"rank": item.get("rank"), "id": item["id"], "priority": item["priority"]} for item in priorities],
        "p0": [item for item in priorities if item["priority"] == "P0"],
        "p1": [item for item in priorities if item["priority"] == "P1"],
        "p2": [item for item in priorities if item["priority"] == "P2"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", default=str(DEFAULT_MATRIX))
    args = parser.parse_args()
    print(json.dumps(build_report(args.matrix), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
