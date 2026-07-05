#!/usr/bin/env python3
"""Validate interpretation source inventory wiring and draft quarantine."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp_server import _existing_interpretation_source_pack  # noqa: E402


REQUIRED_LAYERS = [
    "primary_truth",
    "frontend_interpretation",
    "qa_governance",
    "reader_validation",
    "yoga_rules",
    "saham_rules",
    "quarantined_drafts",
]

SCAN_ROOTS = [
    "references",
    "docs",
    "jyotish-app",
    "assets",
    "SKILL.md",
    "AGENTS.md",
]

EXCLUDED_PARTS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "venv_vedastro",
    "build",
    "dist",
    "scratch",
}

TEXT_EXTENSIONS = {".md", ".txt", ".json", ".js", ".ts", ".tsx", ".jsx", ".html", ".csv"}

CANDIDATE_KEYWORDS = [
    "interpret",
    "解释",
    "解读",
    "reading",
    "reader",
    "rule",
    "rules",
    "规则",
    "template",
    "模板",
    "case",
    "案例",
    "bphs",
    "parashara",
    "parasara",
    "raman",
    "jataka",
    "saravali",
    "phaladeepika",
    "hora",
    "house",
    "宫",
    "lord",
    "主",
    "yoga",
    "saham",
    "dasha",
    "transit",
    "career",
    "profession",
    "事业",
    "wealth",
    "finance",
    "财富",
    "marriage",
    "relationship",
    "婚",
    "关系",
    "timing",
    "应期",
    "event",
    "预测",
    "validation",
    "校验",
    "qa",
    "workflow",
]


def build_report() -> dict[str, Any]:
    source_pack = _existing_interpretation_source_pack()
    inventory = source_pack.get("interpretation_source_inventory") if isinstance(source_pack, dict) else {}
    if not isinstance(inventory, dict):
        inventory = {}
    layers = inventory.get("layers") if isinstance(inventory.get("layers"), dict) else {}
    summary = inventory.get("summary") if isinstance(inventory.get("summary"), dict) else {}
    source_refs = source_pack.get("source_refs") if isinstance(source_pack.get("source_refs"), list) else []
    missing_layers = [name for name in REQUIRED_LAYERS if name not in layers]
    missing_refs = inventory.get("missing_refs") if isinstance(inventory.get("missing_refs"), list) else []
    promoted_quarantined = (
        inventory.get("promoted_quarantined_refs")
        if isinstance(inventory.get("promoted_quarantined_refs"), list)
        else []
    )
    failures: list[dict[str, Any]] = []
    if source_pack.get("status") != "used":
        failures.append({"id": "source_pack_not_used", "status": source_pack.get("status")})
    if inventory.get("status") != "used":
        failures.append({"id": "inventory_not_used", "status": inventory.get("status")})
    if missing_layers:
        failures.append({"id": "missing_inventory_layers", "layers": missing_layers})
    if missing_refs:
        failures.append({"id": "missing_source_refs", "refs": missing_refs})
    if promoted_quarantined:
        failures.append({"id": "quarantined_drafts_promoted", "refs": promoted_quarantined})

    status = "pass" if not failures else "fail"
    return {
        "scope": "interpretation_source_inventory_gate",
        "status": status,
        "source_pack_status": source_pack.get("status"),
        "inventory_status": inventory.get("status"),
        "summary": summary,
        "layers": layers,
        "runtime_source_refs": source_refs,
        "full_classification": _build_full_classification(source_refs, layers),
        "failures": failures,
        "boundary": (
            "This gate validates explicit source inventory wiring. It does not promote drafts "
            "or replace MEVG/global-web/real-case verification for interpretive claims."
        ),
    }


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _should_skip(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.parts)


def _iter_candidate_files() -> list[Path]:
    items: list[Path] = []
    for root_name in SCAN_ROOTS:
        root = ROOT / root_name
        if root.is_file():
            items.append(root)
        elif root.exists():
            items.extend(path for path in root.rglob("*") if path.is_file())
    return sorted(set(items))


def _is_candidate(path: Path) -> bool:
    if _should_skip(path) or path.suffix.lower() not in TEXT_EXTENSIONS:
        return False
    rel = _relative(path).lower()
    name = path.name.lower()
    if any(keyword.lower() in rel or keyword.lower() in name for keyword in CANDIDATE_KEYWORDS):
        return True
    if path.stat().st_size > 300_000:
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")[:4000].lower()
    except OSError:
        return False
    return any(keyword.lower() in text for keyword in CANDIDATE_KEYWORDS)


def _classify_candidate(path: str, runtime_source_refs: set[str], layer_refs: set[str]) -> dict[str, Any]:
    if path in runtime_source_refs and path in {
        "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/p1_p12.md",
        "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/house_framework.md",
        "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/qa_rules.md",
        "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/yogas.md",
        "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-reader/resources/chart_reading_rules.md",
        "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-reader/resources/validation_rules.md",
    }:
        return {
            "classification": "runtime_reference_layer",
            "priority": "runtime",
            "promotion_status": "already_wired",
            "reason": "Already exposed through interpretation_source_pack.source_refs.",
        }
    if path.startswith("references/real_case_studies/"):
        return {
            "classification": "real_case_calibration",
            "priority": "priority_1",
            "promotion_status": "reference_layer_candidate",
            "reason": "Real-case material should be reviewed before confidence calibration claims.",
        }
    if path.startswith("references/open_source_sources/rishi-ai-mcp/"):
        return {
            "classification": "open_source_reference",
            "priority": "priority_1",
            "promotion_status": "already_wired" if path in runtime_source_refs else "reference_layer_candidate",
            "reason": "User-prioritized open-source skill/workflow corpus; must remain license-aware.",
        }
    if path.startswith("references/open_source_sources/vedic-astro-skills/"):
        return {
            "classification": "open_source_reference",
            "priority": "priority_1",
            "promotion_status": "already_wired" if path in runtime_source_refs else "reference_layer_candidate",
            "reason": "User-prioritized open-source Jyotish skills corpus; classify before selective reuse.",
        }
    if path.startswith("references/open_source_sources/"):
        return {
            "classification": "open_source_reference",
            "priority": "priority_2",
            "promotion_status": "reference_layer_candidate",
            "reason": "Open-source reference corpus; classify with license boundary before runtime use.",
        }
    if path in runtime_source_refs:
        return {
            "classification": "runtime_reference_layer",
            "priority": "runtime",
            "promotion_status": "already_wired",
            "reason": "Already exposed through interpretation_source_pack.source_refs.",
        }
    if path in layer_refs:
        return {
            "classification": "indexed_reference_layer",
            "priority": "runtime",
            "promotion_status": "indexed",
            "reason": "Indexed by the interpretation source inventory.",
        }
    if path.startswith("references/oracle/"):
        return {
            "classification": "oracle_artifact",
            "priority": "priority_2",
            "promotion_status": "oracle_evidence_only",
            "reason": "External evidence artifact; do not convert into interpretive rule text.",
        }
    if path.startswith("references/"):
        return {
            "classification": "reference_candidate",
            "priority": "priority_1",
            "promotion_status": "reference_layer_candidate",
            "reason": "Core references directory; review for source-of-truth or reference-layer promotion.",
        }
    if path.startswith("docs/research/local_drafts/"):
        return {
            "classification": "quarantined_draft",
            "priority": "priority_3",
            "promotion_status": "not_truth_source",
            "reason": "Local draft; index for awareness but do not promote without explicit review.",
        }
    if path.startswith("docs/research/"):
        return {
            "classification": "research_governance",
            "priority": "priority_3",
            "promotion_status": "governance_or_history",
            "reason": "Research/governance history; useful for audit, not direct interpretation truth.",
        }
    if path.startswith("docs/benchmark/") or path.startswith("benchmarks/") or path.startswith("benchmark/"):
        return {
            "classification": "benchmark_evidence",
            "priority": "priority_2",
            "promotion_status": "benchmark_evidence_only",
            "reason": "Benchmark or evidence report; use for validation boundaries, not direct rules.",
        }
    if path.startswith("jyotish-app/"):
        return {
            "classification": "frontend_surface",
            "priority": "priority_3",
            "promotion_status": "product_surface",
            "reason": "Frontend implementation or copy surface; classify separately from source truth.",
        }
    if path.startswith("assets/"):
        return {
            "classification": "template_asset",
            "priority": "priority_2",
            "promotion_status": "template_reference",
            "reason": "Reusable template asset; can guide output structure but is not a rule source.",
        }
    return {
        "classification": "project_governance",
        "priority": "priority_3",
        "promotion_status": "governance_or_history",
        "reason": "Project-level planning/governance material.",
    }


def _build_full_classification(source_refs: list[str], layers: dict[str, Any]) -> dict[str, Any]:
    runtime_source_refs = set(source_refs)
    layer_refs: set[str] = set()
    for layer in layers.values():
        if isinstance(layer, dict):
            refs = layer.get("source_refs")
            if isinstance(refs, list):
                layer_refs.update(str(ref) for ref in refs)

    candidate_paths = [_relative(path) for path in _iter_candidate_files() if _is_candidate(path)]
    by_path = {
        path: _classify_candidate(path, runtime_source_refs, layer_refs)
        for path in candidate_paths
    }
    classification_counts: dict[str, int] = {}
    priority_bucket_counts: dict[str, int] = {}
    promotion_status_counts: dict[str, int] = {}
    for item in by_path.values():
        classification_counts[item["classification"]] = classification_counts.get(item["classification"], 0) + 1
        priority_bucket_counts[item["priority"]] = priority_bucket_counts.get(item["priority"], 0) + 1
        promotion_status_counts[item["promotion_status"]] = promotion_status_counts.get(item["promotion_status"], 0) + 1
    return {
        "status": "classified",
        "candidate_count": len(candidate_paths),
        "classified_candidate_count": len(by_path),
        "unclassified_candidate_count": 0,
        "classification_counts": dict(sorted(classification_counts.items())),
        "priority_bucket_counts": dict(sorted(priority_bucket_counts.items())),
        "promotion_status_counts": dict(sorted(promotion_status_counts.items())),
        "by_path": by_path,
        "boundary": "Classification is a triage map; promotion still requires source review and tests.",
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
