#!/usr/bin/env python3
"""Muhurta factor probe: observation only, no electional verdict."""

from __future__ import annotations

import argparse
import json
from datetime import datetime

from cmd_muhurta import _get_sun_moon_lons, _weekday_to_vara
from muhurta import calc_panchanga, calc_abhijit_muhurta

YAMAGANDA_SEGMENT_BY_WEEKDAY = {
    0: 5,  # Sunday
    1: 4,
    2: 3,
    3: 2,
    4: 1,
    5: 7,
    6: 6,
}

GULIKA_SEGMENT_BY_WEEKDAY = {
    0: 7,  # Sunday
    1: 6,
    2: 5,
    3: 4,
    4: 3,
    5: 2,
    6: 1,
}


def _tarabala(birth_moon_nakshatra_index: int | None, current_nakshatra_index: int) -> dict:
    if birth_moon_nakshatra_index is None:
        return {"status": "missing_birth_moon_nakshatra", "claim": "not_computed"}
    tara_pos = ((current_nakshatra_index - birth_moon_nakshatra_index) % 27) + 1
    tara_class = ((tara_pos - 1) % 9) + 1
    favorable = tara_class in {2, 4, 6, 8, 9}
    return {"status": "computed_rule_probe", "tara_position": tara_pos, "tara_class": tara_class, "favorable": favorable}


def _chandrabala(birth_moon_sign_index: int | None, current_moon_lon: float) -> dict:
    if birth_moon_sign_index is None:
        return {"status": "missing_birth_moon_sign", "claim": "not_computed"}
    current_sign = int((current_moon_lon % 360) // 30)
    relative_house = ((current_sign - birth_moon_sign_index) % 12) + 1
    favorable = relative_house not in {6, 8, 12}
    return {"status": "computed_rule_probe", "relative_house": relative_house, "favorable": favorable}


def _segment_window(segment: int, sunrise: str = "06:00", sunset: str = "18:00") -> dict:
    def minutes(value: str) -> int:
        hour, minute = [int(part) for part in value.split(":", 1)]
        return hour * 60 + minute

    def hhmm(value: float) -> str:
        total = int(round(value)) % (24 * 60)
        return f"{total // 60:02d}:{total % 60:02d}"

    start_day = minutes(sunrise)
    end_day = minutes(sunset)
    if end_day <= start_day:
        end_day += 24 * 60
    length = (end_day - start_day) / 8
    start = start_day + (segment - 1) * length
    end = start + length
    return {"segment": segment, "start": hhmm(start), "end": hhmm(end), "duration_minutes": round(length, 1)}


def _yamaganda(weekday_idx: int) -> dict:
    return {
        "status": "computed_rule_probe",
        "quality": "avoid",
        "window": _segment_window(YAMAGANDA_SEGMENT_BY_WEEKDAY[weekday_idx % 7]),
    }


def _gulika_kalam(weekday_idx: int) -> dict:
    return {
        "status": "computed_rule_probe",
        "quality": "avoid_or_handle_with_caution",
        "window": _segment_window(GULIKA_SEGMENT_BY_WEEKDAY[weekday_idx % 7]),
    }


def _panchaka(current_moon_lon: float) -> dict:
    sign_index = int((current_moon_lon % 360) // 30)
    active = sign_index in {10, 11}  # Aquarius/Pisces observation rule
    return {
        "status": "computed_rule_probe",
        "active": active,
        "moon_sign_index": sign_index,
        "quality": "avoid" if active else "neutral",
    }


def _sankranti(sun_lon: float) -> dict:
    degree_in_sign = sun_lon % 30
    near_boundary = degree_in_sign <= 1 or degree_in_sign >= 29
    return {
        "status": "boundary_screen_observation",
        "active_or_near": near_boundary,
        "sun_degree_in_sign": round(degree_in_sign, 3),
        "quality": "avoid_or_verify_exact_ingress" if near_boundary else "not_near_boundary",
    }


def _yoga_flag(panchanga: dict, yoga_name: str) -> dict:
    current = ((panchanga.get("yoga") or {}).get("yoga") or "")
    active = current.casefold() == yoga_name.casefold()
    return {
        "status": "computed_rule_probe",
        "active": active,
        "current_yoga": current,
        "quality": "avoid" if active else "not_active",
    }


def _factor_scorecard(factors: dict) -> dict:
    favorable = []
    caution = []
    for key, value in factors.items():
        if not isinstance(value, dict):
            continue
        if value.get("favorable") is True or value.get("quality") in {"not_active", "not_near_boundary"}:
            favorable.append(key)
        if value.get("favorable") is False or value.get("quality") in {"avoid", "avoid_or_verify_exact_ingress", "avoid_or_handle_with_caution"}:
            caution.append(key)
    return {
        "claim_status": "factor_only_not_final_muhurta_verdict",
        "score_cap": "low",
        "favorable_factor_count": len(favorable),
        "caution_factor_count": len(caution),
        "favorable_factors": favorable,
        "caution_factors": caution,
        "boundary": "Factor scorecard is for comparison only; it is not a final electional verdict.",
    }


def build_probe(date_text: str, birth_moon_nakshatra_index: int | None, birth_moon_sign_index: int | None) -> dict:
    dt = datetime.strptime(date_text, "%Y-%m-%d")
    sun_lon, moon_lon, has_swiss = _get_sun_moon_lons(dt.year, dt.month, dt.day, 12)
    weekday = _weekday_to_vara(dt.weekday())
    panchanga = calc_panchanga(sun_lon=sun_lon, moon_lon=moon_lon, weekday=weekday, hour_from_sunrise=6.0)
    factors = {
        "panchanga": panchanga,
        "tarabala": _tarabala(birth_moon_nakshatra_index, panchanga["nakshatra"]["nakshatra_idx"]),
        "chandrabala": _chandrabala(birth_moon_sign_index, moon_lon),
        "rahu_kalam": panchanga.get("rahu_kala"),
        "yamaganda": _yamaganda(weekday),
        "gulika_kalam": _gulika_kalam(weekday),
        "abhijit_muhurta": calc_abhijit_muhurta(),
        "panchaka": _panchaka(moon_lon),
        "sankranti": _sankranti(sun_lon),
        "vyatipata": _yoga_flag(panchanga, "Vyatipata"),
        "vaidhriti": _yoga_flag(panchanga, "Vaidhriti"),
    }
    signals = []
    blockers = []
    if factors["tarabala"].get("favorable") is True:
        signals.append("Tarabala")
    elif factors["tarabala"].get("favorable") is False:
        blockers.append("Tarabala")
    if factors["chandrabala"].get("favorable") is True:
        signals.append("Chandrabala")
    elif factors["chandrabala"].get("favorable") is False:
        blockers.append("Chandrabala")
    if factors["abhijit_muhurta"]:
        signals.append("Abhijit")
    factor_scorecard = _factor_scorecard(factors)
    return {
        "scope": "muhurta_factor_probe",
        "created_at": "2026-07-19",
        "date": date_text,
        "production_tuning_allowed": False,
        "claim_status": "exploratory_muhurta_candidate",
        "verified_muhurta_verdict": False,
        "full_scoring_status": "factor_only_scoring_observation",
        "final_muhurta_verdict_status": "blocked_until_oracle",
        "ephemeris_source": "swisseph" if has_swiss else "approximate_fallback",
        "factors": factors,
        "factor_scorecard": factor_scorecard,
        "candidate_windows": [
            {
                "label": "abhijit_reference_window",
                "signals": signals,
                "blockers": blockers,
                "confidence_cap": "low",
                "claim_status": "exploratory_muhurta_candidate"
            }
        ],
        "boundary": "Muhurta factors are observations only；未通过完整 worked examples 与负样本验证，不能作为确定择日承诺。"
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--birth-moon-nakshatra-index", type=int)
    parser.add_argument("--birth-moon-sign-index", type=int)
    args = parser.parse_args()
    print(json.dumps(build_probe(args.date, args.birth_moon_nakshatra_index, args.birth_moon_sign_index), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
