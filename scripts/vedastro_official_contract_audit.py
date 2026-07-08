#!/usr/bin/env python3
"""Audit the route-level VedAstro official evidence contract.

This is a provenance/contract gate, not a live VedAstro oracle.  It protects
the user-facing reading layer from claiming official evidence when the official
raw response is blocked, partial, or only represented by local fallback data.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from typing import Any


REQUIRED_CONTRACT_FIELDS = [
    "source_priority_mode",
    "official_primary_evidence",
    "local_supplemental_evidence",
    "fallback_used",
    "blocked_items",
    "conflicts",
    "confidence_cap",
]

VALID_CONFIDENCE_CAPS = {"high", "medium", "low", "blocked"}


ROUTE_FIXTURES: list[dict[str, Any]] = [
    {
        "route": "relationship",
        "contract": {
            "source_priority_mode": "local_fallback_official_blocked",
            "official_primary_evidence": {
                "status": "blocked",
                "required": True,
                "raw_response_available": False,
                "reason": "official_snapshot_budget_exhausted",
            },
            "local_supplemental_evidence": {
                "status": "available",
                "sections": ["D1", "D9", "UL", "Vimshottari", "Narayana"],
            },
            "fallback_used": ["local_jyotish_core"],
            "blocked_items": ["vedastro_official_full_snapshot"],
            "conflicts": [],
            "confidence_cap": "low",
        },
    },
    {
        "route": "career",
        "contract": {
            "source_priority_mode": "vedastro_official_primary",
            "official_primary_evidence": {
                "status": "official_verified",
                "required": True,
                "raw_response_available": True,
                "sections": ["chart_core", "dasha", "strength"],
            },
            "local_supplemental_evidence": {
                "status": "available",
                "sections": ["D10", "A10", "Shadbala", "Ashtakavarga"],
            },
            "fallback_used": [],
            "blocked_items": [],
            "conflicts": [],
            "confidence_cap": "high",
        },
    },
    {
        "route": "wealth",
        "contract": {
            "source_priority_mode": "vedastro_official_primary_partial",
            "official_primary_evidence": {
                "status": "partial",
                "required": True,
                "raw_response_available": True,
                "sections": ["chart_core"],
            },
            "local_supplemental_evidence": {
                "status": "missing_required_sections",
                "missing_sections": ["D2", "D11", "AV"],
            },
            "fallback_used": ["local_chart_core"],
            "blocked_items": ["local_wealth_supplemental_bundle"],
            "conflicts": [],
            "confidence_cap": "low",
        },
    },
    {
        "route": "health",
        "contract": {
            "source_priority_mode": "local_fallback_official_blocked",
            "official_primary_evidence": {
                "status": "blocked",
                "required": True,
                "raw_response_available": False,
                "reason": "endpoint_unconfigured",
            },
            "local_supplemental_evidence": {
                "status": "missing_required_sections",
                "missing_sections": ["D30", "medical_boundary_review"],
            },
            "fallback_used": [],
            "blocked_items": ["vedastro_official_full_snapshot", "local_health_supplemental_bundle"],
            "conflicts": [],
            "confidence_cap": "blocked",
        },
    },
]


def _official_status(contract: dict[str, Any]) -> str:
    evidence = contract.get("official_primary_evidence")
    if not isinstance(evidence, dict):
        return "missing"
    return str(evidence.get("status") or "missing")


def _local_status(contract: dict[str, Any]) -> str:
    evidence = contract.get("local_supplemental_evidence")
    if not isinstance(evidence, dict):
        return "missing"
    return str(evidence.get("status") or "missing")


def expected_confidence_cap(contract: dict[str, Any]) -> str:
    """Return the strictest allowed confidence cap for this evidence state."""

    official = _official_status(contract)
    local = _local_status(contract)
    conflicts = contract.get("conflicts")
    fallback_used = contract.get("fallback_used")
    unresolved_conflicts = bool(conflicts)
    has_fallback = isinstance(fallback_used, list) and bool(fallback_used)

    if official in {"blocked", "missing"} and local != "available" and not has_fallback:
        return "blocked"
    if unresolved_conflicts:
        return "low"
    if official in {"partial", "blocked", "missing"}:
        return "low"
    if local != "available":
        return "low"
    return "high"


def validate_contract(route: str, contract: dict[str, Any]) -> dict[str, Any]:
    missing_fields = [field for field in REQUIRED_CONTRACT_FIELDS if field not in contract]
    confidence_cap = contract.get("confidence_cap")
    expected_cap = expected_confidence_cap(contract)
    errors: list[str] = []

    if missing_fields:
        errors.append(f"missing_required_fields:{','.join(missing_fields)}")
    if confidence_cap not in VALID_CONFIDENCE_CAPS:
        errors.append(f"invalid_confidence_cap:{confidence_cap}")
    if expected_cap == "blocked" and confidence_cap != "blocked":
        errors.append("blocked_state_must_use_blocked_confidence_cap")
    if expected_cap == "low" and confidence_cap not in {"low", "blocked"}:
        errors.append("partial_or_fallback_state_must_not_exceed_low")
    if expected_cap == "high" and confidence_cap not in {"high", "medium", "low", "blocked"}:
        errors.append("verified_state_has_invalid_confidence_cap")

    return {
        "route": route,
        "valid": not errors,
        "missing_fields": missing_fields,
        "official_status": _official_status(contract),
        "local_status": _local_status(contract),
        "fallback_count": len(contract.get("fallback_used") or []),
        "blocked_count": len(contract.get("blocked_items") or []),
        "conflict_count": len(contract.get("conflicts") or []),
        "confidence_cap": confidence_cap,
        "expected_confidence_cap": expected_cap,
        "errors": errors,
    }


def build_audit_report(routes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    fixtures = deepcopy(routes if routes is not None else ROUTE_FIXTURES)
    route_reports = [
        validate_contract(str(item.get("route") or "unknown"), item.get("contract") or {})
        for item in fixtures
    ]
    invalid_routes = [item for item in route_reports if not item["valid"]]

    return {
        "scope": "vedastro_official_evidence_contract_audit",
        "schema_version": 1,
        "required_fields": REQUIRED_CONTRACT_FIELDS,
        "route_count": len(route_reports),
        "routes": route_reports,
        "summary": {
            "valid_routes": len(route_reports) - len(invalid_routes),
            "invalid_routes": len(invalid_routes),
            "confidence_cap_policy": "enforced",
        },
        "boundary": (
            "Contract audit only; this does not prove VedAstro official raw "
            "response availability, endpoint health, API key validity, or quota."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON. Kept for CLI symmetry.")
    args = parser.parse_args()
    _ = args
    print(json.dumps(build_audit_report(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
