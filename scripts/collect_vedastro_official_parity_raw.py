#!/usr/bin/env python3
"""Collect bounded, secret-free VedAstro HTTP raw for divisional parity."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

try:
    from scripts import vedastro_service_adapter as adapter
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    import vedastro_service_adapter as adapter


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
VARGA_FIELDS = {
    "D2": "PlanetHoraD2Signs",
    "D4": "PlanetChaturthamshaD4Sign",
    "D9": "PlanetNavamshaD9Sign",
    "D10": "PlanetDashamamshaD10Sign",
}
SHADBALA_COMPONENT_FIELDS = [
    "PlanetSthanaBala",
    "PlanetDigBala",
    "PlanetKalaBala",
    "PlanetChestaBala",
    "PlanetNaisargikaBala",
    "PlanetDrikBala",
]


def _hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def collect_chart_core(
    case: dict[str, Any],
    *,
    case_id: str,
    planets: list[str],
    output_path: Path,
) -> dict[str, Any]:
    endpoint = os.environ.get("VEDASTRO_API_ENDPOINT", "").strip()
    if not endpoint:
        raise RuntimeError("VEDASTRO_API_ENDPOINT is not configured")

    manifest = adapter._official_full_snapshot_manifest(case, case_id)
    chart_request = next(item for item in manifest["requests"] if item["section"] == "chart_core")
    raw_responses: dict[str, Any] = {}
    statuses: dict[str, str] = {}
    scalar_responses: dict[str, Any] = {}
    scalar_statuses: dict[str, str] = {}
    component_responses: dict[str, Any] = {}
    component_statuses: dict[str, str] = {}
    retry_error_codes: list[int] = []
    attempt_count = 0

    for planet in planets:
        request_item = {**chart_request, "fanout_value": planet}
        try:
            payload, attempts, retries = adapter._post_official_snapshot_section(endpoint, request_item)
            raw_responses[planet] = payload
            statuses[planet] = adapter._payload_status(payload)
            attempt_count += attempts
            retry_error_codes.extend(retries)
        except Exception as exc:  # Preserve partial raw instead of discarding the batch.
            statuses[planet] = f"{type(exc).__name__}:{str(exc)[:200]}"

    common_body = adapter._official_common_body(case)
    scalar_requests = {
        "shadbala": {
            "section": "shadbala",
            "endpoint_path": "/Calculate/AllPlanetStrength",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": common_body,
            "calculator_name": "AllPlanetStrength",
        },
        "ashtakavarga_sav": {
            "section": "ashtakavarga_sav",
            "endpoint_path": "/Calculate/AshtakvargaLifeMap",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": {"birthTime": common_body["time"], "Ayanamsa": common_body["Ayanamsa"]},
            "calculator_name": "AshtakvargaLifeMap",
        },
        "ashtakavarga_bav": {
            "section": "ashtakavarga_bav",
            "endpoint_path": "/Calculate/BhinnashtakavargaChart",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": {"birthTime": common_body["time"], "Ayanamsa": common_body["Ayanamsa"]},
            "calculator_name": "BhinnashtakavargaChart",
        },
        "ashtakavarga_sav_chart": {
            "section": "ashtakavarga_sav_chart",
            "endpoint_path": "/Calculate/SarvashtakavargaChart",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": {"birthTime": common_body["time"], "Ayanamsa": common_body["Ayanamsa"]},
            "calculator_name": "SarvashtakavargaChart",
        },
    }
    for section, request_item in scalar_requests.items():
        try:
            payload, attempts, retries = adapter._post_official_snapshot_section(endpoint, request_item)
            scalar_responses[section] = payload
            scalar_statuses[section] = adapter._payload_status(payload)
            attempt_count += attempts
            retry_error_codes.extend(retries)
        except Exception as exc:
            scalar_statuses[section] = f"{type(exc).__name__}:{str(exc)[:200]}"

    for planet in planets:
        key = f"{planet}.chesta"
        request_item = {
            "section": "shadbala_chesta",
            "endpoint_path": "/Calculate/PlanetChestaBala",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": {
                "planetName": {"Name": planet},
                "time": common_body["time"],
                "useSpecialSunMoon": False,
                "Ayanamsa": common_body["Ayanamsa"],
            },
            "calculator_name": "PlanetChestaBala",
        }
        try:
            payload, attempts, retries = adapter._post_official_snapshot_section(endpoint, request_item)
            component_responses[key] = payload
            component_statuses[key] = adapter._payload_status(payload)
            attempt_count += attempts
            retry_error_codes.extend(retries)
        except Exception as exc:
            component_statuses[key] = f"{type(exc).__name__}:{str(exc)[:200]}"

    settings = {
        "case_id": case_id,
        "birth": {key: case.get(key) for key in ("year", "month", "day", "hour", "minute", "second", "lat", "lon", "tz")},
        "ayanamsa_policy": case.get("ayanamsa_policy") or case.get("ayanamsa") or "lahiri",
        "node_policy": case.get("node_policy") or case.get("node_mode") or "mean",
        "endpoint_host": adapter._endpoint_host(endpoint),
        "calculator": "AllPlanetData",
        "planets": planets,
    }
    packet = {
        "scope": "vedastro_official_http_divisional_parity_raw",
        "status": "ok"
        if statuses and scalar_statuses and component_statuses and all(value == "ok" for value in [*statuses.values(), *scalar_statuses.values(), *component_statuses.values()])
        else "partial",
        "source": "vedastro_official_http",
        "settings": settings,
        "coverage": {
            "sections": [
                *VARGA_FIELDS,
                "shadbala_total",
                "shadbala_components",
                "ashtakavarga_bav",
                "ashtakavarga_sav",
            ],
            "field_map": VARGA_FIELDS,
            "shadbala_component_fields": SHADBALA_COMPONENT_FIELDS,
            "blocked_sections": [],
        },
        "fanout_statuses": dict(sorted(statuses.items())),
        "scalar_statuses": dict(sorted(scalar_statuses.items())),
        "component_statuses": dict(sorted(component_statuses.items())),
        "attempt_count": attempt_count,
        "retry_error_codes": retry_error_codes,
        "raw_responses": raw_responses,
        "scalar_responses": scalar_responses,
        "component_responses": component_responses,
    }
    packet["response_hash"] = _hash({"chart_core": raw_responses, "scalar": scalar_responses, "components": component_responses})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return packet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=sorted(adapter.PARITY_CASES), default="beijing_first_use_demo")
    parser.add_argument("--planets", default=",".join(DEFAULT_PLANETS))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    planets = [item.strip() for item in args.planets.split(",") if item.strip()]
    output = args.output or ROOT / "references" / "oracle" / "artifacts" / f"vedastro_{args.case}_divisional_raw.json"
    report = collect_chart_core(
        dict(adapter.PARITY_CASES[args.case]),
        case_id=args.case,
        planets=planets,
        output_path=output,
    )
    print(json.dumps({"status": report["status"], "output": str(output), "response_hash": report["response_hash"], "fanout_statuses": report["fanout_statuses"]}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
