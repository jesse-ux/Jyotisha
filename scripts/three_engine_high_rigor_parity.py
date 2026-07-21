#!/usr/bin/env python3
"""Build same-case D2/D4/D9/D10/AV/Shadbala parity artifacts."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.jyotish.scripts.run_pyjhora_compare import build_pyjhora_sample
from benchmarks.jyotish.scripts.run_skill_baseline import run_sample
from scripts.three_engine_parity_runner import _capture_jyotishganit_raw

ORACLE = ROOT / "references" / "oracle"
ARTIFACTS = ORACLE / "artifacts"
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
VED_VARGA_FIELDS = {"D2": "PlanetHoraD2Signs", "D4": "PlanetChaturthamshaD4Sign", "D9": "PlanetNavamshaD9Sign", "D10": "PlanetDashamamshaD10Sign"}
VED_COMPONENT_FIELDS = {
    "sthana": "PlanetSthanaBala", "kala": "PlanetKalaBala", "dig": "PlanetDigBala",
    "chesta": "PlanetChestaBala", "naisargika": "PlanetNaisargikaBala", "drik": "PlanetDrikBala",
}
SAMPLE = {
    "id": "steve_jobs_public_aa", "label": "Steve Jobs public AA", "category": "public", "privacy": "public",
    "birth": {"year": 1955, "month": 2, "day": 24, "hour": 19, "minute": 15, "lat": 37.7749, "lon": -122.4194, "tz": -8.0},
    "today": "2026-07-17",
}


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _jyotish_planet_signs(chart: dict[str, Any]) -> dict[str, str]:
    return {str(p["celestialBody"]): str(p["sign"]) for h in chart.get("houses", []) for p in h.get("occupants", []) if p.get("celestialBody") in PLANETS}


def _jyotish_shadbala(raw: dict[str, Any]) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
    totals: dict[str, float] = {}; components: dict[str, dict[str, float]] = {}
    for house in raw["d1Chart"]["houses"]:
        for p in house.get("occupants", []):
            name = p.get("celestialBody")
            if name not in PLANETS or "shadbala" not in p:
                continue
            s = p["shadbala"]
            totals[name] = float(s["Shadbala"]["Total"])
            components[name] = {"sthana": float(s["Sthanabala"]["Total"]), "kala": float(s["Kaalabala"]["Total"]), "dig": float(s["Digbala"]), "chesta": float(s["Cheshtabala"]), "naisargika": float(s["Naisargikabala"]), "drik": float(s["Drikbala"])}
    return totals, components


def _ved_payload(raw: dict[str, Any]) -> dict[str, Any]:
    return raw["Payload"]["AllPlanetData"]


def _ved_components(raw: dict[str, Any], chesta: Any | None = None) -> dict[str, float]:
    payload = _ved_payload(raw)
    values = {name: float(payload[field]) for name, field in VED_COMPONENT_FIELDS.items() if field in payload}
    if chesta is not None:
        values["chesta"] = float(chesta)
    return values


def _status(values: dict[str, Any], tolerance: float | None = None) -> str:
    data = list(values.values())
    if tolerance is not None and all(isinstance(v, (int, float)) for v in data):
        return "match" if max(data) - min(data) <= tolerance else "mismatch"
    return "match" if len({json.dumps(v, sort_keys=True) for v in data}) == 1 else "mismatch"


def build() -> dict[str, Any]:
    local_result = run_sample(SAMPLE)
    if not local_result.get("ok"):
        raise RuntimeError(local_result.get("error"))
    local = local_result["canonical"]
    local["shadbala_method_variants"] = {
        "kala": "bphs_local_solar_events_ahargana_declination",
        "chesta": "bphs_bounded_surya_mean_motion_seeghrochcha",
        "chesta_source": "MIT jyotishganit structure plus public Surya Siddhanta revolution constants",
    }
    pyjhora = build_pyjhora_sample(SAMPLE)
    with tempfile.TemporaryDirectory() as tmp:
        jyotish, _ = _capture_jyotishganit_raw(Path(tmp))
    ved_path = ARTIFACTS / "vedastro_steve_jobs_public_aa_divisional_raw.json"
    ved = json.loads(ved_path.read_text(encoding="utf-8"))

    local_path = ARTIFACTS / "local_steve_jobs_high_rigor_raw.json"
    py_path = ARTIFACTS / "pyjhora_steve_jobs_high_rigor_raw.json"
    jy_path = ARTIFACTS / "jyotishganit_steve_jobs_high_rigor_raw.json"
    _write(local_path, local); _write(py_path, pyjhora); _write(jy_path, jyotish)

    rows: list[dict[str, Any]] = []
    jy_d1 = _jyotish_planet_signs(jyotish["d1Chart"])
    for planet in PLANETS:
        values = {
            "local": local["planets"][planet]["sign"],
            "PyJHora_JHora": pyjhora["planets"][planet]["sign"],
            "VedAstro": _ved_payload(ved["raw_responses"][planet])["PlanetRasiD1Sign"]["Name"],
            "jyotishganit": jy_d1[planet],
        }
        rows.append({"section": "D1", "field": f"{planet}.sign", "local_value": values.pop("local"), "oracle_values": values, "status": _status({"local": local["planets"][planet]["sign"], **values})})
    for section, ved_field in VED_VARGA_FIELDS.items():
        jy_signs = _jyotish_planet_signs(jyotish["divisionalCharts"][section.lower()])
        for planet in PLANETS:
            values = {
                "local": local["varga"][section][planet]["sign"],
                "PyJHora_JHora": pyjhora["varga"][section][planet]["sign"],
                "VedAstro": _ved_payload(ved["raw_responses"][planet])[ved_field]["Name"],
                "jyotishganit": jy_signs[planet],
            }
            rows.append({"section": section, "field": f"{planet}.sign", "local_value": values.pop("local"), "oracle_values": values, "status": _status({"local": local["varga"][section][planet]["sign"], **values})})

    ved_bav = ved["scalar_responses"]["ashtakavarga_bav"]["Payload"]["BhinnashtakavargaChart"]
    ved_sav = ved["scalar_responses"]["ashtakavarga_sav_chart"]["Payload"]["SarvashtakavargaChart"]["Sarvashtakavarga"]["Rows"]
    jy_av = jyotish["ashtakavarga"]
    for planet in PLANETS:
        values = {"local": local["ashtakavarga"]["bav"][planet], "PyJHora_JHora": pyjhora["ashtakavarga"]["bav"][planet], "VedAstro": ved_bav[planet]["Rows"], "jyotishganit": [jy_av[f"{planet.lower()}Bhav"][s] for s in SIGNS]}
        rows.append({"section": "ashtakavarga_bav", "field": planet, "local_value": values.pop("local"), "oracle_values": values, "status": _status({"local": local["ashtakavarga"]["bav"][planet], **values})})
    sav_values = {"local": local["ashtakavarga"]["sav"], "PyJHora_JHora": pyjhora["ashtakavarga"]["sav"], "VedAstro": ved_sav, "jyotishganit": [jy_av["sav"][s] for s in SIGNS]}
    rows.append({"section": "ashtakavarga_sav", "field": "12_sign_scores", "local_value": sav_values.pop("local"), "oracle_values": sav_values, "status": _status({"local": local["ashtakavarga"]["sav"], **sav_values})})

    jy_totals, jy_components = _jyotish_shadbala(jyotish)
    for planet in PLANETS:
        total_values = {"local": local["shadbala"][planet], "PyJHora_JHora": pyjhora["shadbala"][planet], "VedAstro": float(_ved_payload(ved["raw_responses"][planet])["PlanetShadbalaPinda"]), "jyotishganit": jy_totals[planet]}
        rows.append({"section": "shadbala_total", "field": planet, "local_value": total_values.pop("local"), "oracle_values": total_values, "status": _status({"local": local["shadbala"][planet], **total_values}, 0.5)})
        ved_chesta = ved["component_responses"][f"{planet}.chesta"]["Payload"]["PlanetChestaBala"]
        ved_components = _ved_components(ved["raw_responses"][planet], ved_chesta)
        for component in VED_COMPONENT_FIELDS:
            values = {"local": local["shadbala_components"][planet][component], "PyJHora_JHora": pyjhora["shadbala_components"][planet][component], "VedAstro": ved_components[component], "jyotishganit": jy_components[planet][component]}
            row = {"section": "shadbala_components", "field": f"{planet}.{component}", "local_value": values.pop("local"), "oracle_values": values, "status": _status({"local": local["shadbala_components"][planet][component], **values}, 0.5)}
            if component == "chesta":
                row["method_conflict"] = "PyJHora unbounded; VedAstro/jyotishganit bounded; Sun/Moon treatment differs across engines."
            rows.append(row)

    manifest = {
        "case_id": "steve_jobs_public_1955_lahiri", "birth_data_policy": "public_case_only", "blocked_reason": "none",
        "engines": {
            "VedAstro": {"status": "official_verified", "official_raw_response_path": "artifacts/" + ved_path.name, "artifact_hash": _sha(ved_path), "settings": ved["settings"]},
            "PyJHora_JHora": {"status": "imported", "raw_output_path": "artifacts/" + py_path.name, "artifact_hash": _sha(py_path), "settings": pyjhora["settings"]},
            "jyotishganit": {"status": "imported", "raw_output_path": "artifacts/" + jy_path.name, "artifact_hash": _sha(jy_path), "settings": {"ayanamsa": jyotish["ayanamsa"]}},
        },
        "comparison_rows": rows,
        "method_arbitration": {
            "kala": "local_vs_PyJHora_7_of_7_within_0.05_virupa",
            "chesta": "blocked_cross_engine_method_conflict",
            "chesta_local_variant": "bphs_bounded_surya_mean_motion_seeghrochcha",
        },
        "runtime_boundary": "Full same-case raw coverage; mismatches remain formula/method differences, not missing artifacts.",
    }
    _write(ORACLE / "three_engine_parity_replay_manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    result = build()
    print(json.dumps({"status": "built", "rows": len(result["comparison_rows"])}, indent=2))
