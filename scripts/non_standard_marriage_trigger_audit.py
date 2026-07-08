#!/usr/bin/env python3
"""Audit public non-standard marriage timing trigger cases."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "references" / "non_standard_marriage_trigger_cases.json"


def _resolve(path: str | None) -> Path:
    if not path:
        return DEFAULT_CASES
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def audit_cases(path: str | None = None) -> dict[str, Any]:
    data = json.loads(_resolve(path).read_text(encoding="utf-8"))
    standard = set(data["standard_marriage_lords"])
    rows: list[dict[str, Any]] = []
    lord_counts: Counter[str] = Counter()
    link_counts: Counter[str] = Counter()

    for case in data["cases"]:
        active = set(case.get("reported_dasha") or [])
        non_standard = sorted(active - standard)
        links = sorted(set(case.get("marriage_network_links") or []))
        lord_counts.update(non_standard)
        link_counts.update(links)
        rows.append(
            {
                "id": case["id"],
                "event_date": case["event_date"],
                "reported_dasha": case.get("reported_dasha", []),
                "classification": "non_standard_proxy" if non_standard and links else "standard_or_blocked",
                "non_standard_lords": non_standard,
                "marriage_network_links": links,
                "source": case["source"],
                "url": case["url"],
            }
        )

    return {
        "scope": "non_standard_marriage_trigger_audit",
        "schema_version": 1,
        "case_count": len(data["cases"]),
        "standard_marriage_lords": sorted(standard),
        "summary": {
            "non_standard_proxy_cases": sum(row["classification"] == "non_standard_proxy" for row in rows),
            "top_non_standard_lords": lord_counts.most_common(),
            "top_marriage_network_links": link_counts.most_common(),
        },
        "rules": data["rules"],
        "rows": rows,
        "boundary": (
            "Use this only to prevent over-narrow Venus/Jupiter/Saturn timing claims. "
            "A non-standard lord still needs chart-specific D1/D9/UL/DK/A7, dasha subperiod and transit confirmation."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", default=None)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    print(json.dumps(audit_cases(args.cases), ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
