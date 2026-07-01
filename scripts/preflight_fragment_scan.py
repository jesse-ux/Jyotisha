#!/usr/bin/env python3
"""Preflight scan for fragment discipline, redundancy, and real-capability boundaries.

This script is intentionally stdlib-only and reuses existing project audits.
It exists to enforce a "scan before work" rule for multi-window development,
so high-value drafts, mirrors, and external-work-brain fragments do not get
forgotten or confused with source truth.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import oracle_boundary_audit  # noqa: E402


LOCAL_DRAFTS_DIR = ROOT / "docs" / "research" / "local_drafts" / "2026-06"
EXTERNAL_WORK_BRAIN_DIR = Path("/Users/wuyongnaren/.gemini/antigravity-ide/brain")
DISTRIBUTION_MIRROR_DIR = Path("/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology")
ORACLE_FILE = ROOT / "references" / "oracle" / "dasha_shadbala_oracle_cases.json"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _run_json_script(*args: str) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr or completed.stdout or f"Failed: {' '.join(args)}")
    return json.loads(completed.stdout)


def _list_files(base: Path, patterns: tuple[str, ...]) -> list[str]:
    if not base.exists():
        return []
    items: list[str] = []
    for pattern in patterns:
        for path in base.rglob(pattern):
            if path.is_file():
                items.append(str(path))
    return sorted(set(items))


def _summarize_local_drafts() -> list[dict[str, Any]]:
    if not LOCAL_DRAFTS_DIR.exists():
        return []
    preferred_tokens = (
        "reuse_audit",
        "three_fronts",
        "tajika",
        "shadbala",
        "dasha",
        "yogi",
        "fragment",
        "truth",
        "benchmark",
    )
    rows: list[dict[str, Any]] = []
    for path in sorted(LOCAL_DRAFTS_DIR.glob("*.md")):
        name = path.name
        if not any(token in name for token in preferred_tokens):
            continue
        rows.append(
            {
                "category": "repo_local_draft",
                "path": str(path),
                "reason": "High-value draft not promoted into repo truth yet.",
            }
        )
    return rows[:12]


def _summarize_external_work_brain() -> list[dict[str, Any]]:
    if not EXTERNAL_WORK_BRAIN_DIR.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in _list_files(
        EXTERNAL_WORK_BRAIN_DIR,
        ("*.md", "*.py"),
    ):
        name = os.path.basename(path).lower()
        if not any(token in name for token in ("vedastro", "audit", "skill", "workflow", "oracle")):
            continue
        rows.append(
            {
                "category": "external_work_brain",
                "path": path,
                "reason": "Recovery-only work-brain artifact; re-anchor before reuse.",
            }
        )
    return rows[:12]


def _redundant_or_mirror_rows(fragment_audit: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {
            "category": "distribution_mirror",
            "path": str(DISTRIBUTION_MIRROR_DIR),
            "reason": "Historical skill mirror; do not reverse-sync over main repo truth.",
        }
    ]
    for rel in fragment_audit.get("workspace_residue", {}).get("untracked_files", [])[:12]:
        rows.append(
            {
                "category": "workspace_residue",
                "path": str(ROOT / rel),
                "reason": "Untracked residue or generated artifact; review before treating as source truth.",
            }
        )
    return rows


def _real_capability_risks(oracle_boundary: dict[str, Any]) -> list[dict[str, Any]]:
    summary = oracle_boundary.get("summary", {})
    risks = [
        {
            "id": "external_oracle_not_closed",
            "severity": "high",
            "reason": "External oracle boundary remains open; production tuning is still blocked.",
            "evidence": {
                "production_tuning_recommended": summary.get("production_tuning_recommended"),
                "open_items": summary.get("open_items", []),
            },
        },
        {
            "id": "historical_event_accuracy_not_proven",
            "severity": "high",
            "reason": "Engineering surfaces are covered, but historical life-event accuracy is not yet proven by external oracle closure.",
            "evidence": {
                "routes_present": ["career_timing_strict", "event_verification_strict", "full_reading_strict"],
                "needs_real_backtest": True,
            },
        },
        {
            "id": "official_vs_local_boundary",
            "severity": "medium",
            "reason": "VedAstro official ingestion exists, but some real-capability claims still depend on local fallback and incomplete external comparison packs.",
            "evidence": {
                "longitude_cases": summary.get("longitude_cases", 0),
                "dasha_cases": summary.get("dasha_cases", 0),
                "shadbala_cases": summary.get("shadbala_cases", 0),
            },
        },
    ]
    return risks


def _cleanup_priorities(fragment_audit: dict[str, Any], high_value_unpromoted: list[dict[str, Any]]) -> list[dict[str, Any]]:
    workspace_residue = fragment_audit.get("workspace_residue", {}).get("untracked_files", [])
    priorities = [
        {
            "id": "triage_workspace_residue",
            "severity": "high" if workspace_residue else "medium",
            "why": "Untracked residue can hide generated truth, stale artifacts, or partial experiments across windows.",
            "evidence": {
                "untracked_count": len(workspace_residue),
                "sample_paths": workspace_residue[:5],
            },
        },
        {
            "id": "promote_or_archive_high_value_drafts",
            "severity": "medium",
            "why": "High-value draft audits should either be promoted into repo truth or explicitly archived to reduce rediscovery cost.",
            "evidence": {
                "draft_count": len(high_value_unpromoted),
                "sample_paths": [item["path"] for item in high_value_unpromoted[:5]],
            },
        },
    ]
    return priorities


def build_report() -> dict[str, Any]:
    fragment_audit = _run_json_script("scripts/audit_fragments.py", "--strict")
    capability_audit = _run_json_script(
        "scripts/jyotish_engine.py",
        "audit-capabilities",
        "--mode",
        "validate",
    )
    oracle = json.loads(_read_text(ORACLE_FILE))
    oracle_boundary = oracle_boundary_audit.build_report(oracle)

    high_value_unpromoted = _summarize_local_drafts() + _summarize_external_work_brain()
    redundant_or_mirror = _redundant_or_mirror_rows(fragment_audit)
    real_capability_risks = _real_capability_risks(oracle_boundary)
    cleanup_priorities = _cleanup_priorities(fragment_audit, high_value_unpromoted)

    return {
        "scope": "preflight_fragment_scan",
        "summary": {
            "authority_layers_scanned": 4,
            "production_truth_layer": "main_repo_truth",
            "high_value_unpromoted_count": len(high_value_unpromoted),
            "redundant_or_mirror_count": len(redundant_or_mirror),
            "workspace_residue_count": len(fragment_audit.get("workspace_residue", {}).get("untracked_files", [])),
            "real_capability_risk_count": len(real_capability_risks),
            "real_capability_status": "engineering_surfaces_covered_but_external_accuracy_not_closed",
        },
        "layers": {
            "main_repo_truth": {
                "status": "authoritative",
                "paths": [
                    str(ROOT / "SKILL.md"),
                    str(ROOT / "AGENTS.md"),
                    str(ROOT / "scripts"),
                    str(ROOT / "tests"),
                    str(ROOT / "references"),
                    str(ROOT / "docs" / "research"),
                ],
            },
            "repo_local_drafts": {
                "status": "draft_reference_only",
                "path": str(LOCAL_DRAFTS_DIR),
            },
            "external_work_brain": {
                "status": "recovery_reference_only",
                "path": str(EXTERNAL_WORK_BRAIN_DIR),
            },
            "distribution_mirror": {
                "status": "mirror_do_not_reverse_sync",
                "path": str(DISTRIBUTION_MIRROR_DIR),
            },
        },
        "upstream_audits": {
            "fragment_audit": {
                "valid": fragment_audit.get("valid"),
                "candidate_count": fragment_audit.get("fragments", {}).get("candidate_count"),
                "workspace_residue_count": fragment_audit.get("workspace_residue", {}).get("untracked_count"),
            },
            "capability_audit": {
                "valid": capability_audit.get("valid"),
                "technique_count": capability_audit.get("technique_count"),
                "problem_count": capability_audit.get("problem_count"),
            },
        },
        "findings": {
            "high_value_unpromoted_count": len(high_value_unpromoted),
            "redundant_or_mirror_count": len(redundant_or_mirror),
            "workspace_residue_count": len(fragment_audit.get("workspace_residue", {}).get("untracked_files", [])),
            "real_capability_risk_count": len(real_capability_risks),
        },
        "high_value_unpromoted": high_value_unpromoted,
        "redundant_or_mirror": redundant_or_mirror,
        "real_capability_boundary": {
            "status": "not_fully_closed",
            "oracle_boundary": {
                "scope": oracle_boundary.get("scope"),
                "production_tuning_recommended": oracle_boundary.get("summary", {}).get("production_tuning_recommended"),
                "dasha_cases": oracle_boundary.get("summary", {}).get("dasha_cases"),
                "shadbala_cases": oracle_boundary.get("summary", {}).get("shadbala_cases"),
                "longitude_cases": oracle_boundary.get("summary", {}).get("longitude_cases"),
                "open_items": oracle_boundary.get("summary", {}).get("open_items", []),
            },
        },
        "real_capability_risks": real_capability_risks,
        "cleanup_priorities": cleanup_priorities,
        "boundary": (
            "Run this preflight scan before major work so drafts, mirrors, and external-work-brain "
            "fragments are reviewed deliberately, and so engineering-surface success is not mistaken "
            "for externally validated historical accuracy."
        ),
    }


def main() -> int:
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
