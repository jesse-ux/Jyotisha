#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Technique capability registry validator and audit generator.

This script deliberately uses only Python stdlib. Open-source research suggested
Yamale/jsonschema-style validation for registries, but this skill avoids adding
runtime dependencies beyond pyswisseph.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_REGISTRY = os.path.join(ROOT_DIR, "references", "technique_registry.json")

ALLOWED_STATUS = {
    "covered",
    "partial",
    "knowledge-only",
    "workflow-only",
    "not-integrated",
    "missing",
}
REQUIRED_TECHNIQUE_FIELDS = {
    "name": str,
    "domains": list,
    "status": str,
    "knowledge_refs": list,
    "commands": list,
    "output_paths": list,
    "audit_label": str,
    "missing_impact": str,
}


def load_registry(path: str = DEFAULT_REGISTRY) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _path_exists_relative(path: str) -> bool:
    if path.startswith("scripts/") and " " in path:
        path = path.split()[0]
    return os.path.exists(os.path.join(ROOT_DIR, path))


def validate_registry(registry: Dict[str, Any]) -> Dict[str, Any]:
    problems: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    techniques = registry.get("techniques")
    if not isinstance(techniques, dict) or not techniques:
        problems.append({"level": "error", "path": "techniques", "message": "techniques must be a non-empty object"})
        techniques = {}

    for tech_id, tech in techniques.items():
        if not isinstance(tech, dict):
            problems.append({"level": "error", "path": tech_id, "message": "technique entry must be an object"})
            continue
        for field, expected_type in REQUIRED_TECHNIQUE_FIELDS.items():
            if field not in tech:
                problems.append({"level": "error", "path": f"techniques.{tech_id}.{field}", "message": "required field missing"})
                continue
            if not isinstance(tech[field], expected_type):
                problems.append({"level": "error", "path": f"techniques.{tech_id}.{field}", "message": f"must be {expected_type.__name__}"})
        status = tech.get("status")
        if status not in ALLOWED_STATUS:
            problems.append({"level": "error", "path": f"techniques.{tech_id}.status", "message": f"invalid status {status!r}"})
        if status == "covered" and not tech.get("output_paths"):
            problems.append({"level": "error", "path": f"techniques.{tech_id}.output_paths", "message": "covered techniques must expose output_paths"})
        if status == "partial" and not tech.get("limitation"):
            warnings.append({"level": "warning", "path": f"techniques.{tech_id}.limitation", "message": "partial techniques should explain limitation"})
        for ref in tech.get("knowledge_refs", []):
            if isinstance(ref, str) and not _path_exists_relative(ref):
                warnings.append({"level": "warning", "path": f"techniques.{tech_id}.knowledge_refs", "message": f"reference not found: {ref}"})

    routes = registry.get("routes", {})
    if not isinstance(routes, dict):
        problems.append({"level": "error", "path": "routes", "message": "routes must be an object"})
        routes = {}
    for route_id, route in routes.items():
        if not isinstance(route, dict):
            problems.append({"level": "error", "path": f"routes.{route_id}", "message": "route entry must be an object"})
            continue
        required = route.get("required_techniques", [])
        optional = route.get("optional_techniques", [])
        if not isinstance(required, list):
            problems.append({"level": "error", "path": f"routes.{route_id}.required_techniques", "message": "must be a list"})
            required = []
        if not isinstance(optional, list):
            problems.append({"level": "error", "path": f"routes.{route_id}.optional_techniques", "message": "must be a list"})
            optional = []
        for tech_id in required + optional:
            if tech_id not in techniques:
                problems.append({"level": "error", "path": f"routes.{route_id}", "message": f"unknown technique id: {tech_id}"})

    status_counts: Dict[str, int] = {s: 0 for s in sorted(ALLOWED_STATUS)}
    domain_counts: Dict[str, int] = {}
    for tech in techniques.values():
        status = tech.get("status")
        if status in status_counts:
            status_counts[status] += 1
        for domain in tech.get("domains", []):
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

    return {
        "valid": len(problems) == 0,
        "problem_count": len(problems),
        "warning_count": len(warnings),
        "status_counts": status_counts,
        "domain_counts": dict(sorted(domain_counts.items())),
        "problems": problems,
        "warnings": warnings,
        "routes": sorted(routes.keys()),
        "technique_count": len(techniques),
    }


def build_audit_table(registry: Dict[str, Any], route_id: str | None = None) -> Dict[str, Any]:
    techniques = registry.get("techniques", {})
    route = registry.get("routes", {}).get(route_id, {}) if route_id else {}
    if route_id and not route:
        raise KeyError(f"Unknown route: {route_id}")

    if route:
        ordered_ids = list(dict.fromkeys(route.get("required_techniques", []) + route.get("optional_techniques", [])))
    else:
        ordered_ids = sorted(techniques.keys())

    rows = []
    for tech_id in ordered_ids:
        tech = techniques[tech_id]
        rows.append({
            "technique_id": tech_id,
            "audit_label": tech.get("audit_label"),
            "status": tech.get("status"),
            "commands": tech.get("commands", []),
            "output_paths": tech.get("output_paths", []),
            "missing_impact": tech.get("missing_impact"),
            "limitation": tech.get("limitation"),
        })
    return {"route": route_id or "all", "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Jyotish technique registry and emit audit data")
    parser.add_argument("--registry", default=DEFAULT_REGISTRY, help="Path to technique_registry.json")
    parser.add_argument("--route", default=None, help="Optional route id for audit table")
    parser.add_argument("--mode", choices=["validate", "table"], default="validate")
    args = parser.parse_args()

    try:
        registry = load_registry(args.registry)
        if args.mode == "validate":
            result = validate_registry(registry)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["valid"] else 1
        result = build_audit_table(registry, args.route)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
