#!/usr/bin/env python3
"""Daily transit / optional double-transit PAC scanner."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str], timeout: int = 90) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=timeout, check=False)
    if completed.returncode != 0:
        return {"status": "error", "stderr": (completed.stderr or completed.stdout).strip()[:500]}
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"status": "invalid_json", "stdout_excerpt": completed.stdout[:500]}


def _date_range(start: str, end: str) -> list[date]:
    cursor = date.fromisoformat(start)
    stop = date.fromisoformat(end)
    days = []
    while cursor <= stop:
        days.append(cursor)
        cursor += timedelta(days=1)
    return days


def _transit(day: date, args: argparse.Namespace) -> dict[str, Any]:
    return _run([
        sys.executable,
        "scripts/jyotish_engine.py",
        "transit",
        "--year",
        str(day.year),
        "--month",
        str(day.month),
        "--day",
        str(day.day),
        "--planet",
        args.planets,
        "--tz",
        str(args.tz),
    ])


def _double_transit(day: date, args: argparse.Namespace) -> dict[str, Any]:
    return _run([
        sys.executable,
        "scripts/jyotish_engine.py",
        "double-transit-pac",
        "--year",
        str(args.year),
        "--month",
        str(args.month),
        "--day",
        str(args.day),
        "--hour",
        str(args.hour),
        "--minute",
        str(args.minute),
        "--second",
        str(args.second),
        "--lat",
        str(args.lat),
        "--lon",
        str(args.lon),
        "--tz",
        str(args.tz),
        "--date",
        day.isoformat(),
        "--house",
        str(args.house),
    ])


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    rows = []
    for day in _date_range(args.start, args.end):
        row: dict[str, Any] = {"date": day.isoformat(), "transit": _transit(day, args)}
        if args.include_double_transit:
            row["double_transit_pac"] = _double_transit(day, args)
        rows.append(row)
    return {
        "scope": "daily_transit_window_scan",
        "start": args.start,
        "end": args.end,
        "days": len(rows),
        "planets": args.planets.split(","),
        "include_double_transit": args.include_double_transit,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--planets", default="Jupiter,Saturn,Rahu,Ketu")
    parser.add_argument("--tz", type=float, default=0)
    parser.add_argument("--include-double-transit", action="store_true")
    parser.add_argument("--year", type=int)
    parser.add_argument("--month", type=int)
    parser.add_argument("--day", type=int)
    parser.add_argument("--hour", type=int, default=12)
    parser.add_argument("--minute", type=int, default=0)
    parser.add_argument("--second", type=int, default=0)
    parser.add_argument("--lat", type=float, default=0.0)
    parser.add_argument("--lon", type=float, default=0.0)
    parser.add_argument("--house", type=int, default=7)
    args = parser.parse_args()
    if args.include_double_transit and None in (args.year, args.month, args.day):
        raise SystemExit("--include-double-transit requires --year --month --day")
    print(json.dumps(build_report(args), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
