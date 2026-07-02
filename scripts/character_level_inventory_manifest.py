#!/usr/bin/env python3
"""Build a lightweight character-level inventory manifest for Jyotish sources.

This is an index and governance manifest, not a semantic promotion pass. It
hashes every in-scope file, extracts text metadata when cheap, and queues heavy
PDF/image/document extraction instead of running expensive OCR by default.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = ROOT / "docs" / "research" / "character_level_inventory_manifest_latest.json"
REPORT_MD = ROOT / "docs" / "research" / "character_level_inventory_manifest_latest.md"

PROJECT_SCAN_ROOTS = [
    "references",
    "references/open_source_sources",
    "docs/research",
    "SKILL.md",
    "AGENTS.md",
]

EXCLUDED_PARTS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "venv",
    "venv_vedastro",
    ".venv",
    "build",
    "dist",
}

TEXT_EXTENSIONS = {
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsonl",
    ".jsx",
    ".mjs",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}
DOCUMENT_EXTENSIONS = {".doc", ".docx", ".epub", ".mobi", ".pages", ".ppt", ".pptx", ".rtf", ".xls", ".xlsx"}


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _should_skip(path: Path) -> bool:
    try:
        rel_parts = path.relative_to(ROOT).parts
    except ValueError:
        rel_parts = path.parts
    return any(part in EXCLUDED_PARTS for part in rel_parts)


def _iter_project_files() -> list[Path]:
    files: set[Path] = set()
    for root_name in PROJECT_SCAN_ROOTS:
        root = ROOT / root_name
        if not root.exists() or _should_skip(root):
            continue
        if root.is_file():
            files.add(root)
        else:
            files.update(path for path in root.rglob("*") if path.is_file() and not _should_skip(path))
    return sorted(files)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _text_stats(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    decoded = raw.decode("utf-8", errors="replace")
    replacement_count = decoded.count("\ufffd")
    return {
        "extraction_status": "text_decode_lossy" if replacement_count else "text_indexed",
        "character_count": len(decoded),
        "line_count": decoded.count("\n") + (1 if decoded else 0),
        "decode_replacement_count": replacement_count,
    }


def _extraction_status(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return _text_stats(path)
    if suffix in PDF_EXTENSIONS:
        return {
            "extraction_status": "pdf_text_extraction_queued",
            "character_count": None,
            "line_count": None,
            "decode_replacement_count": None,
        }
    if suffix in IMAGE_EXTENSIONS:
        return {
            "extraction_status": "image_ocr_queued",
            "character_count": None,
            "line_count": None,
            "decode_replacement_count": None,
        }
    if suffix in DOCUMENT_EXTENSIONS:
        return {
            "extraction_status": "document_text_extraction_queued",
            "character_count": None,
            "line_count": None,
            "decode_replacement_count": None,
        }
    return {
        "extraction_status": "binary_indexed",
        "character_count": None,
        "line_count": None,
        "decode_replacement_count": None,
    }


def _classify_path(path: str) -> dict[str, str]:
    if path.startswith("references/open_source_sources/rishi-ai-mcp/"):
        return {
            "classification": "open_source_reference",
            "priority": "priority_1",
            "promotion_status": "reference_layer_candidate",
            "reason": "User-prioritized open-source workflow corpus; requires license-aware review.",
        }
    if path.startswith("references/open_source_sources/vedic-astro-skills/"):
        return {
            "classification": "open_source_reference",
            "priority": "priority_1",
            "promotion_status": "reference_layer_candidate",
            "reason": "User-prioritized Jyotish skill corpus; requires selective source promotion.",
        }
    if path.startswith("references/open_source_sources/"):
        return {
            "classification": "open_source_reference",
            "priority": "priority_2",
            "promotion_status": "reference_layer_candidate",
            "reason": "Open-source corpus; index first, promote only after license and conflict review.",
        }
    if path.startswith("references/real_case_studies/"):
        return {
            "classification": "real_case_calibration",
            "priority": "priority_1",
            "promotion_status": "reference_layer_candidate",
            "reason": "Real-case material for calibration; not direct rule truth.",
        }
    if path.startswith("references/oracle/"):
        return {
            "classification": "oracle_artifact",
            "priority": "priority_2",
            "promotion_status": "oracle_evidence_only",
            "reason": "Oracle artifact; use for parity evidence, not interpretive rules.",
        }
    if path.startswith("references/"):
        return {
            "classification": "reference_candidate",
            "priority": "priority_1",
            "promotion_status": "reference_layer_candidate",
            "reason": "Local reference source candidate; requires content-level review before promotion.",
        }
    if path.startswith("docs/research/local_drafts/"):
        return {
            "classification": "quarantined_draft",
            "priority": "priority_3",
            "promotion_status": "not_truth_source",
            "reason": "Historical draft; do not promote without explicit review.",
        }
    if path.startswith("docs/research/"):
        return {
            "classification": "research_governance",
            "priority": "priority_3",
            "promotion_status": "governance_or_history",
            "reason": "Research history or governance record; index separately from rule truth.",
        }
    return {
        "classification": "project_governance",
        "priority": "priority_3",
        "promotion_status": "governance_or_history",
        "reason": "Project-level governance file.",
    }


def _root_bucket(path: str) -> str:
    if path.startswith("references/open_source_sources/"):
        return "references/open_source_sources"
    if path.startswith("references/"):
        return "references"
    if path.startswith("docs/research/"):
        return "docs/research"
    return path.split("/", 1)[0]


def build_manifest(*, scope: str = "project", write: bool = True) -> dict[str, Any]:
    if scope != "project":
        raise ValueError("Only --scope project is supported by the lightweight manifest.")

    by_path: dict[str, dict[str, Any]] = {}
    classification_counts: dict[str, int] = {}
    extraction_counts: dict[str, int] = {}
    root_summary: dict[str, dict[str, int]] = {}
    unclassified_files = 0
    unknown_extraction_status = 0

    for file_path in _iter_project_files():
        rel = _relative(file_path)
        file_class = _classify_path(rel)
        extraction = _extraction_status(file_path)
        if not file_class.get("classification"):
            unclassified_files += 1
        if not extraction.get("extraction_status"):
            unknown_extraction_status += 1
        byte_count = file_path.stat().st_size
        item = {
            "path": rel,
            "suffix": file_path.suffix.lower(),
            "byte_count": byte_count,
            "sha256": _sha256(file_path),
            **extraction,
            **file_class,
        }
        by_path[rel] = item
        classification_counts[item["classification"]] = classification_counts.get(item["classification"], 0) + 1
        extraction_counts[item["extraction_status"]] = extraction_counts.get(item["extraction_status"], 0) + 1
        bucket = _root_bucket(rel)
        root_summary.setdefault(bucket, {"files": 0, "bytes": 0})
        root_summary[bucket]["files"] += 1
        root_summary[bucket]["bytes"] += byte_count

    summary = {
        "total_files": len(by_path),
        "unhashed_files": sum(1 for item in by_path.values() if not item.get("sha256")),
        "unclassified_files": unclassified_files,
        "unknown_extraction_status": unknown_extraction_status,
        "classification_counts": dict(sorted(classification_counts.items())),
        "extraction_status_counts": dict(sorted(extraction_counts.items())),
    }
    status = "pass" if summary["unhashed_files"] == 0 and unclassified_files == 0 and unknown_extraction_status == 0 else "fail"
    report = {
        "scope": scope,
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": {
            "heavy_ocr": False,
            "whole_machine_scan": False,
            "semantic_promotion": False,
            "boundary": "Fast manifest only: hashes and cheap text stats now; heavy OCR and whole-machine scan are queued.",
        },
        "scan_roots": PROJECT_SCAN_ROOTS,
        "summary": summary,
        "root_summary": dict(sorted(root_summary.items())),
        "by_path": by_path,
        "artifacts": {
            "json_report": _relative(REPORT_JSON),
            "markdown_report": _relative(REPORT_MD),
        },
    }
    if write:
        _write_reports(report)
    return report


def _write_reports(report: dict[str, Any]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(_render_markdown(report), encoding="utf-8")


def _render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Character-Level Inventory Manifest",
        "",
        f"- status: {report['status']}",
        f"- scope: {report['scope']}",
        f"- generated_at: {report['generated_at']}",
        f"- total_files: {summary['total_files']}",
        f"- unhashed_files: {summary['unhashed_files']}",
        f"- unclassified_files: {summary['unclassified_files']}",
        f"- unknown_extraction_status: {summary['unknown_extraction_status']}",
        f"- Heavy OCR: {'enabled' if report['mode']['heavy_ocr'] else 'disabled'}",
        f"- Whole-machine scan: {'enabled' if report['mode']['whole_machine_scan'] else 'disabled'}",
        "",
        "## Root Summary",
        "",
        "| Root | Files | Bytes |",
        "| --- | ---: | ---: |",
    ]
    for root, item in report["root_summary"].items():
        lines.append(f"| `{root}` | {item['files']} | {item['bytes']} |")
    lines.extend(["", "## Extraction Status Counts", ""])
    for name, count in summary["extraction_status_counts"].items():
        lines.append(f"- `{name}`: {count}")
    lines.extend(["", "## Classification Counts", ""])
    for name, count in summary["classification_counts"].items():
        lines.append(f"- `{name}`: {count}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            report["mode"]["boundary"],
            "",
            "This manifest proves indexing, hashing, and extraction-state classification. It does not by itself promote any source into the runtime truth chain.",
            "",
        ]
    )
    return "\n".join(lines)


def _summary_view(report: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in report.items()
        if key not in {"by_path"}
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", default="project", choices=["project"])
    parser.add_argument("--no-write", action="store_true", help="Print the manifest without writing report artifacts.")
    parser.add_argument("--summary-only", action="store_true", help="Print only summary fields; still writes full artifacts unless --no-write is set.")
    args = parser.parse_args(argv)

    report = build_manifest(scope=args.scope, write=not args.no_write)
    printable = _summary_view(report) if args.summary_only else report
    print(json.dumps(printable, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
