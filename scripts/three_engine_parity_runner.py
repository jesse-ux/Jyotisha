#!/usr/bin/env python3
"""Capture a public same-chart parity packet without overstating oracle closure."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from domain_calculation_service import compute_chart


ROOT = Path(__file__).resolve().parents[1]
PYJHORA_ARTIFACT = ROOT / "references/oracle/artifacts/pyjhora_steve_jobs_dasha_stdout_20260627.txt"
JYOTISHGANIT_ROOT = ROOT / "references/open_source_sources/jyotishganit"
VEDASTRO_ARTIFACT_DIR = ROOT / "scratch/local/vedastro_adapter"

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
PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
LONGITUDE_TOLERANCE_DEGREES = 0.02


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


def _capture_pyjhora_structured_d1(output_dir: Path) -> tuple[dict[str, Any], str]:
    try:
        import contextlib
        import importlib
        import io

        with contextlib.redirect_stdout(io.StringIO()):
            utils = importlib.import_module("jhora.utils")
            charts = importlib.import_module("jhora.horoscope.chart.charts")
            drik = importlib.import_module("jhora.panchanga.drik")

        jd = utils.julian_day_number(
            (PUBLIC_CASE["year"], PUBLIC_CASE["month"], PUBLIC_CASE["day"]),
            (PUBLIC_CASE["hour"], PUBLIC_CASE["minute"], PUBLIC_CASE["second"]),
        )
        drik.set_ayanamsa_mode("LAHIRI", jd=jd)
        place = drik.Place("San Francisco, CA", PUBLIC_CASE["lat"], PUBLIC_CASE["lon"], PUBLIC_CASE["tz"])
        with contextlib.redirect_stdout(io.StringIO()):
            raw = charts.rasi_chart(jd, place)
        index_to_planet = {0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury", 4: "Jupiter", 5: "Venus", 6: "Saturn"}
        planets: dict[str, dict[str, float | str]] = {}
        for body, position in raw:
            if body not in index_to_planet:
                continue
            sign_index, degree = position
            planets[index_to_planet[body]] = {
                "sign": SIGNS[int(sign_index)],
                "longitude": int(sign_index) * 30 + float(degree),
            }
        payload = {
            "source": "PyJHora.jhora.horoscope.chart.charts.rasi_chart",
            "settings": {"ayanamsa": "LAHIRI", "jd_input": "local_birth_time", "node_mode": "PyJHora default"},
            "raw": raw,
            "planets": planets,
        }
        path = _write_json(output_dir / "pyjhora_structured_d1.json", payload)
        return payload, str(path)
    except Exception as exc:
        return {"error": f"{exc.__class__.__name__}: {exc}"}, ""


def _vedastro_state(*, allow_network: bool) -> dict[str, Any]:
    if not allow_network:
        return {
            "status": "blocked",
            "official_raw_response_path": "",
            "reason": "network_disabled_for_public_replay",
        }
    artifact = _latest_vedastro_official_raw_artifact()
    if artifact:
        return {
            "status": "official_verified",
            "official_raw_response_path": str(artifact),
            "artifact_hash": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            "settings": {"ayanamsa": PUBLIC_CASE["ayanamsa"], "node_mode": PUBLIC_CASE["node_mode"]},
            "reason": "imported_latest_official_full_snapshot_artifact",
        }
    return {
        "status": "blocked",
        "official_raw_response_path": "",
        "reason": "official_runner_requires_explicit_raw_capture_workflow",
    }


def _latest_vedastro_official_raw_artifact() -> Path | None:
    if not VEDASTRO_ARTIFACT_DIR.exists():
        return None
    candidates: list[Path] = []
    for path in VEDASTRO_ARTIFACT_DIR.glob("official_full_snapshot-*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        raw = payload.get("official_raw_response") or payload.get("raw_response")
        source = str(raw.get("source") or "") if isinstance(raw, dict) else ""
        if (
            payload.get("status") == "ok"
            and source.startswith("vedastro_official")
            and _artifact_matches_public_case(payload)
        ):
            candidates.append(path)
    if not candidates:
        return None
    return max(candidates, key=lambda item: item.stat().st_mtime)


def _artifact_matches_public_case(payload: dict[str, Any]) -> bool:
    manifest = payload.get("request_manifest") if isinstance(payload.get("request_manifest"), dict) else {}
    text = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
    return (
        "24/02/1955" in text
        and "19:15" in text
        and "37.7749" in text
        and "-122.4194" in text
    )


def _load_vedastro_artifact(path: str) -> dict[str, Any]:
    if not path:
        return {}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _vedastro_d1(artifact: dict[str, Any], planet: str) -> dict[str, Any]:
    try:
        payload = artifact["snapshot_sections"]["chart_core"][planet]["Payload"]["AllPlanetData"]
        return {
            "sign": payload["PlanetRasiD1Sign"]["Name"],
            "longitude": float(payload["PlanetNirayanaLongitude"]["TotalDegrees"]),
        }
    except (KeyError, TypeError, ValueError):
        return {}


def _jyotishganit_d1(raw: dict[str, Any], planet: str) -> dict[str, Any]:
    for house in (raw.get("d1Chart") or {}).get("houses") or []:
        for occupant in house.get("occupants") or []:
            if occupant.get("celestialBody") != planet:
                continue
            sign = occupant.get("sign")
            degree = occupant.get("signDegrees")
            if sign not in SIGNS or degree is None:
                return {}
            return {"sign": sign, "longitude": SIGNS.index(sign) * 30 + float(degree)}
    return {}


def _pyjhora_d1(raw: dict[str, Any], planet: str) -> dict[str, Any]:
    value = raw.get("planets", {}).get(planet)
    return value if isinstance(value, dict) else {}


def _d1_comparison_rows(
    local: dict[str, Any],
    vedastro_artifact: dict[str, Any],
    jyotishganit_raw: dict[str, Any],
    pyjhora_raw: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for planet in PLANETS:
        local_planet = local.get("planets", {}).get(planet) or {}
        vedastro = _vedastro_d1(vedastro_artifact, planet)
        jyotishganit = _jyotishganit_d1(jyotishganit_raw, planet)
        pyjhora = _pyjhora_d1(pyjhora_raw, planet)
        local_sign = local_planet.get("sign")
        sign_values = {
            "VedAstro": vedastro.get("sign"),
            "PyJHora_JHora": pyjhora.get("sign"),
            "jyotishganit": jyotishganit.get("sign"),
        }
        comparable_signs = [value for value in sign_values.values() if value is not None]
        rows.append({
            "section": "D1",
            "field": f"{planet}.sign",
            "local_value": local_sign,
            "oracle_values": sign_values,
            "status": (
                "match"
                if local_sign and comparable_signs and all(value == local_sign for value in comparable_signs)
                else "blocked" if not comparable_signs else "mismatch"
            ),
        })

        local_lon = local_planet.get("lon")
        longitude_values = {
            "VedAstro": vedastro.get("longitude"),
            "PyJHora_JHora": pyjhora.get("longitude"),
            "jyotishganit": jyotishganit.get("longitude"),
        }
        comparable = [value for value in longitude_values.values() if isinstance(value, (int, float))]
        rows.append({
            "section": "D1",
            "field": f"{planet}.longitude",
            "local_value": local_lon,
            "oracle_values": longitude_values,
            "status": (
                "match"
                if isinstance(local_lon, (int, float))
                and comparable
                and all(abs(value - local_lon) <= LONGITUDE_TOLERANCE_DEGREES for value in comparable)
                else "blocked" if not comparable else "mismatch"
            ),
        })
    return rows


def build_public_case_replay(*, output_dir: Path, allow_vedastro_network: bool = False) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    local = compute_chart(PUBLIC_CASE)
    jyotishganit_raw, jyotishganit_path = _capture_jyotishganit_raw(output_dir)
    pyjhora_raw, pyjhora_path = _capture_pyjhora_structured_d1(output_dir)
    pyjhora_available = PYJHORA_ARTIFACT.is_file()
    vedastro = _vedastro_state(allow_network=allow_vedastro_network)
    vedastro_artifact = _load_vedastro_artifact(vedastro.get("official_raw_response_path", ""))
    rows = _d1_comparison_rows(local, vedastro_artifact, jyotishganit_raw, pyjhora_raw) + [
        {
            "section": "Panchanga",
            "field": "raw_capture",
            "local_value": None,
            "oracle_values": {
                "VedAstro": None,
                "PyJHora_JHora": "structured_d1_captured" if pyjhora_path else "dasha_only_artifact",
                "jyotishganit": "captured" if jyotishganit_path else None,
            },
            "status": "not_comparable",
            "reason": "three_engine_scope_does_not_share_this_normalized_field",
        },
    ]
    has_blocked = any(row.get("status") == "blocked" for row in rows)
    has_mismatch = any(row.get("status") == "mismatch" for row in rows)
    has_required_raw = vedastro.get("status") == "official_verified" and bool(pyjhora_path) and bool(jyotishganit_path)
    blocked_reason = (
        "official_vedastro_raw_missing_or_unverified"
        if vedastro.get("status") != "official_verified"
        else "some_comparison_rows_blocked"
        if has_blocked
        else "comparison_rows_mismatch"
        if has_mismatch
        else "none"
    )
    report_status = (
        "blocked"
        if not bool(jyotishganit_path)
        else "mismatch"
        if has_mismatch
        else "partial"
        if not has_required_raw or has_blocked
        else "pass"
    )
    pyjhora_artifact_path = pyjhora_path or (str(PYJHORA_ARTIFACT) if pyjhora_available else "")
    report = {
        "case_id": PUBLIC_CASE["case_id"],
        "birth_data_policy": "public_case_only",
        "status": report_status,
        "tested": vedastro.get("status") == "official_verified" and bool(rows),
        "blocked_reason": blocked_reason,
        "engines": {
            "VedAstro": vedastro,
            "PyJHora_JHora": {
                "status": "structured_captured" if pyjhora_path else "raw_imported" if pyjhora_available else "blocked",
                "raw_output_path": pyjhora_artifact_path,
                "artifact_hash": hashlib.sha256(Path(pyjhora_artifact_path).read_bytes()).hexdigest() if pyjhora_artifact_path else "",
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
            "This packet has real public raw artifacts and may include VedAstro official raw evidence, "
            "and normalized D1 planet sign/longitude parity is tested. Non-D1 scopes still require separate gates."
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
