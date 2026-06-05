#!/usr/bin/env python3
"""Build Skill-side planet position fixtures from standard_test_charts context."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STANDARD = ROOT / "references" / "standard_test_charts.json"
OUTPUT = ROOT / "references" / "planet_positions_60.json"


def main() -> int:
    data = json.loads(STANDARD.read_text(encoding="utf-8"))
    charts = []
    for chart in data.get("charts", []):
        context = chart.get("context", {})
        d1 = context.get("d1", {})
        if not d1.get("planets") or not d1.get("ascendant"):
            raise ValueError(f"Missing D1 context for {chart.get('name')}")
        charts.append(
            {
                "name": chart["name"],
                "planets": d1["planets"],
                "ascendant": d1["ascendant"],
                "context": context,
            }
        )

    output = {
        "schema_version": "2.0",
        "description": "Skill-side Yoga validation positions with D1/D9/Panchanga/Upagraha context",
        "charts": charts,
    }
    OUTPUT.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(charts)} charts to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
