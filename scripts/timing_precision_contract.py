#!/usr/bin/env python3
"""Honest three-layer timing contract for uncalibrated day/month rankings."""

from __future__ import annotations

from typing import Any


def build_timing_precision_contract(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    candidates = source.get("candidate_windows") if isinstance(source.get("candidate_windows"), list) else []
    triggers = source.get("exact_triggers") if isinstance(source.get("exact_triggers"), list) else []
    verified_window = source.get("verified_window") or source.get("broad_window")
    return {
        "timing_precision": "candidate_day_window" if candidates else "broad_window_only",
        "claim_status": "exploratory_unvalidated",
        "verified_window": verified_window,
        "candidate_windows": candidates,
        "exact_triggers": triggers,
        "promotion_gate": {
            "status": "blocked",
            "required": "new_independently_labeled_day_level_holdout",
            "current_negative_controls_reusable_for_tuning": False,
        },
        "boundary": "候选日期未通过独立日级 holdout 验证，不能作为确定事件承诺；精确时间仅表示技术触发点。",
    }
