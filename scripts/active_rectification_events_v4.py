# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Compatibility entrypoint backed by the formal V5 score service."""
from __future__ import annotations

from typing import Any

from scripts.rectification.api_service import score_candidates


def score_life_events_v4(request: dict[str, Any]) -> dict[str, Any]:
    return score_candidates(request)


if __name__ == "__main__":
    raise SystemExit("Import score_life_events_v4 from the worker or API server.")
