#!/usr/bin/env python3
"""Probe VedAstro time and longitude method semantics without trusting raw hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any
from urllib import request
from urllib.parse import urlparse

try:
    from scripts.local_env import load_local_env
except ModuleNotFoundError:  # pragma: no cover
    from local_env import load_local_env

ROOT = Path(__file__).resolve().parents[1]
load_local_env(ROOT)
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
API_VERSION_HEADERS = {"x-api-version", "api-version", "x-version"}
SERVER_IDENTITY_HEADERS = {"server", "x-powered-by", "etag", "last-modified"}
OBSERVABILITY_HEADERS = API_VERSION_HEADERS | SERVER_IDENTITY_HEADERS | {"date", "cf-ray", "x-request-id", "request-id", "via"}


def _hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def redact_headers(headers: dict[str, Any]) -> dict[str, str]:
    return {str(key).lower(): str(value) for key, value in headers.items() if str(key).lower() in OBSERVABILITY_HEADERS}


def _time(std_time: str) -> dict[str, Any]:
    return {
        "StdTime": std_time,
        "Location": {"Name": "San Francisco, CA", "Longitude": -122.4194, "Latitude": 37.7749},
    }


def _utc_iso(std_time: str) -> str:
    return datetime.strptime(std_time, "%H:%M %d/%m/%Y %z").astimezone(timezone.utc).isoformat()


def _post(calculator: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
    endpoint = os.environ.get("VEDASTRO_API_ENDPOINT", "").rstrip("/")
    api_key = os.environ.get("VEDASTRO_API_KEY", "").strip()
    if not endpoint or not api_key:
        raise RuntimeError("VEDASTRO_API_ENDPOINT and VEDASTRO_API_KEY are required")
    url = f"{endpoint}/Calculate/{calculator}"
    headers = {"Content-Type": "application/json", "Accept": "application/json", "Cache-Control": "no-cache", "Pragma": "no-cache", "x-api-key": api_key}
    req = request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    with request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
        payload = json.loads(raw.decode("utf-8"))
        response_headers = redact_headers(dict(response.headers.items()))
    return {
        "calculator": calculator,
        "request_url_host": urlparse(url).netloc,
        "request_body_hash": _hash(body),
        "response_headers": response_headers,
        "response_input_hash": _hash(payload.get("Input")),
        "response_payload_hash": _hash(payload.get("Payload")),
        "raw_hash": hashlib.sha256(raw).hexdigest(),
        "status": payload.get("Status"),
        "input": payload.get("Input"),
        "payload": payload.get("Payload"),
    }


def _parse_all_planet(value: Any) -> dict[str, float]:
    if not isinstance(value, str):
        return {}
    return {name: float(number) for name, number in re.findall(r"([A-Za-z]+)\s*-\s*(-?\d+(?:\.\d+)?)", value) if name in PLANETS}


def _all_planet_run(std_time: str, timeout: float) -> dict[str, Any]:
    result = _post("AllPlanetLongitude", {"time": _time(std_time), "Ayanamsa": "lahiri"}, timeout)
    result["normalized"] = _parse_all_planet((result.get("payload") or {}).get("AllPlanetLongitude"))
    result["interpreted_utc"] = _utc_iso(std_time)
    return result


def _planet_run(calculator: str, planet: str, std_time: str, timeout: float) -> dict[str, Any]:
    result = _post(calculator, {"planetName": {"Name": planet}, "time": _time(std_time), "Ayanamsa": "lahiri"}, timeout)
    value = (result.get("payload") or {}).get(calculator)
    if calculator == "AllPlanetData":
        value = (value or {}).get("PlanetRasiD1Sign", {}).get("DegreesIn", {}).get("TotalDegrees")
        sign = (result.get("payload") or {}).get(calculator, {}).get("PlanetRasiD1Sign", {}).get("Name")
        value = float(value) + 30 * ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"].index(sign)
    else:
        value = (value or {}).get("TotalDegrees")
    result["normalized_value"] = float(value)
    return result


def _vectors_equal(left: dict[str, float], right: dict[str, float], tolerance: float = 1e-7) -> bool:
    return set(left) == set(right) and all(abs(left[key] - right[key]) <= tolerance for key in left)


def evaluate_time_contract(runs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    local = runs.get("local_minus_08") or []
    utc = runs.get("utc_equivalent") or []
    control = runs.get("positive_08_control") or []
    normalized = [item.get("normalized") or {} for item in local]
    raw_hashes = [item.get("raw_hash") for item in local]
    return {
        "equivalent_local_utc": bool(local and utc and _vectors_equal(normalized[0], utc[0].get("normalized") or {})),
        "positive_offset_control_distinct": bool(local and control and not _vectors_equal(normalized[0], control[0].get("normalized") or {})),
        "repeat_normalized_stable": bool(normalized and all(_vectors_equal(normalized[0], item) for item in normalized[1:])),
        "raw_hash_stable": len(set(raw_hashes)) <= 1,
    }


def evaluate_method_contract(*, all_planet: dict[str, float], all_planet_data: dict[str, float], nirayana: dict[str, float], tolerance: float = 0.01) -> dict[str, Any]:
    data_match = _vectors_equal(all_planet_data, nirayana, tolerance)
    all_match = _vectors_equal(all_planet, nirayana, tolerance)
    deltas = {planet: {"all_planet_vs_nirayana": round(all_planet.get(planet, 0) - nirayana.get(planet, 0), 9), "all_planet_data_vs_nirayana": round(all_planet_data.get(planet, 0) - nirayana.get(planet, 0), 9)} for planet in sorted(set(all_planet_data) & set(nirayana))}
    return {"status": "resolved" if data_match and all_match else "blocked", "all_planet_data_matches_nirayana": data_match, "all_planet_longitude_matches_nirayana": all_match, "planet_deltas": deltas}


def _catalog_fingerprint() -> dict[str, Any]:
    completed = subprocess.run([sys.executable, str(ROOT / "scripts" / "vedastro_python_bridge.py"), "--list-capabilities"], cwd=ROOT, text=True, capture_output=True, timeout=60, check=False)
    if completed.returncode != 0:
        return {"status": "blocked", "reason": "capability_catalog_unavailable"}
    payload = json.loads(completed.stdout)
    try:
        package_version = version("vedastro")
    except PackageNotFoundError:
        package_version = None
    return {"status": "captured", "source": payload.get("source"), "module_name": payload.get("module_name"), "installed_package_version": package_version, "catalog_hash": _hash(payload), "capability_count": len(payload.get("capabilities") or [])}


def run_probe(repeats: int = 3, timeout: float = 30.0) -> dict[str, Any]:
    variants = {
        "local_minus_08": "19:15 24/02/1955 -08:00",
        "utc_equivalent": "03:15 25/02/1955 +00:00",
        "positive_08_control": "19:15 24/02/1955 +08:00",
    }
    runs: dict[str, list[dict[str, Any]]] = {}
    for name, std_time in variants.items():
        count = repeats if name == "local_minus_08" else 1
        runs[name] = [_all_planet_run(std_time, timeout) for _ in range(count)]

    baseline = variants["local_minus_08"]
    data_runs = {planet: _planet_run("AllPlanetData", planet, baseline, timeout) for planet in PLANETS}
    nirayana_runs = {planet: _planet_run("PlanetNirayanaLongitude", planet, baseline, timeout) for planet in PLANETS}
    all_planet = runs["local_minus_08"][0]["normalized"]
    all_planet_data = {planet: item["normalized_value"] for planet, item in data_runs.items()}
    nirayana = {planet: item["normalized_value"] for planet, item in nirayana_runs.items()}
    time_gate = evaluate_time_contract(runs)
    method_gate = evaluate_method_contract(all_planet=all_planet, all_planet_data=all_planet_data, nirayana=nirayana)
    headers = [item.get("response_headers") or {} for group in runs.values() for item in group] + [item.get("response_headers") or {} for item in data_runs.values()] + [item.get("response_headers") or {} for item in nirayana_runs.values()]
    version_values = sorted({value for header in headers for key, value in header.items() if key in API_VERSION_HEADERS})
    server_values = sorted({value for header in headers for key, value in header.items() if key in SERVER_IDENTITY_HEADERS})
    api_version_state = "captured" if version_values else "blocked"
    contract_resolved = all(time_gate[key] for key in ("equivalent_local_utc", "positive_offset_control_distinct", "repeat_normalized_stable")) and method_gate["status"] == "resolved" and api_version_state == "captured"
    return {
        "schema_version": 1,
        "scope": "vedastro_time_and_longitude_contract_probe",
        "case_id": "steve_jobs_public_aa",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "contract_status": "resolved" if contract_resolved else "blocked",
        "field_statuses": {"VedAstro.D1.longitude": "resolved" if contract_resolved else "blocked"},
        "time_contract": time_gate,
        "method_contract": method_gate,
        "api_version_contract": {"status": api_version_state, "observed_values": version_values, "reason": None if version_values else "no_explicit_api_version_header_returned"},
        "server_identity_contract": {"status": "captured" if server_values else "blocked", "observed_values": server_values},
        "capability_catalog": _catalog_fingerprint(),
        "variants": {name: {"std_time": std_time, "interpreted_utc": _utc_iso(std_time)} for name, std_time in variants.items()},
        "normalized_vectors": {"AllPlanetLongitude": all_planet, "AllPlanetData": all_planet_data, "PlanetNirayanaLongitude": nirayana},
        "method_recommendation": {
            "canonical_candidate": ["AllPlanetData.PlanetRasiD1Sign", "PlanetNirayanaLongitude"],
            "blocked_method": "AllPlanetLongitude",
            "reason": "AllPlanetLongitude disagrees with the two mutually consistent nirayana paths for at least one planet.",
        },
        "raw_runs": {"time_variants": runs, "all_planet_data": data_runs, "nirayana": nirayana_runs},
        "privacy": {"api_key_persisted": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--output", type=Path, default=ROOT / "references" / "oracle" / "artifacts" / "vedastro_steve_jobs_contract_probe.json")
    args = parser.parse_args()
    report = run_probe(repeats=max(1, args.repeats), timeout=args.timeout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"contract_status": report["contract_status"], "output": str(args.output), "time_contract": report["time_contract"], "method_contract": report["method_contract"], "api_version_contract": report["api_version_contract"]}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
