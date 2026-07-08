#!/usr/bin/env python3
"""Replay local Jyotish engines against public birth-data seed cases."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "references" / "public_oracle_cases.json"


def _birth_args(birth: dict[str, Any]) -> list[str]:
    args: list[str] = []
    for key in ("year", "month", "day", "hour", "minute", "second", "lat", "lon", "tz"):
        args.extend([f"--{key}", str(birth[key])])
    return args


def _commands(case: dict[str, Any]) -> list[dict[str, Any]]:
    birth = _birth_args(case["birth"])
    return [
        {"id": "chart_d1", "command": ["chart", *birth]},
        {"id": "varga_d9", "command": ["varga", *birth, "--d9"]},
        {"id": "varga_full_core", "command": ["varga-full", *birth, "--divisions", "D2,D4,D7,D9,D10,D12,D16,D20,D24,D30,D60"]},
        {"id": "vimshottari_md_ad", "command": ["dasha", *birth, "--years", "45"]},
        {"id": "vimshottari_pd", "script": "scripts/vimshottari_subperiod_timeline.py", "args": [*birth, "--years", "45"]},
        {"id": "yoga", "command": ["yoga", *birth]},
        {"id": "shadbala", "command": ["shadbala", *birth]},
        {"id": "ashtakavarga", "command": ["ashtakavarga", *birth]},
        {"id": "kp", "command": ["kp", *birth]},
        {"id": "jaimini", "command": ["jaimini", *birth]},
        {"id": "narayana_dasha", "command": ["narayana-dasha", *birth]},
        {"id": "tajika", "command": ["tajika", *birth, "--age", "30"]},
        {"id": "solar_return", "command": ["solar-return", *birth, "--target-year", str(case["birth"]["year"] + 30)]},
        {"id": "muhurta", "command": ["muhurta", "--date", "2027-03-01", "--scan-days", "1"]},
        {"id": "transit", "command": ["transit", "--year", "2027", "--month", "3", "--day", "1", "--planet", "Jupiter,Saturn", "--tz", str(case["birth"]["tz"])]},
        {"id": "daily_transit_scan", "script": "scripts/daily_transit_window_scan.py", "args": ["--start", "2027-03-01", "--end", "2027-03-01", "--planets", "Jupiter,Saturn", "--tz", str(case["birth"]["tz"])]},
        {"id": "double_transit_pac", "command": ["double-transit-pac", *birth, "--date", "2027-03-01", "--house", "7"]},
        {"id": "vivah_saham", "command": ["vivah-saham", *birth, "--transit-date", "2027-03-01"]},
        {"id": "flying_star_audit", "script": "scripts/flying_star_audit.py", "args": [*birth, "--age", "30", "--event-house", "7"]},
        {"id": "bhava_chalit", "command": ["bhava-chalit", *birth]},
        {"id": "sudarshana", "command": ["sudarshana", *birth]},
        {"id": "aspects", "command": ["aspects", *birth]},
        {"id": "full_reading", "command": ["full-reading", *birth, "--today", "2027-03-01", "--transit-date", "2027-03-01"], "timeout": 90, "heavy": True},
    ]


def _run(item: dict[str, Any], timeout: int) -> dict[str, Any]:
    if "script" in item:
        command = [sys.executable, item["script"], *item["args"]]
    else:
        command = [sys.executable, "scripts/jyotish_engine.py", *item["command"]]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=item.get("timeout", timeout), check=False)
    status = "tested" if completed.returncode == 0 else "failed"
    payload_type = "unknown"
    if completed.returncode == 0:
        try:
            json.loads(completed.stdout)
            payload_type = "json"
        except json.JSONDecodeError:
            payload_type = "text"
    return {
        "engine": item["id"],
        "status": status,
        "returncode": completed.returncode,
        "payload_type": payload_type,
        "stderr_excerpt": (completed.stderr or "").strip()[:300],
    }


def _oracle_rows(case: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    oracles = case.get("expected_oracles", {})
    for provider, payload in oracles.items():
        if not isinstance(payload, dict):
            continue
        if "status" in payload:
            rows.append({"case_id": case["id"], "provider": provider, "target": "provider", "status": payload["status"]})
            continue
        for target, details in payload.items():
            if isinstance(details, dict):
                rows.append({
                    "case_id": case["id"],
                    "provider": provider,
                    "target": target,
                    "status": details.get("status", "pending_external_capture"),
                    "artifact": details.get("artifact"),
                    "packet": details.get("packet"),
                    "expected": details.get("expected"),
                })
    return rows


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    data = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    cases = data["cases"][:1] if args.quick else data["cases"]
    rows = []
    skipped = []
    oracle_rows = []
    for case in cases:
        oracle_rows.extend(_oracle_rows(case))
        for item in _commands(case):
            if item.get("heavy") and not args.include_heavy:
                skipped.append({"case_id": case["id"], "engine": item["id"], "status": "untested", "reason": "heavy; rerun with --include-heavy"})
                continue
            rows.append({"case_id": case["id"], **_run(item, args.timeout)})
    blocked = [
        {"engine": "VedAstro official full snapshot", "status": "blocked", "reason": "premium_key/budget/raw_response not closed"},
        {"engine": "PyJHora/JHora parity", "status": "blocked", "reason": "jhora dependency missing"},
        {"engine": "JHora desktop oracle", "status": "blocked", "reason": "manual desktop oracle required"},
        {"engine": "all_35_dasha_full_matrix", "status": "untested", "reason": "not mapped into public replay yet"},
        {"engine": "all_D1_to_D144_full_matrix", "status": "untested", "reason": "core subset replayed; exhaustive divisional sweep not yet run"},
        {"engine": "predictive_accuracy_claims", "status": "no_public_oracle", "reason": "public birth data alone cannot validate prediction accuracy"},
    ]
    summary: dict[str, int] = {}
    for row in [*rows, *skipped, *blocked]:
        summary[row["status"]] = summary.get(row["status"], 0) + 1
    oracle_summary: dict[str, int] = {}
    for row in oracle_rows:
        oracle_summary[row["status"]] = oracle_summary.get(row["status"], 0) + 1
    return {
        "scope": "public_oracle_replay",
        "boundary": data["boundary"],
        "case_count": len(cases),
        "summary": summary,
        "oracle_summary": oracle_summary,
        "expected_oracles": oracle_rows,
        "rows": rows,
        "blocked_or_untested": [*skipped, *blocked],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--include-heavy", action="store_true")
    parser.add_argument("--timeout", type=int, default=45)
    args = parser.parse_args()
    report = build_report(args)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if report["summary"].get("failed") else 0


if __name__ == "__main__":
    raise SystemExit(main())
