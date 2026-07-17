#!/usr/bin/env python3
"""Scan actual local-chart differences across a birth-time candidate range."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "scripts" / "jyotish_engine.py"
_VARGAS = ("D4", "D9", "D10", "D24", "D30")


def _engine_json(command: str, payload: dict[str, Any], *, timeout: int = 20) -> dict[str, Any]:
    args = ["python3", str(ENGINE), command]
    for key in ("year", "month", "day", "hour", "minute", "lat", "lon", "tz"):
        args.extend([f"--{key}", str(payload[key])])
    if command == "varga-full":
        args.extend(["--divisions", ",".join(_VARGAS)])
    completed = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=True)
    return json.loads(completed.stdout)


def _all_varga_ascendants(payload: dict[str, Any]) -> dict[str, str | None]:
    values = {varga: None for varga in _VARGAS}
    try:
        raw = _engine_json("varga-full", payload)
    except subprocess.CalledProcessError:
        return values
    for name, chart in raw.items():
        if not isinstance(chart, dict):
            continue
        for varga in _VARGAS:
            if name.startswith(varga + "_"):
                values[varga] = (chart.get("Ascendant") or {}).get("sign")
    return values


def scan_candidate_times(payload: dict[str, Any], *, uncertainty_minutes: int = 30, step_minutes: int = 1) -> dict[str, Any]:
    required = ("year", "month", "day", "hour", "minute", "lat", "lon", "tz")
    missing = [key for key in required if payload.get(key) is None]
    if missing:
        raise ValueError(f"missing candidate scan fields: {', '.join(missing)}")
    center = datetime(int(payload["year"]), int(payload["month"]), int(payload["day"]), int(payload["hour"]), int(payload["minute"]))
    step_minutes = max(int(step_minutes), 1)
    uncertainty_minutes = max(int(uncertainty_minutes), 1)
    rows: list[dict[str, Any]] = []
    for offset in range(-uncertainty_minutes, uncertainty_minutes + 1, step_minutes):
        moment = center + timedelta(minutes=offset)
        point = {**payload, "year": moment.year, "month": moment.month, "day": moment.day, "hour": moment.hour, "minute": moment.minute}
        chart = _engine_json("chart", point)
        asc = chart.get("ascendant", {})
        divisional = _all_varga_ascendants(point)
        rows.append({
            "time": moment.strftime("%Y-%m-%d %H:%M"),
            "offset_minutes": offset,
            "d1_ascendant": asc.get("sign"),
            "d1_degree_in_sign": asc.get("degree_in_sign"),
            "divisional_ascendants": divisional,
        })
    signatures = [tuple([row["d1_ascendant"], *row["divisional_ascendants"].values()]) for row in rows]
    unavailable_vargas = [varga.upper() for varga in _VARGAS if all(row["divisional_ascendants"][varga.upper()] is None for row in rows)]
    supported_vargas = [varga.lower() for varga in _VARGAS if varga.upper() not in unavailable_vargas]
    modal = Counter(signatures).most_common(1)[0][0]
    for row, signature in zip(rows, signatures):
        row["sensitivity_count"] = sum(left != right for left, right in zip(signature, modal))
        row["sensitive_layers"] = [
            name for name, current, typical in zip(("D1", "D4", "D9", "D10", "D24", "D30"), signature, modal)
            if current != typical
        ]
    transitions = []
    for previous, current in zip(rows, rows[1:]):
        changed = [name for name in ("d1_ascendant", "divisional_ascendants") if previous[name] != current[name]]
        if changed:
            transitions.append({"between": [previous["time"], current["time"]], "changed": changed})
    return {
        "scope": "candidate_time_sensitivity_scan",
        "status": "local_computed",
        "engine": "local_jyotish_engine",
        "candidate_count": len(rows),
        "center_time": center.strftime("%Y-%m-%d %H:%M"),
        "uncertainty_minutes": uncertainty_minutes,
        "step_minutes": step_minutes,
        "rows": rows,
        "transitions": transitions,
        "supported_vargas": [varga.upper() for varga in supported_vargas],
        "unavailable_vargas": unavailable_vargas,
        "pending_layers": ["UL", "A7", "A10", "KP_cusp"],
        "boundary": "Actual local D1/Varga differences only. Unsupported Varga CLI flags are explicitly unavailable. Event answers still require an explicit event-to-candidate adjudication model before minute-level rectification.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for field, cast in (("year", int), ("month", int), ("day", int), ("hour", int), ("minute", int), ("lat", float), ("lon", float), ("tz", float)):
        parser.add_argument(f"--{field}", required=True, type=cast)
    parser.add_argument("--uncertainty-minutes", type=int, default=30)
    parser.add_argument("--step-minutes", type=int, default=1)
    args = parser.parse_args()
    print(json.dumps(scan_candidate_times(vars(args), uncertainty_minutes=args.uncertainty_minutes, step_minutes=args.step_minutes), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
