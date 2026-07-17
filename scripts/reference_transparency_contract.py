#!/usr/bin/env python3
"""User-visible disclosure for timing, engine observations, and public case references."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from scripts.domain_calculation_service import compute_chart, compute_transit_longitude, compute_vimshottari_timeline
    from scripts.timing_precision_contract import build_timing_precision_contract
    from scripts.varga import SIGNS, SIGN_LORDS, calc_varga
    from scripts.dasha_analyzer import build_antardasha
    from scripts.narayana_dasha import narayana_dasha_full_report
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from domain_calculation_service import compute_chart, compute_transit_longitude, compute_vimshottari_timeline
    from timing_precision_contract import build_timing_precision_contract
    from varga import SIGNS, SIGN_LORDS, calc_varga
    from dasha_analyzer import build_antardasha
    from narayana_dasha import narayana_dasha_full_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "references" / "real_case_calibration" / "replay_manifest.json"
DEFAULT_CONTEXT_MANIFEST = ROOT / "references" / "real_case_calibration" / "public_context_manifest.json"
DOMAIN_HOUSES = {
    "career": "house_10",
    "marriage": "house_7",
    "wealth": "house_2",
    "health": "house_6",
}
FEATURE_WEIGHTS = {
    "ascendant": 0.35,
    "moon_sign": 0.30,
    "domain_lord_sign": 0.25,
    "node_axis": 0.10,
    "d9_ascendant": 0.10,
    "d9_venus": 0.10,
    "d10_ascendant": 0.10,
    "d10_sun": 0.10,
    "vimshottari_mahadasha": 0.15,
    "vimshottari_antardasha": 0.10,
    "narayana_mahadasha_sign": 0.10,
    "narayana_antardasha_sign": 0.10,
    "jupiter_transit_house": 0.10,
    "saturn_transit_house": 0.10,
}
HIGH_SIMILARITY_THRESHOLD = 0.75


def _sign(chart: dict[str, Any], planet: str) -> str | None:
    planets = chart.get("planets") if isinstance(chart, dict) else None
    value = planets.get(planet) if isinstance(planets, dict) else None
    return value.get("sign") if isinstance(value, dict) else None


def _domain_lord_sign(chart: dict[str, Any], domain: str) -> str | None:
    house = DOMAIN_HOUSES.get(domain)
    houses = chart.get("houses") if isinstance(chart, dict) else None
    house_index = int(house.split("_", 1)[1]) if house else None
    house_value = None
    if isinstance(houses, dict) and house:
        house_value = houses.get(house)
        if house_value is None and house_index is not None:
            house_value = houses.get(house_index) or houses.get(str(house_index))
    lord = house_value.get("lord") if isinstance(house_value, dict) else None
    if not isinstance(lord, str) and isinstance(house_value, dict):
        lord = SIGN_LORDS.get(house_value.get("sign") or house_value.get("cusp_sign"))
    return _sign(chart, lord) if isinstance(lord, str) else None


def _longitude(chart: dict[str, Any], key: str) -> float | None:
    if key == "Ascendant":
        value = chart.get("ascendant") if isinstance(chart, dict) else None
    else:
        planets = chart.get("planets") if isinstance(chart, dict) else None
        value = planets.get(key) if isinstance(planets, dict) else None
    if not isinstance(value, dict):
        return None
    try:
        return float(value["lon"])
    except (KeyError, TypeError, ValueError):
        return None


def _varga_sign(chart: dict[str, Any], key: str, division: int) -> str | None:
    longitude = _longitude(chart, key)
    return calc_varga(longitude, division)["sign"] if longitude is not None else None


def _birth_datetime(chart: dict[str, Any]) -> datetime | None:
    birth = chart.get("birth_info") if isinstance(chart, dict) else None
    if not isinstance(birth, dict):
        birth = chart.get("birth") if isinstance(chart, dict) else None
    if not isinstance(birth, dict) or not isinstance(birth.get("date"), str):
        return None
    raw_time = birth.get("time")
    if not isinstance(raw_time, str):
        raw_time = f"{int(birth.get('hour', 0)):02d}:{int(birth.get('minute', 0)):02d}:{int(birth.get('second', 0)):02d}"
    try:
        return datetime.fromisoformat(f"{birth['date']}T{raw_time}")
    except ValueError:
        return None


def _vimshottari_state(chart: dict[str, Any], reference_date: str | None) -> dict[str, str] | None:
    if not isinstance(reference_date, str):
        return None
    try:
        target = datetime.fromisoformat(reference_date[:10])
    except ValueError:
        return None
    birth_dt, moon_lon = _birth_datetime(chart), _longitude(chart, "Moon")
    if birth_dt is None or moon_lon is None:
        return None
    try:
        periods = compute_vimshottari_timeline(birth_dt=birth_dt, moon_lon=moon_lon)["periods"]
        for period in periods:
            start = datetime.fromisoformat(period["start"])
            end = datetime.fromisoformat(period["end"])
            if start <= target <= end:
                antardashas = build_antardasha({"lord": period["lord"], "start": start, "end": end})
                antardasha = next(
                    (item["lord"] for item in antardashas if item["start"] <= target <= item["end"]),
                    None,
                )
                return {"mahadasha": period["lord"], "antardasha": antardasha}
    except (KeyError, TypeError, ValueError):
        return None
    return None


def _narayana_state(chart: dict[str, Any], reference_date: str | None) -> dict[str, str] | None:
    if not isinstance(reference_date, str):
        return None
    try:
        target = datetime.fromisoformat(reference_date[:10])
    except ValueError:
        return None
    birth_dt = _birth_datetime(chart)
    ascendant = chart.get("ascendant") if isinstance(chart, dict) else None
    asc_sign = ascendant.get("sign") if isinstance(ascendant, dict) else None
    planets = chart.get("planets") if isinstance(chart, dict) else None
    if birth_dt is None or asc_sign not in SIGNS or not isinstance(planets, dict):
        return None
    try:
        planet_lons = {name: float(value["lon"]) for name, value in planets.items() if isinstance(value, dict) and value.get("lon") is not None}
        if not planet_lons:
            return None
        age = (target - birth_dt).total_seconds() / (365.25 * 86400)
        if age <= 0:
            return None
        current = narayana_dasha_full_report(
            lagna_sign_idx=SIGNS.index(asc_sign),
            planet_lons=planet_lons,
            current_age=age,
            birth_year=birth_dt.year,
        ).get("current_dasha", {})
        md, ad = current.get("md"), current.get("ad")
        if not isinstance(md, dict) or not isinstance(ad, dict):
            return None
        return {"mahadasha_sign": md.get("sign"), "antardasha_sign": ad.get("sign")}
    except (KeyError, TypeError, ValueError):
        return None


def _timezone_offset(chart: dict[str, Any]) -> float | None:
    birth = chart.get("birth_info") if isinstance(chart, dict) else None
    if not isinstance(birth, dict):
        birth = chart.get("birth") if isinstance(chart, dict) else None
    raw = birth.get("tz") if isinstance(birth, dict) else None
    try:
        return float(str(raw).replace("UTC", ""))
    except (TypeError, ValueError):
        return None


@lru_cache(maxsize=256)
def _transit_sign_index(planet: str, reference_date: str, tz: float, ayanamsa: str) -> int | None:
    try:
        longitude = compute_transit_longitude(
            planet=planet,
            reference_date=reference_date,
            tz=tz,
            ayanamsa=ayanamsa,
        )["longitude"]
        return int(float(longitude) / 30) % 12
    except (KeyError, TypeError, ValueError):
        return None


def _transit_state(chart: dict[str, Any], reference_date: str | None) -> dict[str, Any] | None:
    if not isinstance(reference_date, str):
        return None
    try:
        datetime.strptime(reference_date[:10], "%Y-%m-%d")
    except ValueError:
        return None
    ascendant = chart.get("ascendant") if isinstance(chart, dict) else None
    asc_sign = ascendant.get("sign") if isinstance(ascendant, dict) else None
    tz = _timezone_offset(chart)
    if asc_sign not in SIGNS or tz is None:
        return None
    birth = chart.get("birth_info") if isinstance(chart, dict) else None
    if not isinstance(birth, dict):
        birth = chart.get("birth") if isinstance(chart, dict) else None
    ayanamsa = birth.get("ayanamsa_name", "lahiri") if isinstance(birth, dict) else "lahiri"
    asc_idx = SIGNS.index(asc_sign)
    jupiter = _transit_sign_index("Jupiter", reference_date[:10], tz, str(ayanamsa))
    saturn = _transit_sign_index("Saturn", reference_date[:10], tz, str(ayanamsa))
    if jupiter is None or saturn is None:
        return None
    return {
        "jupiter_transit_house": (jupiter - asc_idx) % 12 + 1,
        "saturn_transit_house": (saturn - asc_idx) % 12 + 1,
        "reference_date": reference_date[:10],
    }


def _features(chart: dict[str, Any], domain: str) -> dict[str, Any]:
    ascendant = chart.get("ascendant") if isinstance(chart, dict) else None
    rahu, ketu = _sign(chart, "Rahu"), _sign(chart, "Ketu")
    features = {
        "ascendant": ascendant.get("sign") if isinstance(ascendant, dict) else None,
        "moon_sign": _sign(chart, "Moon"),
        "domain_lord_sign": _domain_lord_sign(chart, domain),
        "node_axis": (rahu, ketu) if rahu is not None and ketu is not None else None,
    }
    if domain == "marriage":
        features.update({
            "d9_ascendant": _varga_sign(chart, "Ascendant", 9),
            "d9_venus": _varga_sign(chart, "Venus", 9),
        })
    elif domain == "career":
        features.update({
            "d10_ascendant": _varga_sign(chart, "Ascendant", 10),
            "d10_sun": _varga_sign(chart, "Sun", 10),
        })
    return features


@lru_cache(maxsize=64)
def _case_chart(case_id: str, year: int, month: int, day: int, hour: int, minute: int,
                lat: float, lon: float, tz: float, node_mode: str) -> dict[str, Any] | None:
    try:
        return compute_chart({
            "year": year, "month": month, "day": day, "hour": hour, "minute": minute,
            "lat": lat, "lon": lon, "tz": tz, "ayanamsa": "lahiri", "node_mode": node_mode,
        })
    except Exception:
        return None


def _chart_for_case(case: dict[str, Any]) -> dict[str, Any] | None:
    provided = case.get("chart")
    if isinstance(provided, dict):
        return provided
    subject = case.get("subject")
    if not isinstance(subject, dict):
        return None
    required = ("year", "month", "day", "hour", "minute", "lat", "lon", "tz")
    if any(subject.get(field) is None for field in required):
        return None
    return _case_chart(
        str(case.get("case_id", "")), int(subject["year"]), int(subject["month"]), int(subject["day"]),
        int(subject["hour"]), int(subject["minute"]), float(subject["lat"]), float(subject["lon"]),
        float(subject["tz"]), str(subject.get("node_mode", "mean")),
    )


def _similarity(
    user_chart: dict[str, Any], case_chart: dict[str, Any], domain: str,
    *, reference_date: str | None = None, case_event_date: str | None = None,
) -> dict[str, Any]:
    user = _features(user_chart, domain)
    candidate = _features(case_chart, domain)
    user_dasha = _vimshottari_state(user_chart, reference_date)
    case_dasha = _vimshottari_state(case_chart, case_event_date)
    user_narayana = _narayana_state(user_chart, reference_date)
    case_narayana = _narayana_state(case_chart, case_event_date)
    user_transit = _transit_state(user_chart, reference_date)
    case_transit = _transit_state(case_chart, case_event_date)
    if user_dasha is not None and case_dasha is not None:
        user["vimshottari_mahadasha"] = user_dasha["mahadasha"]
        candidate["vimshottari_mahadasha"] = case_dasha["mahadasha"]
        if user_dasha.get("antardasha") is not None and case_dasha.get("antardasha") is not None:
            user["vimshottari_antardasha"] = user_dasha["antardasha"]
            candidate["vimshottari_antardasha"] = case_dasha["antardasha"]
        md_matches = user_dasha["mahadasha"] == case_dasha["mahadasha"]
        ad_matches = user_dasha.get("antardasha") == case_dasha.get("antardasha")
        timing_state = {
            "status": "matched" if md_matches and ad_matches else "partial_match" if md_matches else "different",
            "user_vimshottari_mahadasha": user_dasha["mahadasha"],
            "case_event_vimshottari_mahadasha": case_dasha["mahadasha"],
            "user_vimshottari_antardasha": user_dasha.get("antardasha"),
            "case_event_vimshottari_antardasha": case_dasha.get("antardasha"),
            "reference_date": reference_date,
            "case_event_date": case_event_date,
        }
    else:
        timing_state = {"status": "not_compared"}
    if user_narayana is not None and case_narayana is not None:
        user["narayana_mahadasha_sign"] = user_narayana["mahadasha_sign"]
        candidate["narayana_mahadasha_sign"] = case_narayana["mahadasha_sign"]
        user["narayana_antardasha_sign"] = user_narayana["antardasha_sign"]
        candidate["narayana_antardasha_sign"] = case_narayana["antardasha_sign"]
        timing_state["narayana_status"] = (
            "matched"
            if user_narayana == case_narayana
            else "partial_match"
            if user_narayana["mahadasha_sign"] == case_narayana["mahadasha_sign"]
            else "different"
        )
        timing_state["user_narayana"] = user_narayana
        timing_state["case_event_narayana"] = case_narayana
    else:
        timing_state["narayana_status"] = "not_compared"
    if user_transit is not None and case_transit is not None:
        user["jupiter_transit_house"] = user_transit["jupiter_transit_house"]
        user["saturn_transit_house"] = user_transit["saturn_transit_house"]
        candidate["jupiter_transit_house"] = case_transit["jupiter_transit_house"]
        candidate["saturn_transit_house"] = case_transit["saturn_transit_house"]
        timing_state["transit_status"] = (
            "matched"
            if user_transit["jupiter_transit_house"] == case_transit["jupiter_transit_house"]
            and user_transit["saturn_transit_house"] == case_transit["saturn_transit_house"]
            else "partial_match"
            if user_transit["jupiter_transit_house"] == case_transit["jupiter_transit_house"]
            or user_transit["saturn_transit_house"] == case_transit["saturn_transit_house"]
            else "different"
        )
        timing_state["user_transit"] = user_transit
        timing_state["case_event_transit"] = case_transit
    else:
        timing_state["transit_status"] = "not_compared"
    matching, dissimilar, total = [], [], 0.0
    for name, weight in FEATURE_WEIGHTS.items():
        if name not in user or name not in candidate:
            continue
        if user[name] is None or candidate[name] is None:
            continue
        total += weight
        if user[name] == candidate[name]:
            matching.append(name)
        else:
            dissimilar.append(name)
    score = round(sum(FEATURE_WEIGHTS[name] for name in matching) / total, 3) if total else 0.0
    compared_vargas = []
    if domain == "marriage" and all(user.get(name) is not None and candidate.get(name) is not None for name in ("d9_ascendant", "d9_venus")):
        compared_vargas.append("D9")
    if domain == "career" and all(user.get(name) is not None and candidate.get(name) is not None for name in ("d10_ascendant", "d10_sun")):
        compared_vargas.append("D10")
    uncompared = []
    if timing_state["status"] == "not_compared":
        uncompared.insert(0, "vimshottari_mahadasha")
        uncompared.insert(1, "vimshottari_antardasha")
    if timing_state["narayana_status"] == "not_compared":
        uncompared.append("narayana_dasha")
    if timing_state["transit_status"] == "not_compared":
        uncompared.append("transit_event_state")
    if domain == "marriage" and "D9" not in compared_vargas:
        uncompared.insert(0, "D9")
    if domain == "career" and "D10" not in compared_vargas:
        uncompared.insert(0, "D10")
    return {
        "score": score,
        "matching_factors": matching,
        "dissimilar_factors": dissimilar,
        "feature_scope": "D1 ascendant, Moon, theme-house lord, Rahu/Ketu axis" + (f", {'/'.join(compared_vargas)}" if compared_vargas else "") + (", Vimshottari MD/AD" if timing_state["status"] != "not_compared" else "") + (", Narayana MD/AD" if timing_state["narayana_status"] != "not_compared" else "") + (", Jupiter/Saturn transit houses" if timing_state["transit_status"] != "not_compared" else ""),
        "uncompared_layers": uncompared,
        "timing_state": timing_state,
    }


def _load_cases(manifest_path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    cases = payload.get("cases") if isinstance(payload, dict) else None
    return [case for case in cases if isinstance(case, dict)] if isinstance(cases, list) else []


def _coverage(cases: list[dict[str, Any]], themes: list[str]) -> dict[str, list[str]]:
    domains: set[str] = set()
    for case in cases:
        replay = case.get("replay")
        if not isinstance(replay, dict):
            continue
        replay_status = replay.get("outcome_replay_status")
        if replay_status == "replayed" and replay.get("do_not_use_for_prediction") is not True:
            pass
        elif replay_status == "pending" and replay.get("do_not_use_for_prediction") is True:
            pass
        else:
            continue
        for event in case.get("event_outcomes", []):
            if isinstance(event, dict) and isinstance(event.get("domain"), str):
                domains.add(event["domain"])
    available = sorted(domains)
    return {
        "available_event_domains": available,
        "requested_uncovered_domains": sorted(set(themes) - domains),
    }


def select_similar_public_cases(
    user_chart: dict[str, Any],
    themes: list[str],
    *,
    cases: list[dict[str, Any]] | None = None,
    reference_date: str | None = None,
    threshold: float = HIGH_SIMILARITY_THRESHOLD,
    max_cases: int = 3,
) -> dict[str, Any]:
    candidates = cases if cases is not None else (
        _load_cases(DEFAULT_MANIFEST) + _load_cases(DEFAULT_CONTEXT_MANIFEST)
    )
    selected: list[dict[str, Any]] = []
    for case in candidates:
        replay = case.get("replay")
        if not isinstance(replay, dict):
            continue
        replay_status = replay.get("outcome_replay_status")
        if replay_status == "replayed" and replay.get("do_not_use_for_prediction") is not True:
            reference_status = "calibration_replayed"
        elif replay_status == "pending" and replay.get("do_not_use_for_prediction") is True:
            reference_status = "public_context_only"
        else:
            continue
        case_chart = _chart_for_case(case)
        if not isinstance(case_chart, dict):
            continue
        for event in case.get("event_outcomes", []):
            if not isinstance(event, dict) or event.get("domain") not in themes:
                continue
            similarity = _similarity(
                user_chart,
                case_chart,
                event["domain"],
                reference_date=reference_date,
                case_event_date=event.get("event_date"),
            )
            if similarity["score"] < threshold:
                continue
            source = case.get("source") if isinstance(case.get("source"), dict) else {}
            event_source = event.get("source") if isinstance(event.get("source"), dict) else {}
            subject = case.get("subject") if isinstance(case.get("subject"), dict) else {}
            selected.append({
                "case_id": case.get("case_id"),
                "subject": subject.get("name"),
                "domain": event.get("domain"),
                "event_type": event.get("event_type"),
                "event_date": event.get("event_date"),
                "outcome": event.get("outcome"),
                "case_source": {"url": source.get("url"), "source_grade": source.get("source_grade")},
                "event_source": {"url": event_source.get("url"), "source_grade": event_source.get("source_grade")},
                "similarity": similarity,
                "reference_only": True,
                "reference_status": reference_status,
                "difference_notice": "相似仅限列出的 D1 特征；未比较层不得推断为相同。",
            })
    selected.sort(key=lambda item: (-item["similarity"]["score"], item["case_id"] or ""))
    selected = selected[:max_cases]
    return {
        "status": "high_similarity_public_references_available" if selected else "no_high_similarity_public_reference",
        "cases": selected,
        "threshold": threshold,
        "manifest": [
            "references/real_case_calibration/replay_manifest.json",
            "references/real_case_calibration/public_context_manifest.json",
        ],
        "public_figures_only": True,
        "does_not_predict_user_outcome": True,
        "coverage": _coverage(candidates, themes),
        "boundary": "公开案例用于比较与理解，不表示用户会复现该事件。",
    }


def build_reference_transparency_contract(
    chart: dict[str, Any], themes: list[str], *, timing: dict[str, Any] | None = None,
    cases: list[dict[str, Any]] | None = None, reference_date: str | None = None,
) -> dict[str, Any]:
    timing_contract = build_timing_precision_contract(timing)
    return {
        "version": "transparent_reference_v1",
        "timing_display": {
            "claim_status": timing_contract["claim_status"],
            "verified_window": "display_with_evidence_scope",
            "candidate_windows": "display_with_signals_and_confidence_cap",
            "exact_triggers": "display_as_technical_trigger_not_guarantee",
            "boundary": timing_contract["boundary"],
        },
        "external_engine_observations": {
            "Local native": {"role": "primary_calculation", "source": "current request calculation contract"},
            "VedAstro hosted": {
                "role": "external_observation", "deployment_identity": "not_publicly_proven",
                "source": "references/oracle/vedastro_contract_arbitration_2026_07_17.json",
            },
            "Xalen": {"role": "formula_isolation_observation", "source": "references/oracle/xalen_fourth_oracle_comparison_2026_07_17.json"},
            "jyotishyamitra": {"role": "independent_observation", "source": "references/oracle/jyotishyamitra_steve_jobs_probe_2026_07_18.json"},
        },
        "method_variants": {
            "display": "show_parallel_methods_with_sources",
            "source": "references/oracle/xalen_formula_unit_attribution_2026_07_17.json",
            "boundary": "流派/公式差异并列展示；不以单一引擎多数投票决定真值。",
        },
        "similar_public_cases": select_similar_public_cases(
            chart,
            themes,
            cases=cases,
            reference_date=reference_date,
        ),
    }
