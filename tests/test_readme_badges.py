#!/usr/bin/env python3
"""Keep README capability badges aligned with the current registry."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
REGISTRY = ROOT / "references" / "technique_registry.json"


def _readme_badge_value(name: str) -> int:
    text = README.read_text(encoding="utf-8")
    match = re.search(rf"\[!\[{re.escape(name)}\]\(https://img\.shields\.io/badge/{name.lower()}-(\d+)-", text)
    assert match, f"Missing README badge for {name}"
    return int(match.group(1))


def test_readme_badges_match_technique_registry_counts() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    techniques = registry["techniques"].values()
    counts = Counter(item["status"] for item in techniques)
    total = len(registry["techniques"])

    assert _readme_badge_value("Capabilities") == total
    assert _readme_badge_value("Covered") == counts["covered"]
    assert _readme_badge_value("Complete") == counts["complete"]
    assert _readme_badge_value("Partial") == counts["partial"]
