#!/usr/bin/env python3
"""Generate active-choice birth-time rectification questions."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from typing import Any

from scripts.active_rectification_scoring import build_questions, score_answers


def _parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M")


def _candidate_scan(
    center: datetime,
    uncertainty_minutes: int,
    step_minutes: int,
    *,
    lat: float | None = None,
    lon: float | None = None,
    tz: float | None = None,
    ayanamsa: str = "lahiri",
) -> dict[str, Any]:
    start = center - timedelta(minutes=uncertainty_minutes)
    end = center + timedelta(minutes=uncertainty_minutes)
    total_minutes = int((end - start).total_seconds() // 60)
    candidate_count = total_minutes // step_minutes + 1
    sample_offsets = sorted({-uncertainty_minutes, 0, uncertainty_minutes})
    samples = []
    for offset in sample_offsets:
        candidate = center + timedelta(minutes=offset)
        if offset < 0:
            cluster = "early_candidate_cluster"
        elif offset > 0:
            cluster = "late_candidate_cluster"
        else:
            cluster = "middle_candidate_cluster"
        sample = {
            "time": candidate.strftime("%Y-%m-%d %H:%M"),
            "offset_minutes": offset,
            "cluster": cluster,
            "sensitivity_flags": _sensitivity_flags(abs(offset)),
        }
        recast = _candidate_recast(candidate, lat=lat, lon=lon, tz=tz, ayanamsa=ayanamsa)
        if recast:
            sample.update(recast)
        samples.append(sample)
    has_true_recast = all("varga_lagna" in sample for sample in samples)
    has_kp_recast = all("kp_cusps" in sample for sample in samples)
    computed_layers = ["time_range", "candidate_cluster", "question_sensitivity_map"]
    blocked_layers = ["true_varga_recast", "true_kp_cusp_recast", "true_arudha_recast"]
    if has_true_recast:
        computed_layers.extend(["true_varga_recast", "true_arudha_recast"])
        blocked_layers = ["true_kp_cusp_recast"]
    if has_kp_recast:
        computed_layers.append("true_kp_cusp_recast")
        blocked_layers = [layer for layer in blocked_layers if layer != "true_kp_cusp_recast"]
    return {
        "start": start.strftime("%Y-%m-%d %H:%M"),
        "end": end.strftime("%Y-%m-%d %H:%M"),
        "step_minutes": step_minutes,
        "candidate_count": candidate_count,
        "cluster_labels": ["early_candidate_cluster", "middle_candidate_cluster", "late_candidate_cluster"],
        "samples": samples,
        "sensitivity_summary": {
            "method": "range_bucket_scan_v1",
            "high_value_layers": ["D9", "D10", "D24", "D30", "D60", "UL", "A7", "A10", "KP_cusp"],
            "computed_layers": computed_layers,
            "blocked_layers": blocked_layers,
            "boundary": "Candidate Varga, Arudha and KP cusp recasts are computed from the local domain chart; external oracle parity remains a separate gate.",
        },
    }


def _sensitivity_flags(abs_offset_minutes: int) -> list[str]:
    flags = ["D9", "D10", "D24", "A10"]
    if abs_offset_minutes >= 10:
        flags.extend(["D30", "UL", "A7"])
    if abs_offset_minutes >= 20:
        flags.extend(["D60", "KP_cusp"])
    return flags


def _candidate_recast(
    candidate: datetime,
    *,
    lat: float | None,
    lon: float | None,
    tz: float | None,
    ayanamsa: str,
) -> dict[str, Any] | None:
    if lat is None or lon is None or tz is None:
        return None
    import domain_calculation_service
    import jaimini
    import varga

    chart = domain_calculation_service.compute_chart({
        "year": candidate.year,
        "month": candidate.month,
        "day": candidate.day,
        "hour": candidate.hour,
        "minute": candidate.minute,
        "second": candidate.second,
        "lat": lat,
        "lon": lon,
        "tz": tz,
        "ayanamsa": ayanamsa,
    })
    planet_lons = {
        name: data["lon"]
        for name, data in chart.get("planets", {}).items()
        if name in {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
    }
    asc_lon = chart["ascendant"]["lon"]
    vargas = varga.calc_all_vargas(planet_lons, asc_lon, divisions=[4, 9, 10, 24, 30, 60])
    arudha = jaimini.calc_arudha_padas(int(asc_lon // 30), planet_lons)
    padas = arudha.get("padas", {})
    upapada = arudha.get("upapada", {})
    return {
        "ascendant": {
            "lon": round(asc_lon, 6),
            "sign": chart["ascendant"].get("sign"),
            "degree_in_sign": chart["ascendant"].get("degree_in_sign"),
        },
        "varga_lagna": {
            **{
                key: value.get("Ascendant", {})
                for key, value in vargas.items()
            },
            **{
                f"D{division}": value.get("Ascendant", {})
                for division in (4, 9, 10, 24, 30)
                for key, value in vargas.items()
                if key.startswith(f"D{division}_")
            },
        },
        "arudha": {
            "A7": padas.get("A7", {}),
            "A10": padas.get("A10", {}),
            "UL": upapada,
        },
        "kp_cusps": _kp_cusp_snapshot(chart),
    }


def _kp_cusp_snapshot(chart: dict[str, Any]) -> dict[str, Any]:
    import kp_system

    snapshot = {}
    for house_key in ("house_1", "house_4", "house_7", "house_10"):
        house = chart.get("houses", {}).get(house_key, {})
        degree = house.get("cusp_degree")
        if degree is None:
            continue
        lords = kp_system.get_kp_lords(float(degree))
        snapshot[house_key] = {
            "cusp_degree": round(float(degree) % 360, 6),
            "sign": lords.get("sign"),
            "rasi_lord": lords.get("rasi_lord"),
            "nakshatra": lords.get("nakshatra"),
            "nakshatra_lord": lords.get("nakshatra_lord"),
            "sub_lord": lords.get("sub_lord"),
            "sub_sub_lord": lords.get("sub_sub_lord"),
        }
    return snapshot


def build_questionnaire(
    birth_time: str,
    uncertainty_minutes: int = 30,
    step_minutes: int = 1,
    *,
    lat: float | None = None,
    lon: float | None = None,
    tz: float | None = None,
    ayanamsa: str = "lahiri",
) -> dict[str, Any]:
    questions = build_questions()
    return {
        "scope": "active_birth_time_rectification_questionnaire",
        "schema_version": 1,
        "candidate_scan": _candidate_scan(
            _parse_time(birth_time),
            uncertainty_minutes,
            step_minutes,
            lat=lat,
            lon=lon,
            tz=tz,
            ayanamsa=ayanamsa,
        ),
        "workflow": [
            "candidate_time_scan",
            "varga_arudha_kp_sensitivity_diff",
            "high_information_question_generation",
            "multiple_choice_user_answers",
            "dynamic_candidate_cluster_scoring",
            "next_round_question_selection",
        ],
        "rounds": {
            "1": "coarse screen",
            "2": "domain follow-up",
            "3": "fine confirmation",
        },
        "sensitivity_layers": ["D9", "D10", "D24", "D30", "D60", "D4", "UL", "A7", "A10", "KP_cusp", "Vimshottari", "Narayana", "Chara"],
        "questions": questions,
        "boundary": "Question generation only; final rectification requires scoring answers against actual candidate chart differences.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--birth-time", required=True, help="Approximate local birth time, YYYY-MM-DD HH:MM")
    parser.add_argument("--uncertainty-minutes", type=int, default=30)
    parser.add_argument("--step-minutes", type=int, default=1)
    parser.add_argument("--answers-json", default="", help="Optional JSON object mapping question id to A/B/C/D")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    questionnaire = build_questionnaire(args.birth_time, args.uncertainty_minutes, args.step_minutes)
    report = score_answers(questionnaire, json.loads(args.answers_json)) if args.answers_json else questionnaire
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
