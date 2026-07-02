#!/usr/bin/env python3
"""Validate interpretation source inventory wiring and draft quarantine."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp_server import _existing_interpretation_source_pack  # noqa: E402


REQUIRED_LAYERS = [
    "primary_truth",
    "frontend_interpretation",
    "qa_governance",
    "reader_validation",
    "yoga_rules",
    "saham_rules",
    "quarantined_drafts",
]


def build_report() -> dict[str, Any]:
    source_pack = _existing_interpretation_source_pack()
    inventory = source_pack.get("interpretation_source_inventory") if isinstance(source_pack, dict) else {}
    if not isinstance(inventory, dict):
        inventory = {}
    layers = inventory.get("layers") if isinstance(inventory.get("layers"), dict) else {}
    summary = inventory.get("summary") if isinstance(inventory.get("summary"), dict) else {}
    source_refs = source_pack.get("source_refs") if isinstance(source_pack.get("source_refs"), list) else []
    missing_layers = [name for name in REQUIRED_LAYERS if name not in layers]
    missing_refs = inventory.get("missing_refs") if isinstance(inventory.get("missing_refs"), list) else []
    promoted_quarantined = (
        inventory.get("promoted_quarantined_refs")
        if isinstance(inventory.get("promoted_quarantined_refs"), list)
        else []
    )
    failures: list[dict[str, Any]] = []
    if source_pack.get("status") != "used":
        failures.append({"id": "source_pack_not_used", "status": source_pack.get("status")})
    if inventory.get("status") != "used":
        failures.append({"id": "inventory_not_used", "status": inventory.get("status")})
    if missing_layers:
        failures.append({"id": "missing_inventory_layers", "layers": missing_layers})
    if missing_refs:
        failures.append({"id": "missing_source_refs", "refs": missing_refs})
    if promoted_quarantined:
        failures.append({"id": "quarantined_drafts_promoted", "refs": promoted_quarantined})

    status = "pass" if not failures else "fail"
    return {
        "scope": "interpretation_source_inventory_gate",
        "status": status,
        "source_pack_status": source_pack.get("status"),
        "inventory_status": inventory.get("status"),
        "summary": summary,
        "layers": layers,
        "runtime_source_refs": source_refs,
        "failures": failures,
        "boundary": (
            "This gate validates explicit source inventory wiring. It does not promote drafts "
            "or replace MEVG/global-web/real-case verification for interpretive claims."
        ),
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
