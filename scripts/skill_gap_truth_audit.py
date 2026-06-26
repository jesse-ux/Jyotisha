#!/usr/bin/env python3
"""Audit the current Jyotish skill truth boundary."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
DEFAULT_REGISTRY = ROOT / "references" / "skill_gap_truth_registry.json"


def _resolve(path: str | None) -> Path:
    if not path:
        return DEFAULT_REGISTRY
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _run_json(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return json.loads(completed.stdout)


def _validate_registry(registry: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if registry.get("scope") != "jyotish_skill_gap_truth_registry":
        problems.append("invalid_scope")
    hard_fronts = registry.get("hard_fronts")
    if not isinstance(hard_fronts, dict) or not hard_fronts:
        problems.append("missing_hard_fronts")
        hard_fronts = {}
    for front_id, front in hard_fronts.items():
        for field in [
            "title",
            "priority",
            "status",
            "current_truth",
            "completion_standard",
            "forbidden_claims",
            "next_actions",
        ]:
            if front.get(field) in (None, "", [], {}):
                problems.append(f"{front_id}:missing_{field}")
        if "alone" not in " ".join(front.get("forbidden_claims", [])).lower():
            problems.append(f"{front_id}:forbidden_claims_should_block_single_factor_or_overclaim")
    corrections = registry.get("past_case_analysis_corrections")
    if not isinstance(corrections, list) or not corrections:
        problems.append("missing_past_case_analysis_corrections")
        corrections = []
    for correction in corrections:
        for field in ["id", "wrong_pattern", "corrected_truth", "source_ref"]:
            if correction.get(field) in (None, "", [], {}):
                problems.append(f"correction:missing_{field}")
        source_ref = correction.get("source_ref")
        if source_ref and not (ROOT / source_ref).exists():
            problems.append(f"correction:missing_source_ref:{source_ref}")
    return problems


def build_report(registry_path: Path) -> dict[str, Any]:
    registry = _load_json(registry_path)
    problems = _validate_registry(registry)
    capability = _run_json([PYTHON, "scripts/audit_capabilities.py", "--mode", "validate"])
    oracle = _run_json([
        PYTHON,
        "scripts/oracle_closure_master_dashboard.py",
        "--format",
        "json",
    ])
    hard_fronts = registry.get("hard_fronts", {})
    remaining = [
        {
            "id": front_id,
            "title": front["title"],
            "priority": front["priority"],
            "status": front["status"],
            "current_truth": front["current_truth"],
            "completion_standard": front["completion_standard"],
            "next_actions": front["next_actions"],
        }
        for front_id, front in hard_fronts.items()
    ]
    priority_rank = {"P0": 0, "P1": 1, "P2": 2}
    remaining.sort(key=lambda item: (priority_rank.get(item["priority"], 99), item["id"]))
    claim_rules = registry.get("public_claim_rules", {})
    can_claim_global_oracle = oracle["summary"]["can_claim_global_oracle_closure"]
    can_claim_global_first = bool(
        claim_rules.get("can_claim_global_first")
        and can_claim_global_oracle
        and capability.get("valid")
    )
    can_claim_all_skills_complete = bool(
        claim_rules.get("can_claim_all_skills_complete")
        and can_claim_global_oracle
        and capability.get("status_counts", {}).get("covered", 0) == 0
    )
    can_claim_perfect_accuracy = bool(
        claim_rules.get("can_claim_perfect_accuracy")
        and can_claim_global_oracle
        and oracle["summary"].get("production_tuning_allowed")
    )
    corrections = registry.get("past_case_analysis_corrections", [])
    return {
        "scope": "jyotish_skill_gap_truth_audit",
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "registry": str(registry_path.relative_to(ROOT) if registry_path.is_relative_to(ROOT) else registry_path),
        "valid": not problems,
        "summary": {
            "technique_count": capability["technique_count"],
            "capability_valid": capability["valid"],
            "capability_problem_count": capability["problem_count"],
            "status_counts": capability["status_counts"],
            "hard_front_count": len(hard_fronts),
            "past_correction_count": len(corrections),
            "registry_problem_count": len(problems),
        },
        "public_claim": {
            "can_claim_global_first": can_claim_global_first,
            "can_claim_all_skills_complete": can_claim_all_skills_complete,
            "can_claim_perfect_accuracy": can_claim_perfect_accuracy,
            "reason": claim_rules.get("reason", ""),
        },
        "oracle_closure": {
            "summary": oracle["summary"],
            "next_action_order": oracle.get("next_action_order", []),
        },
        "remaining_hard_fronts": remaining,
        "past_correction_ids": [item["id"] for item in corrections],
        "past_case_analysis_corrections": corrections,
        "must_not_overclaim": registry.get("must_not_overclaim", []),
        "problems": problems,
        "boundary": (
            "This audit answers the skill-level truth question. A covered technique is not the same as a "
            "complete externally closed technique; single-factor case readings must remain confidence-capped."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    claim = report["public_claim"]
    summary = report["summary"]
    oracle = report["oracle_closure"]["summary"]
    lines = [
        "# Jyotish Skill Gap Truth Audit",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Public Claim Boundary",
        "",
        f"- can_claim_global_first: `{str(claim['can_claim_global_first']).lower()}`",
        f"- can_claim_all_skills_complete: `{str(claim['can_claim_all_skills_complete']).lower()}`",
        f"- can_claim_perfect_accuracy: `{str(claim['can_claim_perfect_accuracy']).lower()}`",
        f"- reason: {claim['reason']}",
        "",
        "## Capability Snapshot",
        "",
        f"- technique_count: `{summary['technique_count']}`",
        f"- capability_valid: `{str(summary['capability_valid']).lower()}`",
        f"- hard_front_count: `{summary['hard_front_count']}`",
        f"- past_correction_count: `{summary['past_correction_count']}`",
        "",
        "## External Oracle Closure",
        "",
        f"- total_tasks: `{oracle['total_tasks']}`",
        f"- external_verified_tasks: `{oracle['external_verified_tasks']}`",
        f"- open_tasks: `{oracle['open_tasks']}`",
        f"- can_claim_global_oracle_closure: `{str(oracle['can_claim_global_oracle_closure']).lower()}`",
        "",
        "## Remaining Hard Fronts",
        "",
    ]
    for front in report["remaining_hard_fronts"]:
        lines.extend(
            [
                f"### {front['title']}",
                "",
                f"- id: `{front['id']}`",
                f"- priority: `{front['priority']}`",
                f"- status: `{front['status']}`",
                f"- current_truth: {front['current_truth']}",
                "",
            ]
        )
    lines.extend(["## Past Corrections", ""])
    for correction in report["past_case_analysis_corrections"]:
        lines.extend(
            [
                f"- `{correction['id']}`: {correction['corrected_truth']}",
            ]
        )
    lines.extend(["", "## Must Not Overclaim", ""])
    lines.extend(f"- {item}" for item in report["must_not_overclaim"])
    lines.extend(["", "## Boundary", "", report["boundary"], ""])
    if report["problems"]:
        lines.extend(["## Problems", ""])
        lines.extend(f"- {problem}" for problem in report["problems"])
        lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Jyotish skill gap truth boundary")
    parser.add_argument("--registry", help="Path to skill_gap_truth_registry.json")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", help="Optional output path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(_resolve(args.registry))
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else render_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
