#!/usr/bin/env python3
"""Build same-input parity packet for UL/A7/A10/KP cusp fields.

The packet deliberately separates local runtime observations from external
parity. It does not claim three-engine parity unless each field has enough
same-input external raw rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from scripts.active_rectification_questions import recast_candidate_layers
from scripts.vedicastro_kp_house_cusp_probe import build as build_vedicastro_kp


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "references/oracle/ul_a7_a10_kp_cusp_same_input_parity_probe_2026_07_22.json"


def stable(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _local_observation(args: argparse.Namespace) -> dict[str, Any]:
    candidate = datetime(args.year, args.month, args.day, args.hour, args.minute, args.second)
    recast = recast_candidate_layers(
        candidate,
        lat=args.latitude,
        lon=args.longitude,
        tz=args.tz_offset,
        ayanamsa=args.local_ayanamsa,
    )
    if not recast:
        return {"status": "error", "error": "local recast returned null"}
    arudha = recast.get("arudha") or {}
    return {
        "status": "complete",
        "engine": "local",
        "fields": {
            "UL": arudha.get("UL"),
            "A7": arudha.get("A7"),
            "A10": arudha.get("A10"),
            "KP_cusps": recast.get("kp_cusps"),
        },
        "raw_hash": hashlib.sha256(stable(recast).encode("utf-8")).hexdigest(),
        "raw": recast,
    }


def _vedicastro_observation(args: argparse.Namespace) -> dict[str, Any]:
    try:
        payload = build_vedicastro_kp(SimpleNamespace(
            year=args.year,
            month=args.month,
            day=args.day,
            hour=args.hour,
            minute=args.minute,
            second=args.second,
            latitude=args.latitude,
            longitude=args.longitude,
            timezone=args.timezone,
            ayanamsa=args.kp_ayanamsa,
            house_system=args.house_system,
        ))
        return {
            "status": "complete",
            "engine": "VedicAstro",
            "fields": {
                "KP_cusps": payload.get("raw", {}).get("houses"),
            },
            "raw_hash": payload.get("raw_hash"),
            "schema_fingerprint": payload.get("schema_fingerprint"),
            "raw": payload.get("raw"),
            "boundary": payload.get("boundary"),
        }
    except Exception as exc:  # noqa: BLE001 - packet must capture exact runtime blocker
        return {
            "status": "blocked_runtime_error",
            "engine": "VedicAstro",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def build(args: argparse.Namespace) -> dict[str, Any]:
    request = {
        "year": args.year,
        "month": args.month,
        "day": args.day,
        "hour": args.hour,
        "minute": args.minute,
        "second": args.second,
        "latitude": args.latitude,
        "longitude": args.longitude,
        "timezone": args.timezone,
        "tz_offset": args.tz_offset,
        "local_ayanamsa": args.local_ayanamsa,
        "kp_ayanamsa": args.kp_ayanamsa,
        "house_system": args.house_system,
    }
    observations = [
        _local_observation(args),
        _vedicastro_observation(args),
        {
            "status": "not_captured",
            "engine": "PyJHora",
            "missing_fields": ["UL", "A7", "A10", "KP_cusps"],
            "boundary": "AGPL black-box capture required; no same-input raw packet exists.",
        },
        {
            "status": "no_field_contract",
            "engine": "jyotishganit",
            "missing_fields": ["UL", "A7", "A10", "KP_cusps"],
            "boundary": "No mapped same-input Arudha/KP cusp field contract exists.",
        },
    ]
    field_rows = []
    for field in ["UL", "A7", "A10", "KP_cusps"]:
        external_ready = [
            obs["engine"]
            for obs in observations
            if obs["engine"] != "local"
            and obs["status"] == "complete"
            and (obs.get("fields") or {}).get(field)
        ]
        field_rows.append({
            "field": field,
            "local_ready": observations[0]["status"] == "complete" and bool((observations[0].get("fields") or {}).get(field)),
            "external_ready_engines": external_ready,
            "external_ready_count": len(external_ready),
            "three_engine_parity_status": "blocked",
            "claim_boundary": f"{field} remains observation-only until same-input external raw from at least two independent legal sources is captured.",
        })
    return {
        "scope": "ul_a7_a10_kp_cusp_same_input_parity_probe",
        "created_at": "2026-07-22",
        "claim_status": "blocked",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "request": request,
        "summary": {
            "field_count": len(field_rows),
            "local_ready_count": sum(row["local_ready"] for row in field_rows),
            "three_engine_parity_ready_count": 0,
            "external_ready_field_count": sum(row["external_ready_count"] > 0 for row in field_rows),
        },
        "observations": observations,
        "field_rows": field_rows,
        "packet_hash": hashlib.sha256(stable({"request": request, "field_rows": field_rows}).encode("utf-8")).hexdigest(),
        "boundary": "Same-input probe only. UL/A7/A10/KP cusp external three-engine parity remains blocked.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=1955)
    parser.add_argument("--month", type=int, default=2)
    parser.add_argument("--day", type=int, default=24)
    parser.add_argument("--hour", type=int, default=19)
    parser.add_argument("--minute", type=int, default=15)
    parser.add_argument("--second", type=int, default=0)
    parser.add_argument("--latitude", type=float, default=37.3382)
    parser.add_argument("--longitude", type=float, default=-122.0383)
    parser.add_argument("--timezone", default="America/Los_Angeles")
    parser.add_argument("--tz-offset", type=float, default=-8)
    parser.add_argument("--local-ayanamsa", default="lahiri")
    parser.add_argument("--kp-ayanamsa", default="Krishnamurti")
    parser.add_argument("--house-system", default="Placidus")
    parser.add_argument("--output", default=str(OUTPUT))
    args = parser.parse_args()
    packet = build(args)
    text = json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True)
    Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
