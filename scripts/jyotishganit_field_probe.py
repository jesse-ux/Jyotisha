#!/usr/bin/env python3
"""Run a local jyotishganit same-case raw field probe.

Observation-only: records raw/hash/schema for D2/D4/D9/D10, Panchanga,
BAV/SAV and Shadbala availability without promoting truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
JYOTISHGANIT_ROOT = ROOT / "references/open_source_sources/jyotishganit"
TARGET_VARGAS = ["d2", "d4", "d9", "d10"]


def stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def schema_fingerprint(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: schema_fingerprint(v) for k, v in sorted(data.items())}
    if isinstance(data, list):
        if not data:
            return []
        return [schema_fingerprint(data[0])]
    return type(data).__name__


def sign_table(chart: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for code in TARGET_VARGAS:
        section = chart.get("divisionalCharts", {}).get(code)
        if not isinstance(section, dict):
            out[code.upper()] = {"status": "missing"}
            continue
        rows = []
        for house in section.get("houses", []):
            for occ in house.get("occupants", []):
                rows.append(
                    {
                        "planet": occ.get("celestialBody"),
                        "sign": occ.get("sign"),
                        "d1HousePlacement": occ.get("d1HousePlacement"),
                    }
                )
        out[code.upper()] = {
            "status": "present",
            "ascendant_sign": section.get("ascendant", {}).get("sign"),
            "planet_signs": sorted(rows, key=lambda r: str(r.get("planet"))),
        }
    return out


def build_probe(args: argparse.Namespace) -> dict[str, Any]:
    sys.path.insert(0, str(JYOTISHGANIT_ROOT))
    from jyotishganit.main import calculate_birth_chart  # type: ignore

    dt = datetime.fromisoformat(args.datetime)
    chart = calculate_birth_chart(dt, args.latitude, args.longitude, args.timezone, args.location, args.name)
    raw = chart.to_dict()
    selected = {
        "panchanga": raw.get("panchanga"),
        "varga_sign_table": sign_table(raw),
        "ashtakavarga": raw.get("ashtakavarga"),
        "shadbala": raw.get("shadbala"),
        "strengths": raw.get("strengths"),
    }
    payload = {
        "scope": "jyotishganit_field_probe",
        "created_at": "2026-07-19",
        "status": "complete",
        "claim_status": "observation_only",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "engine": {
            "name": "jyotishganit",
            "local_path": str(JYOTISHGANIT_ROOT.relative_to(ROOT)),
        },
        "request": {
            "name": args.name,
            "datetime": args.datetime,
            "latitude": args.latitude,
            "longitude": args.longitude,
            "timezone": args.timezone,
            "location": args.location,
        },
        "coverage": {
            "panchanga": raw.get("panchanga") is not None,
            "D2": selected["varga_sign_table"]["D2"]["status"] == "present",
            "D4": selected["varga_sign_table"]["D4"]["status"] == "present",
            "D9": selected["varga_sign_table"]["D9"]["status"] == "present",
            "D10": selected["varga_sign_table"]["D10"]["status"] == "present",
            "BAV_SAV": isinstance(raw.get("ashtakavarga"), dict)
            and "sav" in raw.get("ashtakavarga", {}),
            "Shadbala": raw.get("shadbala") is not None or raw.get("strengths") is not None,
        },
        "raw_hash": hashlib.sha256(stable_json(raw).encode("utf-8")).hexdigest(),
        "selected_hash": hashlib.sha256(stable_json(selected).encode("utf-8")).hexdigest(),
        "schema_fingerprint": schema_fingerprint(selected),
        "selected_raw": selected,
        "boundary": "Raw/hash observation only. Missing Shadbala field or matching signs do not prove formula truth or production timing readiness.",
    }
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datetime", default="1955-02-24T19:15:00")
    ap.add_argument("--latitude", type=float, default=37.3382)
    ap.add_argument("--longitude", type=float, default=-122.0383)
    ap.add_argument("--timezone", type=float, default=-8.0)
    ap.add_argument("--location", default="San Francisco, CA")
    ap.add_argument("--name", default="Steve Jobs public")
    ap.add_argument("--output")
    args = ap.parse_args()
    payload = build_probe(args)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
