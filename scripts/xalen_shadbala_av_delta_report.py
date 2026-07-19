#!/usr/bin/env python3
"""Group Xalen Shadbala/AV deltas by component family.

Reads archived comparison inputs. Does not recompute astrology formulas.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from scripts.xalen_oracle_comparison import compare


SECTION_CATEGORY = {
    "shadbala_components": "shadbala_formula_variant",
    "shadbala_total": "derived_total_from_component_variants",
    "ashtakavarga_bav": "ashtakavarga_table_or_contributor_variant",
    "ashtakavarga_sav": "ashtakavarga_table_or_contributor_variant",
}


def _registry_by_category(path: Path) -> dict[str, dict]:
    registry = json.loads(path.read_text(encoding="utf-8"))["registry"]
    return {row["category"]: row for row in registry}


def _component_key(row: dict) -> str:
    if row["section"] == "shadbala_components":
        return row["field"].split(".", 1)[1]
    if row["section"] == "shadbala_total":
        return "total_rupa"
    return row["section"]


def build_report(manifest_path: Path, xalen_path: Path, registry_path: Path) -> dict:
    comparison = compare(manifest_path, xalen_path)
    registry = _registry_by_category(registry_path)
    groups: dict[tuple[str, str], dict] = {}
    status_counts = Counter()
    section_counts = Counter()

    for row in comparison["rows"]:
        category = SECTION_CATEGORY.get(row["section"])
        if not category:
            continue
        key = (category, _component_key(row))
        source = registry[category]
        group = groups.setdefault(
            key,
            {
                "category": category,
                "component": key[1],
                "allowed_claim": source["allowed_claim"],
                "unit_contract": source["unit_contract"],
                "required_evidence": source["next_evidence_required"],
                "closure_status": "open",
                "rows": [],
                "status_counts": defaultdict(int),
            },
        )
        group["rows"].append(row)
        group["status_counts"][row["status"]] += 1
        status_counts[(row["section"], row["status"])] += 1
        section_counts[row["section"]] += 1

    component_groups = []
    for group in groups.values():
        group["status_counts"] = dict(sorted(group["status_counts"].items()))
        component_groups.append(group)
    component_groups.sort(key=lambda item: (item["category"], item["component"]))

    return {
        "scope": "xalen_shadbala_av_component_delta_report",
        "source_commit": comparison["source_commit"],
        "license": comparison["license"],
        "truth_policy": "method_variant_not_majority_vote",
        "production_tuning_allowed": False,
        "boundary": "Xalen deltas identify formula/table/unit evidence needs; they are not majority-vote truth.",
        "source_artifacts": {
            "manifest": str(manifest_path),
            "xalen_raw": str(xalen_path),
            "provenance_registry": str(registry_path),
        },
        "summary": {
            "shadbala_component_rows": section_counts["shadbala_components"],
            "shadbala_component_mismatch_count": status_counts[("shadbala_components", "mismatch")],
            "shadbala_total_rows": section_counts["shadbala_total"],
            "shadbala_total_mismatch_count": status_counts[("shadbala_total", "mismatch")],
            "ashtakavarga_rows": section_counts["ashtakavarga_bav"] + section_counts["ashtakavarga_sav"],
            "ashtakavarga_mismatch_count": status_counts[("ashtakavarga_bav", "mismatch")]
            + status_counts[("ashtakavarga_sav", "mismatch")],
            "component_group_count": len(component_groups),
        },
        "component_groups": component_groups,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("references/oracle/three_engine_parity_replay_manifest.json"),
    )
    parser.add_argument(
        "--xalen",
        type=Path,
        default=Path("references/oracle/artifacts/xalen_steve_jobs_high_rigor_raw.json"),
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("references/oracle/shadbala_av_component_provenance_registry_2026_07_19.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report(args.manifest, args.xalen, args.registry)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
