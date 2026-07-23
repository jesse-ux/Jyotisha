#!/usr/bin/env python3
"""Compare a PanchangBodh KP 12-cusp packet against a local KP replay raw.

This is a field-level replay delta, not a truth upgrade.  PanchangBodh does not
show timezone, ayanamsa, or node-mode settings in the supplied screenshots, so
small numeric agreement can only make the packet replay-ready.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKET = ROOT / "references/oracle/cases/kp_12_cusp_panchangbodh_steve_jobs_2026_07_23.json"
DEFAULT_LOCAL_RAW = ROOT / "references/oracle/cases/kp_12_cusp_panchangbodh_steve_jobs_2026_07_23.local_vedicastro_replay.json"
DEFAULT_OUTPUT = ROOT / "references/oracle/cases/kp_12_cusp_panchangbodh_steve_jobs_2026_07_23.local_replay_delta.json"

SIGN_OFFSETS = {
    "aries": 0,
    "taurus": 30,
    "gemini": 60,
    "cancer": 90,
    "leo": 120,
    "virgo": 150,
    "libra": 180,
    "scorpio": 210,
    "sagittarius": 240,
    "capricorn": 270,
    "aquarius": 300,
    "pisces": 330,
}


def stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z]", "", value.casefold())


def degree_to_seconds(value: str) -> int:
    match = re.search(r"(\d+)[°:+]\s*([A-Za-z]+)?\s*(\d+)[':]\s*(\d+)", value)
    if not match:
        raise ValueError(f"unsupported_degree:{value}")
    deg = int(match.group(1))
    sign = match.group(2)
    if not sign:
        tail = re.search(r"\b(Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpio|Sagittarius|Capricorn|Aquarius|Pisces)\b", value, re.I)
        sign = tail.group(1) if tail else None
    minute = int(match.group(3))
    second = int(match.group(4))
    total = deg * 3600 + minute * 60 + second
    if sign:
        total += SIGN_OFFSETS[sign.casefold()] * 3600
    return total % (360 * 3600)


def load_packet(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    packets = document.get("packets") or []
    if len(packets) != 1:
        raise ValueError("expected_single_packet")
    return packets[0]


def load_local_rows(path: Path) -> list[dict[str, Any]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = document.get("raw", {}).get("houses") or []
    if len(rows) < 12:
        raise ValueError("local_raw_missing_12_houses")
    return rows[:12]


def build_delta(packet_path: Path = DEFAULT_PACKET, local_raw_path: Path = DEFAULT_LOCAL_RAW) -> dict[str, Any]:
    packet = load_packet(packet_path)
    local_rows = load_local_rows(local_raw_path)
    packet_rows = packet["twelve_exact_cusp_longitudes"]
    star_lords = packet["twelve_star_lords"]
    sub_lords = packet["twelve_sub_lords"]
    sub_sub_lords = packet["twelve_sub_sub_lords"]

    rows = []
    max_abs_arcsec_delta = 0
    lord_mismatches: list[dict[str, Any]] = []
    for index, (expected, actual) in enumerate(zip(packet_rows, local_rows), start=1):
        expected_seconds = degree_to_seconds(expected["degree"])
        actual_seconds = degree_to_seconds(f"{actual['SignLonDMS']} {actual['Rasi']}")
        delta = actual_seconds - expected_seconds
        if delta > 180 * 3600:
            delta -= 360 * 3600
        if delta < -180 * 3600:
            delta += 360 * 3600
        max_abs_arcsec_delta = max(max_abs_arcsec_delta, abs(delta))

        comparisons = {
            "star_lord_match": normalize_name(star_lords[index - 1]) == normalize_name(actual["NakshatraLord"]),
            "sub_lord_match": normalize_name(sub_lords[index - 1]) == normalize_name(actual["SubLord"]),
            "sub_sub_lord_match": normalize_name(sub_sub_lords[index - 1]) == normalize_name(actual["SubSubLord"]),
        }
        for field, matched in comparisons.items():
            if not matched:
                lord_mismatches.append(
                    {
                        "cusp": index,
                        "field": field.replace("_match", ""),
                        "panchangbodh": {
                            "star_lord": star_lords[index - 1],
                            "sub_lord": sub_lords[index - 1],
                            "sub_sub_lord": sub_sub_lords[index - 1],
                        },
                        "local_vedicastro": {
                            "star_lord": actual["NakshatraLord"],
                            "sub_lord": actual["SubLord"],
                            "sub_sub_lord": actual["SubSubLord"],
                        },
                    }
                )
        rows.append(
            {
                "cusp": index,
                "panchangbodh_degree": expected["degree"],
                "local_vedicastro_degree": f"{actual['SignLonDMS']} {actual['Rasi']}",
                "arcsec_delta_local_minus_panchangbodh": delta,
                **comparisons,
            }
        )

    status = "within_tolerance" if max_abs_arcsec_delta <= 30 and not lord_mismatches else "mismatch_explained"
    return {
        "scope": "kp_12_cusp_local_replay_delta",
        "created_at": date.today().isoformat(),
        "packet_id": packet["packet_id"],
        "claim_status": "replay_delta_observation_only",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "source_packet": str(packet_path.relative_to(ROOT)),
        "local_replay_raw": str(local_raw_path.relative_to(ROOT)),
        "local_replay_raw_sha256": hashlib.sha256(local_raw_path.read_bytes()).hexdigest(),
        "status": status,
        "summary": {
            "row_count": len(rows),
            "max_abs_arcsec_delta": max_abs_arcsec_delta,
            "lord_mismatch_count": len(lord_mismatches),
            "degree_tolerance_arcsec": 30,
        },
        "lord_mismatches": lord_mismatches,
        "rows": rows,
        "raw_hash": hashlib.sha256(stable_json(rows).encode("utf-8")).hexdigest(),
        "boundary": (
            "Local replay uses VedicAstro/Krishnamurti/Placidus with inferred San Francisco "
            "timezone and coordinates. PanchangBodh screenshots do not visibly pin timezone, "
            "ayanamsa, or node mode. This delta can support replay readiness only; it cannot "
            "promote KP cusp data to final truth or timing/outcome oracle."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--local-raw", type=Path, default=DEFAULT_LOCAL_RAW)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    delta = build_delta(args.packet, args.local_raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(delta, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(delta, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
