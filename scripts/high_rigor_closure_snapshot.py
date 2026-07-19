#!/usr/bin/env python3
"""Materialize high-rigor closure gate output as a dated evidence snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.high_rigor_closure_gate import build_report


def stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def build(date: str) -> dict[str, Any]:
    report = build_report()
    snapshot = {
        "scope": "high_rigor_closure_gate_snapshot",
        "created_at": date,
        "source_scope": report["scope"],
        "overall_status": report["overall_status"],
        "production_tuning_allowed": report["production_tuning_allowed"],
        "verified_day_month_timing_allowed": report["verified_day_month_timing_allowed"],
        "birth_time_truth_allowed": report["birth_time_truth_allowed"],
        "commercial_sync_allowed": report["commercial_sync_allowed"],
        "gates": report["gates"],
        "next_actions": report["next_actions"],
        "boundary": "Snapshot of gate state only; blocked/partial gates remain blocked until their evidence packets close.",
    }
    snapshot["snapshot_hash"] = hashlib.sha256(stable_json(snapshot).encode("utf-8")).hexdigest()
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-07-20")
    args = parser.parse_args()
    print(json.dumps(build(args.date), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
