#!/usr/bin/env python3
"""Capture a public same-chart parity packet without overstating oracle closure."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from domain_calculation_service import compute_chart


ROOT = Path(__file__).resolve().parents[1]
PYJHORA_ARTIFACT = ROOT / "references/oracle/artifacts/pyjhora_steve_jobs_dasha_stdout_20260627.txt"
JYOTISHGANIT_ROOT = ROOT / "references/open_source_sources/jyotishganit"

PUBLIC_CASE = {
    "case_id": "steve_jobs_public_1955_lahiri",
    "year": 1955,
    "month": 2,
    "day": 24,
    "hour": 19,
    "minute": 15,
    "second": 0,
    "lat": 37.7749,
    "lon": -122.4194,
    "tz": -8.0,
    "ayanamsa": "lahiri",
    "node_mode": "mean",
}


def _write_json(path: Path, value: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _capture_jyotishganit_raw(output_dir: Path) -> tuple[dict[str, Any], str]:
    sys.path.insert(0, str(JYOTISHGANIT_ROOT))
    try:
        from jyotishganit import calculate_birth_chart, get_birth_chart_json

        chart = calculate_birth_chart(
            datetime(
                PUBLIC_CASE["year"],
                PUBLIC_CASE["month"],
                PUBLIC_CASE["day"],
                PUBLIC_CASE["hour"],
                PUBLIC_CASE["minute"],
                PUBLIC_CASE["second"],
            ),
            PUBLIC_CASE["lat"],
            PUBLIC_CASE["lon"],
            PUBLIC_CASE["tz"],
            location_name="San Francisco, CA",
            name="Steve Jobs (public benchmark)",
        )
        raw = get_birth_chart_json(chart)
        path = _write_json(output_dir / "jyotishganit_raw.json", raw)
        return raw, str(path)
    except Exception as exc:
        return {"error": f"{exc.__class__.__name__}: {exc}"}, ""
    finally:
        try:
            sys.path.remove(str(JYOTISHGANIT_ROOT))
        except ValueError:
            pass


def _vedastro_state(*, allow_network: bool) -> dict[str, Any]:
    if not allow_network:
        return {
            "status": "blocked",
            "official_raw_response_path": "",
            "reason": "network_disabled_for_public_replay",
        }
    return {
        "status": "blocked",
        "official_raw_response_path": "",
        "reason": "official_runner_requires_explicit_raw_capture_workflow",
    }


def build_public_case_replay(*, output_dir: Path, allow_vedastro_network: bool = False) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    local = compute_chart(PUBLIC_CASE)
    jyotishganit_raw, jyotishganit_path = _capture_jyotishganit_raw(output_dir)
    pyjhora_available = PYJHORA_ARTIFACT.is_file()
    vedastro = _vedastro_state(allow_network=allow_vedastro_network)

    rows = [
        {
            "section": "D1",
            "field": "Sun.longitude",
            "local_value": local["planets"]["Sun"]["lon"],
            "oracle_values": {
                "VedAstro": None,
                "PyJHora_JHora": None,
                "jyotishganit": None,
            },
            "status": "blocked",
            "reason": "raw_values_not_normalized_across_all_three_engines",
        },
        {
            "section": "Panchanga",
            "field": "raw_capture",
            "local_value": None,
            "oracle_values": {
                "VedAstro": None,
                "PyJHora_JHora": "dasha_only_artifact",
                "jyotishganit": "captured" if jyotishganit_path else None,
            },
            "status": "not_comparable",
            "reason": "three_engine_scope_does_not_share_this_normalized_field",
        },
    ]
    report = {
        "case_id": PUBLIC_CASE["case_id"],
        "birth_data_policy": "public_case_only",
        "status": "partial" if pyjhora_available and jyotishganit_path else "blocked",
        "tested": False,
        "blocked_reason": "official_vedastro_raw_missing_or_unverified",
        "engines": {
            "VedAstro": vedastro,
            "PyJHora_JHora": {
                "status": "raw_imported" if pyjhora_available else "blocked",
                "raw_output_path": str(PYJHORA_ARTIFACT) if pyjhora_available else "",
                "settings": {"ayanamsa": "LAHIRI", "node_mode": "PyJHora default"},
            },
            "jyotishganit": {
                "status": "raw_captured" if jyotishganit_path else "blocked",
                "raw_output_path": jyotishganit_path,
                "error": jyotishganit_raw.get("error") if isinstance(jyotishganit_raw, dict) else None,
            },
        },
        "local": {
            "result_hash": local["result_hash"],
            "calculation_contract": local["calculation_contract"],
        },
        "comparison_rows": rows,
        "runtime_boundary": (
            "This packet has real public raw artifacts but remains unverified until a VedAstro "
            "official raw response and normalized three-engine field comparison are imported."
        ),
    }
    _write_json(output_dir / "three_engine_parity_replay.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="scratch/local/three_engine_parity")
    parser.add_argument("--allow-vedastro-network", action="store_true")
    args = parser.parse_args()
    report = build_public_case_replay(
        output_dir=ROOT / args.output_dir,
        allow_vedastro_network=args.allow_vedastro_network,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
