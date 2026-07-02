#!/usr/bin/env python3
"""Regression tests for character-level source inventory manifests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_manifest(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, "scripts/character_level_inventory_manifest.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout[-2000:]
    return json.loads(completed.stdout)


def test_manifest_indexes_project_source_layers_without_heavy_ocr() -> None:
    report = _run_manifest("--scope", "project", "--no-write")

    assert report["scope"] == "project"
    assert report["status"] == "pass"
    assert report["mode"]["heavy_ocr"] is False
    assert report["mode"]["whole_machine_scan"] is False
    assert report["summary"]["total_files"] >= 900
    assert report["summary"]["unhashed_files"] == 0
    assert report["summary"]["unclassified_files"] == 0
    assert report["summary"]["unknown_extraction_status"] == 0

    roots = report["root_summary"]
    assert roots["references"]["files"] + roots["references/open_source_sources"]["files"] >= 500
    assert roots["references/open_source_sources"]["files"] >= 250
    assert roots["docs/research"]["files"] >= 500

    by_path = report["by_path"]
    assert by_path["references/advanced-techniques.md"]["classification"] == "reference_candidate"
    assert by_path["references/open_source_sources/rishi-ai-mcp/.agents/skills/career-analysis/SKILL.md"]["classification"] == "open_source_reference"
    assert by_path["docs/research/ACTIVE_FRONTS.md"]["classification"] == "research_governance"
    assert by_path["references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/qa_rules.md"]["classification"] in {
        "open_source_reference",
        "runtime_reference_layer",
    }

    for item in by_path.values():
        assert item["sha256"]
        assert item["byte_count"] >= 0
        assert item["extraction_status"] in {
            "text_indexed",
            "text_decode_lossy",
            "binary_indexed",
            "pdf_text_extraction_queued",
            "image_ocr_queued",
            "document_text_extraction_queued",
        }


def test_manifest_writes_json_and_markdown_reports() -> None:
    report = _run_manifest("--scope", "project")

    json_path = ROOT / report["artifacts"]["json_report"]
    md_path = ROOT / report["artifacts"]["markdown_report"]
    assert json_path.exists()
    assert md_path.exists()

    saved = json.loads(json_path.read_text(encoding="utf-8"))
    assert saved["summary"] == report["summary"]

    markdown = md_path.read_text(encoding="utf-8")
    assert "Character-Level Inventory Manifest" in markdown
    assert "unclassified_files: 0" in markdown
    assert "Heavy OCR: disabled" in markdown
    assert "Whole-machine scan: disabled" in markdown


def test_manifest_summary_only_omits_large_by_path_payload() -> None:
    report = _run_manifest("--scope", "project", "--no-write", "--summary-only")

    assert report["status"] == "pass"
    assert report["summary"]["total_files"] >= 900
    assert "root_summary" in report
    assert "by_path" not in report


def test_quality_gate_runs_character_level_manifest_without_writing_reports() -> None:
    quality_gate = (ROOT / "scripts" / "run_quality_gate.py").read_text(encoding="utf-8")

    assert 'ROOT / "scripts" / "character_level_inventory_manifest.py"' in quality_gate
    assert (
        '[PYTHON, "scripts/character_level_inventory_manifest.py", "--scope", "project", "--no-write", "--summary-only"]'
        in quality_gate
    )


def test_external_manifest_indexes_high_relevance_machine_fragments_without_copying_text() -> None:
    report = _run_manifest("--scope", "external", "--no-write")

    assert report["scope"] == "external"
    assert report["status"] == "pass"
    assert report["mode"]["whole_machine_scan"] is False
    assert report["mode"]["external_high_relevance_scan"] is True
    assert report["summary"]["total_files"] >= 10
    assert report["summary"]["unhashed_files"] == 0
    assert report["summary"]["unclassified_files"] == 0
    assert report["summary"]["unknown_extraction_status"] == 0

    paths = set(report["by_path"])
    assert any(path.endswith("/Downloads/印度占星.pdf") for path in paths)
    assert any("/文件仓库/印度占星文章/" in path for path in paths)
    assert any("/WorkBuddy/" in path for path in paths)
    assert any("/.workbuddy/skills/jyotish-vedic-astrology/" in path for path in paths)

    extraction_counts = report["summary"]["extraction_status_counts"]
    assert extraction_counts["pdf_text_extraction_queued"] >= 1
    assert extraction_counts["document_text_extraction_queued"] >= 1

    for path, item in report["by_path"].items():
        assert path.startswith("/Users/wuyongnaren/")
        assert item["sha256"]
        assert item["classification"] in {
            "external_book_or_document",
            "external_engine_fragment",
            "external_historical_report",
            "external_skill_fragment",
            "external_archive_or_binary",
        }
        assert "text_preview" not in item


def test_external_manifest_writes_separate_reports() -> None:
    report = _run_manifest("--scope", "external", "--summary-only")

    assert "by_path" not in report
    assert report["artifacts"]["json_report"] == "docs/research/character_level_external_manifest_latest.json"
    assert report["artifacts"]["markdown_report"] == "docs/research/character_level_external_manifest_latest.md"

    json_path = ROOT / report["artifacts"]["json_report"]
    md_path = ROOT / report["artifacts"]["markdown_report"]
    assert json_path.exists()
    assert md_path.exists()
    assert "External High-Relevance Inventory Manifest" in md_path.read_text(encoding="utf-8")


def test_extraction_queue_report_combines_project_and_external_binary_work() -> None:
    report = _run_manifest("--scope", "extraction-queue")

    assert report["scope"] == "extraction-queue"
    assert report["status"] == "pass"
    assert report["summary"]["queued_files"] >= 60
    assert report["summary"]["unhashed_files"] == 0
    assert report["queue_counts"]["pdf_text_extraction_queued"] >= 2
    assert report["queue_counts"]["document_text_extraction_queued"] >= 10
    assert report["queue_counts"]["image_ocr_queued"] >= 50

    for item in report["queue"]:
        assert item["sha256"]
        assert item["source_scope"] in {"project", "external"}
        assert item["extraction_status"] in {
            "pdf_text_extraction_queued",
            "image_ocr_queued",
            "document_text_extraction_queued",
        }
        assert "text_preview" not in item

    json_path = ROOT / report["artifacts"]["json_report"]
    md_path = ROOT / report["artifacts"]["markdown_report"]
    assert json_path.exists()
    assert md_path.exists()
    assert "Extraction Queue Manifest" in md_path.read_text(encoding="utf-8")
