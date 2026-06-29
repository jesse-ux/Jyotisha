#!/usr/bin/env python3
"""Summarize the technique registry as a backend capability evidence pool."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "references" / "technique_registry.json"


def load_registry(path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_capability_evidence_pool_summary(registry: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = registry if registry is not None else load_registry()
    techniques = registry.get("techniques") if isinstance(registry, dict) else {}
    if not isinstance(techniques, dict):
        techniques = {}

    entry_type_counts = Counter()
    evidence_role_counts = Counter()
    visibility_counts = Counter()
    prediction_counts = Counter()
    primary_entries: list[str] = []
    audit_only_entries: list[str] = []
    alias_entries: list[str] = []

    for tech_id, tech in techniques.items():
        if not isinstance(tech, dict):
            continue
        entry_type = tech.get("entry_type") or "supporting_indicator"
        evidence_role = tech.get("evidence_role") or "secondary"
        visibility = tech.get("user_visibility") or "expert_audit"
        verification = tech.get("verification_level") if isinstance(tech.get("verification_level"), dict) else {}
        prediction = verification.get("prediction") or "not_claimed"

        entry_type_counts[entry_type] += 1
        evidence_role_counts[evidence_role] += 1
        visibility_counts[visibility] += 1
        prediction_counts[prediction] += 1

        if evidence_role == "primary":
            primary_entries.append(tech_id)
        elif evidence_role == "audit_only":
            audit_only_entries.append(tech_id)
        elif evidence_role == "alias":
            alias_entries.append(tech_id)

    return {
        "scope": "backend_capability_evidence_pool",
        "total_entries": len(techniques),
        "public_label": registry.get("public_label", f"{len(techniques)} capability entries"),
        "ordinary_user_policy": registry.get(
            "ordinary_user_policy",
            "Users see topic-level conclusions; capability entries are routed behind the scenes.",
        ),
        "entry_type_counts": dict(sorted(entry_type_counts.items())),
        "evidence_role_counts": dict(sorted(evidence_role_counts.items())),
        "user_visibility_counts": dict(sorted(visibility_counts.items())),
        "prediction_verification_counts": dict(sorted(prediction_counts.items())),
        "primary_entries": sorted(primary_entries),
        "audit_only_entries": sorted(audit_only_entries),
        "alias_entries": sorted(alias_entries),
        "conclusion_policy": {
            "primary_chain_required": True,
            "all_89_entries_must_not_be_flattened_into_conclusions": True,
            "supporting_entries_can_only_raise_or_lower_confidence": True,
            "audit_only_entries_cannot_affect_astrological_conclusions": True,
            "conflicts_must_downgrade_confidence": True,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args(argv)

    summary = build_capability_evidence_pool_summary(load_registry(Path(args.registry)))
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
