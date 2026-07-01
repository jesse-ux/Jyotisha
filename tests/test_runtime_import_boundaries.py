#!/usr/bin/env python3
"""Regression tests for runtime import-source boundaries."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIRROR_SCRIPTS_TOKEN = ".workbuddy/skills/jyotish-vedic-astrology/scripts"


def test_bphs_validator_does_not_import_varga_from_distribution_mirror() -> None:
    script = ROOT / "scripts" / "validate_bphs_invariants.py"
    text = script.read_text(encoding="utf-8")

    assert MIRROR_SCRIPTS_TOKEN not in text


def test_runtime_entrypoints_do_not_put_distribution_mirror_on_import_path() -> None:
    runtime_entrypoints = [
        ROOT / "mcp_server.py",
        ROOT / "scripts" / "jyotish_api_server.py",
        ROOT / "scripts" / "unified_consultation_orchestrator.py",
        ROOT / "scripts" / "vedastro_service_adapter.py",
        ROOT / "scripts" / "historical_event_backtest.py",
        ROOT / "scripts" / "validate_bphs_invariants.py",
    ]

    offenders = [
        str(path.relative_to(ROOT))
        for path in runtime_entrypoints
        if path.exists() and MIRROR_SCRIPTS_TOKEN in path.read_text(encoding="utf-8", errors="ignore")
    ]

    assert offenders == []


def test_mcp_docstring_marks_workbuddy_as_distribution_mirror_not_runtime_source() -> None:
    text = (ROOT / "mcp_server.py").read_text(encoding="utf-8", errors="ignore")

    assert "Add to ~/.workbuddy/mcp.json" not in text
    assert "/.workbuddy/skills/jyotish-vedic-astrology/mcp_server.py" not in text
    assert "distribution mirror" in text
    assert "reference only" in text
