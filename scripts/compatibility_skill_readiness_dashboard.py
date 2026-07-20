#!/usr/bin/env python3
"""Build a bounded compatibility/synastry skill readiness dashboard.

This is governance glue, not a truth engine.  It records which relationship
layers are callable, which are registry-only, and which must stay blocked.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "references" / "oracle" / "compatibility_skill_readiness_dashboard_2026_07_20.json"


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def layer(
    layer_id: str,
    name: str,
    runtime_path: str | None,
    runtime_status: str,
    skill_status: str,
    api_ui_status: str,
    external_oracle_status: str,
    commercial_sync_status: str,
    claim_boundary: str,
    evidence: list[str] | None = None,
) -> dict:
    paths = list(evidence or [])
    if runtime_path:
        paths.insert(0, runtime_path)
    return {
        "layer_id": layer_id,
        "name": name,
        "runtime_status": runtime_status,
        "runtime_path": runtime_path,
        "runtime_path_exists": exists(runtime_path) if runtime_path else False,
        "skill_status": skill_status,
        "api_ui_status": api_ui_status,
        "external_oracle_status": external_oracle_status,
        "commercial_sync_status": commercial_sync_status,
        "evidence_paths": paths,
        "claim_boundary": claim_boundary,
    }


def build() -> dict:
    layers = [
        layer(
            "ashtakoota_guna_milan",
            "Ashtakoota / Guna Milan",
            "scripts/ashtakoot.py",
            "available",
            "callable_basic",
            "surface_audit_needed",
            "partial",
            "basic_safe_with_boundary",
            "36-point compatibility can be exposed as one factor only; not deterministic marriage outcome.",
            ["references/oracle/ashtakoot_oracle_cases.json", "scripts/synastry.py"],
        ),
        layer(
            "mangal_dosha",
            "Mangal / Kuja Dosha matching",
            "scripts/ashtakoot.py",
            "available",
            "callable_basic",
            "surface_audit_needed",
            "partial",
            "basic_safe_with_boundary",
            "Use as risk flag and cancellation check; never as standalone rejection verdict.",
        ),
        layer(
            "d9_navamsa_relationship",
            "D9 Navamsa relationship layer",
            "scripts/relationship_analysis.py",
            "available",
            "callable_context",
            "surface_audit_needed",
            "partial",
            "safe_as_context",
            "D9 can support relationship analysis; timing/outcome claims still require Dasha, transits, and external calibration.",
            ["references/navamsa-marriage-deep-analysis.md"],
        ),
        layer(
            "darakaraka",
            "Darakaraka spouse significator",
            "scripts/darakaraka_reader.py",
            "available",
            "callable_context",
            "surface_audit_needed",
            "source_reference_only",
            "safe_as_context",
            "May describe spouse/relationship themes; not a compatibility score or event proof.",
            ["references/darakaraka-complete-guide.md"],
        ),
        layer(
            "upapada_lagna",
            "Upapada Lagna marriage image",
            "scripts/jaimini.py",
            "available_as_chart_field",
            "callable_context",
            "surface_audit_needed",
            "source_reference_only",
            "safe_as_context",
            "UL is a relationship image layer; must not replace full chart, D9, Dasha, or event evidence.",
            ["references/data-bridge-mapping.md", "references/jaimini-complete-system.md"],
        ),
        layer(
            "relationship_combinations",
            "Relationship rule-family combinations",
            None,
            "registry_only",
            "contract_only",
            "no_runtime_surface",
            "missing",
            "research_only",
            "Indexed rule families still need source packets, deduplication, tests, and claim gates before runtime use.",
            ["references/oracle/relationship_combinations_rule_family_registry_2026_07_19.json"],
        ),
        layer(
            "relationship_ashtakavarga_overlay",
            "Relationship Ashtakavarga overlay",
            None,
            "missing_runtime",
            "not_invoked",
            "no_runtime_surface",
            "missing",
            "blocked_until_oracle",
            "Do not expose relationship AV overlay until rules, examples, and field-level oracle packets exist.",
            ["references/oracle/ashtakavarga_advanced_usage_gap_registry_2026_07_19.json"],
        ),
        layer(
            "planet_lagna_kuta",
            "Planet/Lagna Kuta variants",
            None,
            "registry_only",
            "not_invoked",
            "no_runtime_surface",
            "missing",
            "blocked_until_oracle",
            "Do not claim full top-tier compatibility until Planet/Lagna Kuta variants and worked examples are validated.",
            ["references/oracle/compatibility_full_system_gap_registry_2026_07_19.json"],
        ),
        layer(
            "western_composite_davidson_boundary",
            "Western composite / Davidson boundary",
            None,
            "out_of_scope",
            "not_invoked",
            "no_vedic_surface",
            "not_applicable_vedic_core",
            "out_of_scope_for_vedic_core",
            "Keep out of Vedic commercial runtime unless explicitly scoped as cross-system research.",
        ),
    ]
    return {
        "scope": "compatibility_skill_readiness_dashboard",
        "created_at": "2026-07-20",
        "status": "dashboard_v1",
        "claim_status": "partial",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "summary": {
            "layer_count": len(layers),
            "runtime_available_count": sum(1 for x in layers if x["runtime_status"] in {"available", "available_as_chart_field"}),
            "blocked_or_registry_only_count": sum(1 for x in layers if x["commercial_sync_status"] in {"research_only", "blocked_until_oracle", "out_of_scope_for_vedic_core"}),
            "oracle_ready_count": 0,
        },
        "skill_use_policy": {
            "allowed": "Expose basic compatibility factors and relationship context with explicit low/partial evidence boundaries.",
            "forbidden": "Do not present any layer as deterministic marriage success, divorce prediction, exact relationship timing, or complete synastry truth.",
        },
        "layers": layers,
    }


def main() -> None:
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
