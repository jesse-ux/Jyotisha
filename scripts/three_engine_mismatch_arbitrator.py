#!/usr/bin/env python3
"""Classify parity mismatches by evidence shape without choosing truth by vote."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


VARGA_SECTIONS = {"D2", "D4", "D9", "D10"}


def _category(section: str, differing: list[str]) -> tuple[str, str]:
    if section in VARGA_SECTIONS and differing == ["VedAstro"]:
        return (
            "endpoint_or_varga_semantics",
            "Confirm VedAstro endpoint returns the requested varga under the same ayanamsa/node/method contract.",
        )
    if section.startswith("ashtakavarga"):
        return (
            "ashtakavarga_table_or_contributor_variant",
            "Compare contributor tables, Lagna inclusion, shodhana state, and BAV/SAV row semantics.",
        )
    if section == "shadbala_components":
        return (
            "shadbala_formula_variant",
            "Compare component formula, units, local solar context, aspect model, and Chesta lineage before totals.",
        )
    if section == "shadbala_total":
        return (
            "derived_total_from_component_variants",
            "Do not arbitrate totals until all six component variants and Virupa/Rupa units are aligned.",
        )
    if differing == ["VedAstro"]:
        return (
            "vedastro_deployment_or_method_drift",
            "Replay against an identified VedAstro build and method; hosted anonymous output cannot decide truth.",
        )
    return (
        "cross_engine_numeric_or_schema_difference",
        "Normalize versions, schema paths, units, and formula variants; require an external worked example.",
    )


def arbitrate_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    categories: Counter[str] = Counter()
    for source in manifest.get("comparison_rows") or []:
        if source.get("status") != "mismatch":
            continue
        local = source.get("local_value")
        differing = sorted(
            engine for engine, value in (source.get("oracle_values") or {}).items() if value != local
        )
        category, closure = _category(str(source.get("section")), differing)
        categories[category] += 1
        rows.append({
            "section": source.get("section"),
            "field": source.get("field"),
            "local_value": local,
            "oracle_values": source.get("oracle_values"),
            "differing_engines": differing,
            "category": category,
            "closure_requirement": closure,
            "truth_status": "unresolved",
        })
    return {
        "scope": "three_engine_field_level_mismatch_arbitration",
        "manifest_path": str(manifest_path),
        "truth_policy": "no_majority_vote",
        "mismatch_count": len(rows),
        "classified_count": sum(categories.values()),
        "unclassified_count": len(rows) - sum(categories.values()),
        "category_counts": dict(sorted(categories.items())),
        "rows": rows,
        "status": "classified_unresolved" if rows else "no_mismatches",
    }


def render_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Three-engine mismatch arbitration",
        "",
        f"manifest: `{report['manifest_path']}`",
        f"status: `{report['status']}`",
        f"truth_policy: `{report['truth_policy']}`",
        "commercial_sync: `status_and_claim_boundary_only`",
        f"mismatch_count: `{report['mismatch_count']}`",
        f"classified_count: `{report['classified_count']}`",
        f"unclassified_count: `{report['unclassified_count']}`",
        "",
        "Do not copy raw research debt into commercial runtime. Commercial receives readiness, claim boundary, and user-safe status only.",
        "",
        "## Category counts",
        "",
        "| category | count |",
        "|---|---:|",
    ]
    for category, count in report["category_counts"].items():
        lines.append(f"| `{category}` | {count} |")
    lines.extend(["", "## Closure requirements", ""])
    seen: set[str] = set()
    for row in report["rows"]:
        category = row["category"]
        if category in seen:
            continue
        seen.add(category)
        lines.append(f"- `{category}`: {row['closure_requirement']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", default="references/oracle/three_engine_parity_replay_manifest.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()
    report = arbitrate_manifest(args.manifest)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown_report(report), encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
