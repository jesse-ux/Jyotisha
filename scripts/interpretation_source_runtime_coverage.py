#!/usr/bin/env python3
"""Machine-checkable runtime coverage summary for interpretation sources."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROVEN_RUNTIME_MARKERS = [
    "dasha_timing_layer_used",
    "varga_strength_layer_used",
    "annual_special_layer_context",
    "modifier_obstacle_layer_used",
]

NOT_FULLY_CLOSED = [
    "references/open_source_sources/jyotishganit",
    "references/open_source_sources/jaimini-tropical",
    "references/open_source_sources/VedicAstro",
    "references/open_source_sources/rishi-ai-mcp",
    "references/open_source_sources/vedic-astro-skills",
    "references/open_source_sources/dashaflow",
]


def build_report() -> dict:
    completed = subprocess.run(
        [sys.executable, "scripts/interpretation_source_inventory_gate.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    inventory = {}
    if completed.returncode == 0 and completed.stdout.strip():
        inventory = json.loads(completed.stdout)
    source_pack_status = (
        inventory.get("source_pack_status")
        if isinstance(inventory, dict)
        else None
    ) or "unknown"
    return {
        "scope": "interpretation_source_runtime_coverage",
        "status": "partial",
        "source_pack_status": source_pack_status,
        "proven_runtime_markers": PROVEN_RUNTIME_MARKERS,
        "runtime_visibility_status": "partial",
        "not_fully_closed": NOT_FULLY_CLOSED,
        "inventory_gate": {
            "status": inventory.get("status") if isinstance(inventory, dict) else "unavailable",
            "summary": inventory.get("summary") if isinstance(inventory, dict) else {},
        },
        "boundary": (
            "Inventory/grading exists, but runtime invocation is only proven for surfaced "
            "strict-workflow markers, not every local source asset."
        ),
    }


def main() -> int:
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
