#!/usr/bin/env python3
"""Stable strict-evidence service boundary.

This module is the import target for engine/API code. The current implementation
delegates to the legacy MCP implementation while the large helper stack is being
extracted out of `mcp_server.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def collect_strict_evidence(route: str, result: dict[str, Any]) -> dict[str, Any]:
    from mcp_server import _collect_strict_evidence

    return _collect_strict_evidence(route, result)


def existing_interpretation_source_pack() -> dict[str, Any]:
    from mcp_server import _existing_interpretation_source_pack

    return _existing_interpretation_source_pack()
