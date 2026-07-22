#!/usr/bin/env python3
"""Compare local varga signs with jyotishganit observation raw.

Only compares fields with shared schema: D2/D4/D9/D10 sign labels plus
coverage for Panchanga/BAV/SAV/Shadbala. Observation-only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_CASE_LATITUDE = 37.7749
PUBLIC_CASE_LONGITUDE = -122.4194
TARGETS = {
    "D2": ["D2_Hora"],
    "D4": ["D4_Chaturthamsa", "D4_Turyamsa"],
    "D9": ["D9_Navamsa"],
    "D10": ["D10_Dasamsa"],
}


def stable(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def local_varga(args: argparse.Namespace) -> dict[str, Any]:
    cmd = [
        sys.executable,
        "scripts/jyotish_engine.py",
        "varga-full",
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
        "--lat",
        str(args.latitude),
        "--lon",
        str(args.longitude),
        "--tz",
        str(args.timezone),
        "--divisions",
        "D2,D4,D9,D10",
    ]
    return json.loads(subprocess.check_output(cmd, cwd=ROOT, text=True))


def jyotishganit_raw(args: argparse.Namespace) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "references/open_source_sources/jyotishganit"))
    from jyotishganit.main import calculate_birth_chart  # type: ignore
    from datetime import datetime

    chart = calculate_birth_chart(
        datetime(args.year, args.month, args.day, args.hour, args.minute),
        args.latitude,
        args.longitude,
        args.timezone,
        args.location,
        args.name,
    )
    return chart.to_dict()


def jyotishganit_signs(raw: dict[str, Any], code: str) -> dict[str, str]:
    section = raw.get("divisionalCharts", {}).get(code.lower(), {})
    rows: dict[str, str] = {}
    asc = section.get("ascendant", {}).get("sign")
    if asc:
        rows["Ascendant"] = asc
    for house in section.get("houses", []):
        for occ in house.get("occupants", []):
            planet = occ.get("celestialBody")
            sign = occ.get("sign")
            if planet and sign:
                rows[planet] = sign
    return rows


def local_signs(raw: dict[str, Any], code: str) -> dict[str, str]:
    section = {}
    for key in TARGETS[code]:
        if key in raw:
            section = raw[key]
            break
    return {
        body: value.get("sign")
        for body, value in section.items()
        if isinstance(value, dict) and body != "_meta" and value.get("sign")
    }


def build(args: argparse.Namespace) -> dict[str, Any]:
    local = local_varga(args)
    jyo = jyotishganit_raw(args)
    rows = []
    for code in TARGETS:
        lrows = local_signs(local, code)
        jrows = jyotishganit_signs(jyo, code)
        bodies = sorted(set(lrows) | set(jrows))
        for body in bodies:
            rows.append(
                {
                    "section": code,
                    "body": body,
                    "local_sign": lrows.get(body),
                    "jyotishganit_sign": jrows.get(body),
                    "status": "match" if lrows.get(body) == jrows.get(body) else "mismatch",
                }
            )
    summary = {
        "row_count": len(rows),
        "match_count": sum(1 for r in rows if r["status"] == "match"),
        "mismatch_count": sum(1 for r in rows if r["status"] == "mismatch"),
    }
    return {
        "scope": "jyotishganit_vs_local_field_comparison",
        "created_at": "2026-07-19",
        "status": "mismatch" if summary["mismatch_count"] else "match",
        "claim_status": "observation_only",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "request": vars(args),
        "summary": summary,
        "coverage": {
            "panchanga_jyotishganit": jyo.get("panchanga") is not None,
            "BAV_SAV_jyotishganit": isinstance(jyo.get("ashtakavarga"), dict)
            and "sav" in jyo.get("ashtakavarga", {}),
            "Shadbala_jyotishganit": jyo.get("shadbala") is not None or jyo.get("strengths") is not None,
        },
        "comparison_hash": hashlib.sha256(stable(rows).encode("utf-8")).hexdigest(),
        "rows": rows,
        "boundary": "Sign-level comparison only. Mismatch rows require field-level formula/ayanamsa/node/rounding attribution; do not majority-vote truth.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=1955)
    ap.add_argument("--month", type=int, default=2)
    ap.add_argument("--day", type=int, default=24)
    ap.add_argument("--hour", type=int, default=19)
    ap.add_argument("--minute", type=int, default=15)
    ap.add_argument("--latitude", type=float, default=PUBLIC_CASE_LATITUDE)
    ap.add_argument("--longitude", type=float, default=PUBLIC_CASE_LONGITUDE)
    ap.add_argument("--timezone", type=float, default=-8.0)
    ap.add_argument("--location", default="San Francisco, CA")
    ap.add_argument("--name", default="Steve Jobs public")
    ap.add_argument("--output")
    args = ap.parse_args()
    payload = build(args)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
