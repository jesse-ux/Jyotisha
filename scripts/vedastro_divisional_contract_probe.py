#!/usr/bin/env python3
"""Capture official VedAstro divisional-degree evidence without overclaiming chart parity."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.vedastro_contract_probe import _post
from scripts import varga


ROOT = Path(__file__).resolve().parents[1]
DIVISIONS = (2, 4, 9, 10)


def probe(*, total_degrees: float, timeout: float) -> dict[str, Any]:
    rows: dict[str, dict[str, Any]] = {}
    all_match = True
    for division in DIVISIONS:
        official = _post(
            "DivisionalLongitude",
            {"totalDegrees": total_degrees, "divisionalNo": division},
            timeout,
        )
        payload = official.get("payload") or {}
        value = (payload.get("DivisionalLongitude") or {}).get("TotalDegrees")
        local = varga.calc_varga(total_degrees, division)["degree_in_sign"]
        try:
            official_degree = float(value)
        except (TypeError, ValueError):
            official_degree = None
        matches_local = official.get("status") == "Pass" and official_degree == local
        all_match = all_match and matches_local
        rows[f"D{division}"] = {
            "official_status": official.get("status"),
            "official_degree": official_degree,
            "local_degree": local,
            "matches_local": matches_local,
            "request_body_hash": official.get("request_body_hash"),
            "response_payload_hash": official.get("response_payload_hash"),
            "raw_hash": official.get("raw_hash"),
        }
    return {
        "scope": "vedastro_divisional_degree_contract_probe",
        "input_total_degrees": total_degrees,
        "contract_status": "degree_mapping_verified" if all_match else "blocked",
        "chart_sign_contract": "blocked",
        "boundary": (
            "This probe validates only the divisional degree transformation. "
            "It does not establish complete D2/D4/D9/D10 sign, ayanamsa, node, "
            "timezone, or hosted-endpoint chart parity."
        ),
        "rows": rows,
        "privacy": {"api_key_persisted": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--total-degrees", type=float, default=3.5)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "references" / "oracle" / "artifacts" / "vedastro_divisional_degree_contract_probe.json",
    )
    args = parser.parse_args()
    report = probe(total_degrees=args.total_degrees, timeout=args.timeout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"contract_status": report["contract_status"], "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
