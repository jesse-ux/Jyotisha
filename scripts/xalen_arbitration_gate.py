#!/usr/bin/env python3
"""Gate Xalen Shadbala/Ashtakavarga variants against external arbitration needs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def build_report(attribution_path: Path, public_batch_path: Path, ephemeris_path: Path) -> dict:
    attribution = json.loads(attribution_path.read_text(encoding="utf-8"))
    public_batch = json.loads(public_batch_path.read_text(encoding="utf-8"))
    ephemeris = json.loads(ephemeris_path.read_text(encoding="utf-8"))
    unresolved = [
        row for row in attribution["rows"]
        if row.get("truth_status") in {
            "method_variant_unresolved",
            "requires_external_worked_example_per_contributor",
            "defer_until_components_arbitrated",
        }
    ]
    enough_cases = public_batch.get("case_count", 0) >= 5
    independent_ephemeris_ok = (
        ephemeris.get("maximum_absolute_longitude_delta_deg", 999) <= 0.01
        and ephemeris.get("varga_difference_count") == 0
    )
    return {
        "scope": "xalen_formula_arbitration_gate",
        "public_case_count": public_batch.get("case_count", 0),
        "multi_case_replay_status": "ready" if enough_cases else "partial",
        "independent_ephemeris_status": "ready" if independent_ephemeris_ok else "partial",
        "unresolved_variant_count": len(unresolved),
        "truth_status": "blocked" if unresolved else "ready",
        "promotion_allowed": not unresolved and enough_cases and independent_ephemeris_ok,
        "required_next_evidence": [
            "published component-level Shadbala worked examples for every disputed component",
            "published BAV contributor-table example with per-sign rows",
            "formula-source citation for each Xalen/local method branch",
        ],
        "boundary": (
            "Multi-case replay and independent ephemeris reduce implementation risk; "
            "they do not arbitrate method variants without external numeric worked examples."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--attribution",
        type=Path,
        default=Path("references/oracle/xalen_formula_unit_attribution_2026_07_17.json"),
    )
    parser.add_argument(
        "--public-batch",
        type=Path,
        default=Path("references/oracle/xalen_public_case_batch_2026_07_17.json"),
    )
    parser.add_argument(
        "--ephemeris",
        type=Path,
        default=Path("references/oracle/xalen_ephemeris_mode_comparison_2026_07_17.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report(args.attribution, args.public_batch, args.ephemeris)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
