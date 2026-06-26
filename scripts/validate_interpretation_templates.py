#!/usr/bin/env python3
"""Validate high-granularity Jyotish interpretation templates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "references" / "interpretation_template_registry.json"

REQUIRED_TEMPLATE_FIELDS = [
    "title",
    "status",
    "authority_level",
    "domain",
    "source_refs",
    "trigger_patterns",
    "required_cross_checks",
    "confidence_ceiling",
    "forbidden_claims",
    "safe_output_patterns",
]


def _resolve(path: str | None) -> Path:
    if not path:
        return DEFAULT_REGISTRY
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_registry(path: Path) -> dict[str, Any]:
    problems: list[str] = []
    registry = _load_json(path)
    if registry.get("scope") != "jyotish_interpretation_template_registry":
        problems.append("invalid_scope")
    templates = registry.get("templates")
    if not isinstance(templates, dict) or not templates:
        problems.append("missing_templates")
        templates = {}

    for template_id, template in templates.items():
        if not isinstance(template, dict):
            problems.append(f"{template_id}:not_object")
            continue
        for field in REQUIRED_TEMPLATE_FIELDS:
            value = template.get(field)
            if value in (None, "", [], {}):
                problems.append(f"{template_id}:missing_{field}")
        for ref in template.get("source_refs", []):
            ref_path = ROOT / ref
            if not ref_path.exists():
                problems.append(f"{template_id}:missing_source_ref:{ref}")
        if not template.get("forbidden_claims"):
            problems.append(f"{template_id}:missing_forbidden_claims")
        if "alone" not in " ".join(template.get("forbidden_claims", [])).lower():
            problems.append(f"{template_id}:forbidden_claims_should_block_single-factor_use")

    return {
        "scope": "jyotish_interpretation_template_validation",
        "schema_version": 1,
        "registry": str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path),
        "valid": not problems,
        "summary": {
            "template_count": len(templates),
            "template_ids": sorted(templates.keys()),
            "problem_count": len(problems),
        },
        "problems": problems,
        "boundary": (
            "These templates are interpretation guardrails. They do not replace chart calculation, "
            "Dasha/transit convergence, external oracle validation or the strict workflow router."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Jyotish Interpretation Template Validation",
        "",
        f"- valid: `{str(report['valid']).lower()}`",
        f"- template_count: `{report['summary']['template_count']}`",
        f"- problem_count: `{report['summary']['problem_count']}`",
        "",
        "## Templates",
        "",
    ]
    lines.extend(f"- `{template_id}`" for template_id in report["summary"]["template_ids"])
    lines.extend(["", "## Boundary", "", report["boundary"], ""])
    if report["problems"]:
        lines.extend(["## Problems", ""])
        lines.extend(f"- {problem}" for problem in report["problems"])
        lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Jyotish interpretation template registry")
    parser.add_argument("--registry", help="Path to interpretation_template_registry.json")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = validate_registry(_resolve(args.registry))
    if args.format == "markdown":
        print(render_markdown(report))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
