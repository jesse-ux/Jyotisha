#!/usr/bin/env python3
"""CLI wrapper for functional benefic/malefic classification."""

from __future__ import annotations

import argparse
import json
from typing import Any

from functional_benefics import PLANETS, derive_functional_benefic_malefic


def _render_text(report: dict[str, Any]) -> str:
    lines = [
        "=== Oracle stdout ===",
        f"Ascendant: {report.get('ascendant')}",
        "--------------------------------------------------",
    ]
    owned_houses = report.get("owned_houses", {})
    benefics = set(report.get("functional_benefics", []))
    malefics = set(report.get("functional_malefics", []))
    yogakarakas = set(report.get("yogakarakas", []))
    for planet in PLANETS:
        owned = owned_houses.get(planet, [])
        houses = " & ".join(map(str, owned)) if owned else "-"
        if planet in yogakarakas:
            lines.append(f"{planet}: Yogakaraka (Lord of {houses}) -> Highly Auspicious")
        elif planet in benefics:
            lines.append(f"{planet}: Functional Benefic (Lord of {houses}) -> Auspicious")
        elif planet in malefics:
            lines.append(f"{planet}: Functional Malefic (Lord of {houses}) -> Destructive / Obstacle")
        else:
            lines.append(f"{planet}: Neutral / Mixed (Lord of {houses}) -> Depends on placement")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Oracle CLI: Functional Benefic/Malefic Determiner")
    parser.add_argument("--ascendant", required=True, type=str, help="The ascendant sign, e.g. Leo")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    report = derive_functional_benefic_malefic(args.ascendant)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_render_text(report))
    return 0 if report.get("status") == "used" else 1


if __name__ == "__main__":
    raise SystemExit(main())
