# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
# ─── How to run ───
# PYTHONPATH=scripts .venv/bin/python scripts/active_rectification_event_engine.py
"""Local chart and dual-Dasha computation for birth-time event scoring."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Final, assert_never

from scripts.active_rectification_events import (
    CandidateEvidence,
    CandidateResult,
    CandidateScoreRow,
    EventDomain,
    LifeEvent,
    RectificationEventRequest,
    adjudicate_candidate_rows,
    precision_weight,
)

SCRIPTS: Final = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import dasha_analyzer  # noqa: E402
import domain_calculation_service  # noqa: E402
import ashtakavarga  # noqa: E402
import divisional_charts_extended  # noqa: E402
import functional_benefics  # noqa: E402
import jaimini  # noqa: E402
import shadbala  # noqa: E402
import narayana_dasha  # noqa: E402
import varga  # noqa: E402

DomainConfig = tuple[tuple[str, ...], tuple[int, ...]]
DOMAIN_CONFIG: Final[dict[EventDomain, DomainConfig]] = {
    "education": (("D24",), (4, 5, 9)),
    "relocation": (("D4",), (4, 12)),
    "relationship": (("D9",), (7,)),
    "career": (("D10",), (10,)),
    "finance": (("D2", "D11"), (2, 11)),
    "health_pressure": (("D30",), (6, 8, 12)),
}


class RectificationEventCalculationError(RuntimeError):
    """Raised when stored rectification evidence cannot be calculated safely."""


def _event_datetime(event: LifeEvent) -> datetime:
    match event["precision"]:
        case "day":
            return datetime.strptime(event["date"], "%Y-%m-%d")
        case "month":
            return datetime.strptime(f"{event['date']}-15", "%Y-%m-%d")
        case "year":
            return datetime.strptime(f"{event['date']}-07-01", "%Y-%m-%d")
        case unreachable:
            assert_never(unreachable)


def _candidate_datetimes(request: RectificationEventRequest) -> list[datetime]:
    birth_date = date.fromisoformat(request["birth_date"])
    start = datetime.combine(birth_date, time.fromisoformat(request["start_time"]))
    end = datetime.combine(birth_date, time.fromisoformat(request["end_time"]))
    if end < start:
        end += timedelta(days=1)
    minute_count = int((end - start).total_seconds() // 60) + 1
    if minute_count < 1 or minute_count > 1_440:
        raise RectificationEventCalculationError("candidate_range_out_of_bounds")
    return [start + timedelta(minutes=offset) for offset in range(minute_count)]


def _active_vimshottari(
    birth_date: str,
    moon_longitude: float,
    event_at: datetime,
) -> tuple[str, str, str]:
    nakshatra, progress, _ = dasha_analyzer.lon_to_nakshatra(moon_longitude)
    timeline, _, _, _ = dasha_analyzer.build_dasha_timeline(
        birth_date,
        nakshatra,
        progress,
    )
    _, major = dasha_analyzer.find_current(timeline, event_at)
    minor = dasha_analyzer.find_current_sub(
        dasha_analyzer.build_antardasha(major),
        event_at,
    )
    pratyantar = dasha_analyzer.find_current_sub(
        dasha_analyzer.build_antardasha(minor),
        event_at,
    )
    return str(major["lord"]), str(minor["lord"]), str(pratyantar["lord"])


def _active_narayana(
    ascendant_index: int,
    planet_longitudes: dict[str, float],
    birth_at: datetime,
    event_at: datetime,
) -> tuple[int | None, int | None]:
    periods = narayana_dasha.calc_narayana_mahadasha(
        ascendant_index,
        planet_longitudes,
    )
    age = max((event_at - birth_at).total_seconds() / (365.2425 * 86_400), 0.0)
    active = narayana_dasha.get_current_narayana_dasha(periods, age)
    major = active.get("md") or {}
    minor = active.get("ad") or {}
    return major.get("sign_idx"), minor.get("sign_idx")


def _varga_chart(charts: dict, prefix: str) -> dict | None:
    return next(
        (chart for name, chart in charts.items() if name.startswith(f"{prefix}_")),
        None,
    )


def _d11_chart(planet_longitudes: dict[str, float], ascendant_longitude: float) -> dict:
    """Adapt the repository's Rudramsa implementation to the event-score shape."""
    raw = divisional_charts_extended.DivisionalChartsCalculator().calculate_all_vargas(
        planet_longitudes, ascendant_longitude,
    )["Rudramsa"]
    return {
        "Ascendant": {"sign_idx": raw["ascendant"]["sign_index"]},
        **{
            planet: {"sign_idx": value["sign_index"]}
            for planet, value in raw["planets"].items()
        },
    }


def _relative_house(sign_index: int, ascendant_index: int) -> int:
    return (sign_index - ascendant_index) % 12 + 1


def _house_lords(ascendant_index: int, houses: tuple[int, ...]) -> set[str]:
    return {
        narayana_dasha.SIGN_LORDS[
            narayana_dasha.SIGNS[(ascendant_index + house - 1) % 12]
        ]
        for house in houses
    }


def _planet_house(chart: dict, planet: str) -> int | None:
    raw = (chart.get("planets", {}).get(planet) or {}).get("house")
    return int(raw) if isinstance(raw, int | float) else None


def _varga_house(chart: dict, planet: str) -> int | None:
    ascendant = chart.get("Ascendant") or {}
    placement = chart.get(planet) or {}
    ascendant_index = ascendant.get("sign_idx")
    planet_index = placement.get("sign_idx")
    if not isinstance(ascendant_index, int) or not isinstance(planet_index, int):
        return None
    return _relative_house(planet_index, ascendant_index)


def _score_event(
    *,
    candidate_time: str,
    event: LifeEvent,
    natal_chart: dict,
    varga_charts: list[dict],
    vimshottari: tuple[str, str, str],
    narayana: tuple[int | None, int | None],
    arudha_padas: dict,
) -> CandidateEvidence:
    _, target_houses = DOMAIN_CONFIG[event["domain"]]
    ascendant_index = int(natal_chart["ascendant"]["lon"] // 30)
    target_lords = _house_lords(ascendant_index, target_houses)
    functional = functional_benefics.derive_functional_benefic_malefic(
        natal_chart["ascendant"].get("sign")
    )
    functional_benefics_set = set(functional.get("functional_benefics") or [])
    functional_malefics_set = set(functional.get("functional_malefics") or [])
    major_lord, minor_lord, pratyantar_lord = vimshottari
    rules: list[str] = []
    points = 0.0

    for lord, weight, label in (
        (major_lord, 2.0, "vim_md"),
        (minor_lord, 1.5, "vim_ad"),
        (pratyantar_lord, 0.75, "vim_pd"),
    ):
        if _planet_house(natal_chart, lord) in target_houses:
            rules.append(f"{label}_domain_house")
            points += weight
        if lord in target_lords:
            rules.append(f"{label}_domain_lord")
            points += weight
        for varga_chart in varga_charts:
            if _varga_house(varga_chart, lord) in target_houses:
                rules.append(f"{label}_domain_varga")
                points += weight / (2 * len(varga_charts))
        if lord in functional_benefics_set:
            rules.append(f"{label}_functional_benefic_auxiliary")
            points += 0.2
        elif lord in functional_malefics_set:
            rules.append(f"{label}_functional_malefic_auxiliary")
            points -= 0.1

    for sign_index, weight, label in (
        (narayana[0], 2.0, "narayana_md"),
        (narayana[1], 1.0, "narayana_ad"),
    ):
        if sign_index is not None and _relative_house(sign_index, ascendant_index) in target_houses:
            rules.append(f"{label}_domain_house")
            points += weight
    arudha_keys = ("A7", "UL") if event["domain"] == "relationship" else ("A10",) if event["domain"] == "career" else ()
    arudha_signs = {
        value.get("sign_idx") for key in arudha_keys
        if isinstance((value := arudha_padas.get(key)), dict) and isinstance(value.get("sign_idx"), int)
    }
    if arudha_signs:
        for lord, label in ((major_lord, "vim_md"), (minor_lord, "vim_ad"), (pratyantar_lord, "vim_pd")):
            planet = natal_chart.get("planets", {}).get(lord) or {}
            if isinstance(planet.get("lon"), (int, float)) and int(planet["lon"] // 30) in arudha_signs:
                rules.append(f"{label}_arudha_auxiliary")
                points += 0.35

    weighted_points = round(points * precision_weight(event["precision"]), 4)
    return {
        "event_id": event["id"],
        "domain": event["domain"],
        "candidate_time": candidate_time,
        "rule_ids": rules or ["no_domain_activation"],
        "points": weighted_points,
    }


def _controlled_transit_rules(
    request: RectificationEventRequest,
    event: LifeEvent,
    natal_ascendant_index: int,
    target_houses: tuple[int, ...],
) -> list[str]:
    """Use only Jupiter/Saturn and only day/month dated events as a weak check."""
    if event["precision"] == "year":
        return []
    event_at = _event_datetime(event)
    transit_chart = domain_calculation_service.compute_chart({
        "year": event_at.year, "month": event_at.month, "day": event_at.day,
        "hour": 12, "minute": 0, "lat": request["lat"], "lon": request["lon"],
        "tz": request["tz"], "ayanamsa": "lahiri", "node_mode": "true",
    })
    rules: list[str] = []
    for planet in ("Jupiter", "Saturn"):
        item = transit_chart.get("planets", {}).get(planet) or {}
        if isinstance(item.get("lon"), (int, float)) and _relative_house(int(item["lon"] // 30), natal_ascendant_index) in target_houses:
            rules.append(f"controlled_transit_{planet.lower()}_domain_house")
    return rules


def _ashtakavarga_auxiliary(natal_chart: dict, ascendant_index: int, target_houses: tuple[int, ...]) -> tuple[list[str], float]:
    """Return a bounded SAV consistency adjustment, never a standalone trigger."""
    result = ashtakavarga.calc_ashtakavarga(natal_chart.get("planets", {}), ascendant_index)
    if not result.get("all_bav_valid") or not (result.get("sav") or {}).get("valid"):
        return [], 0.0
    house_scores = result.get("house_scores_full") or {}
    values = [house_scores.get(f"house_{house}", {}).get("sav_score") for house in target_houses]
    numeric = [float(value) for value in values if isinstance(value, (int, float))]
    if not numeric:
        return [], 0.0
    average = sum(numeric) / len(numeric)
    if average >= 32:
        return ["ashtakavarga_target_house_support_auxiliary"], 0.2
    if average <= 24:
        return ["ashtakavarga_target_house_pressure_auxiliary"], -0.1
    return [], 0.0


def _shadbala_verified_components_auxiliary(natal_chart: dict, birth_hour: float, dasha_lords: tuple[str, str, str]) -> tuple[list[str], float]:
    """Use only Sthana/Drik/Naisargika, whose oracle comparison is already matched."""
    planets = natal_chart.get("planets", {})
    sun = planets.get("Sun") or {}
    moon = planets.get("Moon") or {}
    if not isinstance(sun.get("lon"), (int, float)) or not isinstance(moon.get("lon"), (int, float)):
        return [], 0.0
    result = shadbala.calc_shadbala(
        planets, str(natal_chart["ascendant"].get("sign") or "Aries"), birth_hour,
        float(sun["lon"]), float(moon["lon"]),
    )
    values = {
        planet: float((row.get("sthana_bala") or {}).get("total", 0)) + float(row.get("drik_bala", 0)) + float(row.get("naisargika_bala", 0))
        for planet, row in (result.get("planets") or {}).items()
    }
    if not values:
        return [], 0.0
    baseline = sum(values.values()) / len(values)
    active = [values[lord] for lord in dasha_lords if lord in values]
    if not active:
        return [], 0.0
    average = sum(active) / len(active)
    if average > baseline:
        return ["shadbala_sthana_drik_naisargika_support_auxiliary"], 0.1
    if average < baseline:
        return ["shadbala_sthana_drik_naisargika_pressure_auxiliary"], -0.05
    return [], 0.0


def _candidate_row(
    request: RectificationEventRequest,
    candidate_at: datetime,
) -> CandidateScoreRow:
    chart = domain_calculation_service.compute_chart({
        "year": candidate_at.year,
        "month": candidate_at.month,
        "day": candidate_at.day,
        "hour": candidate_at.hour,
        "minute": candidate_at.minute,
        "lat": request["lat"],
        "lon": request["lon"],
        "tz": request["tz"],
        "ayanamsa": "lahiri",
        "node_mode": "true",
    })
    planet_longitudes = {
        name: float(data["lon"])
        for name, data in chart.get("planets", {}).items()
        if isinstance(data, dict) and isinstance(data.get("lon"), int | float)
    }
    ascendant_longitude = float(chart["ascendant"]["lon"])
    ascendant_index = int(ascendant_longitude // 30)
    arudha_padas = (jaimini.calc_arudha_padas(ascendant_index, planet_longitudes).get("padas") or {})
    charts = varga.calc_all_vargas(
        planet_longitudes,
        ascendant_longitude,
        divisions=[2, 4, 9, 10, 24, 30],
    )
    d11_chart = _d11_chart(planet_longitudes, ascendant_longitude)
    moon_longitude = planet_longitudes["Moon"]
    evidence: list[CandidateEvidence] = []
    missing_layers: list[str] = []

    for event in request["events"]:
        event_at = _event_datetime(event)
        prefixes, _ = DOMAIN_CONFIG[event["domain"]]
        domain_vargas = [d11_chart if prefix == "D11" else _varga_chart(charts, prefix) for prefix in prefixes]
        if any(chart is None for chart in domain_vargas):
            missing_layers.extend(prefixes)
            continue
        vimshottari = _active_vimshottari(request["birth_date"], moon_longitude, event_at)
        narayana = _active_narayana(
            ascendant_index,
            planet_longitudes,
            candidate_at,
            event_at,
        )
        evidence.append(_score_event(
            candidate_time=candidate_at.strftime("%H:%M"),
            event=event,
            natal_chart=chart,
            varga_charts=[chart for chart in domain_vargas if chart is not None],
            vimshottari=vimshottari,
            narayana=narayana,
            arudha_padas=arudha_padas,
        ))
        transit_rules = _controlled_transit_rules(request, event, ascendant_index, DOMAIN_CONFIG[event["domain"]][1])
        if transit_rules:
            evidence[-1]["rule_ids"].extend(transit_rules)
            evidence[-1]["points"] = round(evidence[-1]["points"] + 0.25 * len(transit_rules) * precision_weight(event["precision"]), 4)
        av_rules, av_points = _ashtakavarga_auxiliary(chart, ascendant_index, DOMAIN_CONFIG[event["domain"]][1])
        if av_rules:
            evidence[-1]["rule_ids"].extend(av_rules)
            evidence[-1]["points"] = round(evidence[-1]["points"] + av_points * precision_weight(event["precision"]), 4)
        shadbala_rules, shadbala_points = _shadbala_verified_components_auxiliary(
            chart, candidate_at.hour + candidate_at.minute / 60, vimshottari,
        )
        if shadbala_rules:
            evidence[-1]["rule_ids"].extend(shadbala_rules)
            evidence[-1]["points"] = round(evidence[-1]["points"] + shadbala_points * precision_weight(event["precision"]), 4)

    return {
        "time": candidate_at.strftime("%H:%M"),
        "score": round(sum(item["points"] for item in evidence), 4),
        "evidence": evidence,
        "missing_layers": sorted(set(missing_layers)),
    }


def compute_event_candidate_result(request: RectificationEventRequest) -> CandidateResult:
    """Compute actual minute candidates locally and return a guarded result."""
    normalized = json.dumps(request, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    rows = [_candidate_row(request, candidate) for candidate in _candidate_datetimes(request)]
    return adjudicate_candidate_rows(
        rows,
        event_count=len(request["events"]),
        domain_count=len({event["domain"] for event in request["events"]}),
        request_fingerprint=fingerprint,
    )
