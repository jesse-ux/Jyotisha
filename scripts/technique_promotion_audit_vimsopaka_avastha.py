#!/usr/bin/env python3
"""Audit Vimsopaka/Avastha fragments against current runtime entrypoints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _contains(path: Path, tokens: list[str]) -> bool:
    text = path.read_text(encoding="utf-8")
    return all(token in text for token in tokens)


def build_audit(root: Path) -> dict:
    full_reading = root / "scripts/full_reading.py"
    api_server = root / "scripts/jyotish_api_server.py"
    deep = root / "scripts/deep_varga_avastha.py"
    tests = root / "tests/test_cli_smoke.py"
    deep_tests = root / "tests/test_deep_varga_avastha.py"

    vimsopaka_called = _contains(tests, ["vimsopaka_semantic_summary", "modules", "vimsopaka"])
    avastha_called = _contains(api_server, ["/api/deep_varga_avastha", "_compute_deep_varga_avastha"]) and _contains(
        deep, ["AvasthaCalculator", "DivisionalChartsCalculator"]
    )

    items = [
        {
            "technique_id": "vimsopaka_bala",
            "current_call_status": "formally_called_in_full_reading" if vimsopaka_called else "partial",
            "main_artifacts": ["scripts/full_reading.py", "tests/test_cli_smoke.py"],
            "historical_artifacts": ["skills/jyotish-engine-modules/scripts/vimsopaka_calculator.py"],
            "entrypoints": ["full_reading prompt pack", "vimsopaka_semantic_summary"],
            "reuse_decision": "do_not_duplicate_runtime",
            "next_action": "add_formula_source_and_oracle_packet",
            "claim_boundary": "Runtime presence is real, but Vimsopaka weight table/source/oracle closure is still separate.",
        },
        {
            "technique_id": "avastha_states",
            "current_call_status": "formally_called_via_deep_varga_avastha_endpoint" if avastha_called else "partial",
            "main_artifacts": [
                "scripts/deep_varga_avastha.py",
                "scripts/jyotish_api_server.py",
                "tests/test_deep_varga_avastha.py",
            ],
            "historical_artifacts": ["skills/jyotish-engine-modules/scripts/avastha_calculator.py"],
            "entrypoints": ["/api/deep_varga_avastha"],
            "reuse_decision": "do_not_duplicate_runtime",
            "next_action": "add_display_contract_and_source_oracle_packet",
            "claim_boundary": "Avastha is endpoint-visible, but formula variants and interpretive claim level still need source/oracle packet.",
        },
    ]
    return {
        "scope": "technique_promotion_audit_vimsopaka_avastha",
        "created_at": "2026-07-19",
        "truth_policy": "runtime_presence_not_oracle_closure",
        "production_tuning_allowed": False,
        "summary": {
            "items_checked": len(items),
            "formally_called_count": sum("formally_called" in item["current_call_status"] for item in items),
            "duplicate_runtime_needed": 0,
        },
        "items": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    audit = build_audit(args.root)
    text = json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
