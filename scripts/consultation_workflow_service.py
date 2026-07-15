#!/usr/bin/env python3
"""Shared consultation workflow boundary for API and MCP callers."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
for path in (ROOT, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def execute_consultation_workflow(body: dict[str, Any], *, surface: str = "api") -> dict[str, Any]:
    from jyotish_api_server import JyotishAPIHandler, execute_consultation_workflow as _execute

    handler = JyotishAPIHandler.__new__(JyotishAPIHandler)
    return _execute(handler, body=body, surface=surface)


def build_runtime_evidence_helpers(chart: dict[str, Any]) -> dict[str, Any]:
    from jyotish_api_server import JyotishAPIHandler

    handler = JyotishAPIHandler.__new__(JyotishAPIHandler)
    return {
        "vedastro_official": handler._high_rigor_vedastro_official_summary(chart),
        "vedastro_archive_manifest": handler._compute_vedastro_gateway_archives(),
        "interpretation_coverage": handler._interpretation_source_runtime_coverage(chart),
    }
