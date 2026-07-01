#!/usr/bin/env python3
"""Regression tests for research governance and main-chain documentation."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_local_drafts_disposition_table_covers_all_june_drafts() -> None:
    draft_dir = ROOT / "docs" / "research" / "local_drafts" / "2026-06"
    disposition_doc = ROOT / "docs" / "research" / "local_drafts_2026_06_disposition.md"

    text = disposition_doc.read_text(encoding="utf-8")
    draft_names = sorted(path.name for path in draft_dir.glob("*.md"))

    assert len(draft_names) == 93
    missing = [name for name in draft_names if name not in text]
    assert missing == []
    assert text.count("| promote |") >= 20
    assert "| archive |" in text
    assert "| reference-only |" in text
    assert ".workbuddy" in text
    assert "Do not move or delete files in this pass" in text


def test_unique_main_chain_map_names_runtime_entrypoints_and_boundaries() -> None:
    doc = ROOT / "docs" / "research" / "unique_main_chain_map_2026_07_01.md"
    text = doc.read_text(encoding="utf-8")

    required_tokens = [
        "mcp_server.py",
        "scripts/jyotish_api_server.py",
        "scripts/unified_consultation_orchestrator.py",
        "scripts/vedastro_service_adapter.py",
        "scripts/historical_event_backtest.py",
        "SKILL.md",
        "references/strict-workflow-router.md",
        "VedAstro official snapshot",
        "rectification gate",
        "historical event backtest",
        ".workbuddy",
    ]
    for token in required_tokens:
        assert token in text

    assert "source of truth" in text.lower()
    assert "must not import from `.workbuddy`" in text
