#!/usr/bin/env python3
"""Small display view for the 42-row Shadbala component closure manifest."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "references/oracle/shadbala_component_closure_all_rows_2026_07_23.json"


def build_shadbala_component_status_view(path: Path = MANIFEST) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path.relative_to(ROOT)) if path.is_absolute() else str(path),
            "status": "blocked_manifest_missing",
            "row_count": 0,
            "truth_ready": False,
            "claim_boundary": "component_manifest_missing_no_truth_upgrade",
        }

    data = json.loads(path.read_text(encoding="utf-8"))
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    status_counts = summary.get("closure_status_counts") if isinstance(summary.get("closure_status_counts"), dict) else {}
    component_counts = summary.get("component_counts") if isinstance(summary.get("component_counts"), dict) else {}
    return {
        "path": str(path.relative_to(ROOT)),
        "status": data.get("claim_status") or "component_explanatory_partial",
        "row_count": int(summary.get("row_count") or 0),
        "component_counts": component_counts,
        "closure_status_counts": status_counts,
        "closed_observation_row_count": int(summary.get("closed_observation_row_count") or 0),
        "blocked_or_unresolved_row_count": int(summary.get("row_count") or 0)
        - int(summary.get("closed_observation_row_count") or 0),
        "truth_ready": bool(summary.get("truth_ready")),
        "production_tuning_allowed": bool(data.get("production_tuning_allowed")),
        "truth_matrix_allowed": bool(data.get("truth_matrix_allowed")),
        "claim_boundary": "component_explanatory_partial_not_absolute_virupa_truth",
        "display_note": "42 Shadbala component rows are visible as evidence status; Naisargika is observation-closed, other components remain formula/method arbitration.",
    }


if __name__ == "__main__":
    print(json.dumps(build_shadbala_component_status_view(), ensure_ascii=False, indent=2, sort_keys=True))
