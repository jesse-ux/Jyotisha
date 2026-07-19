#!/usr/bin/env python3
"""Muhurta factor probe: observation only, no electional verdict."""

from __future__ import annotations

import argparse
import json
from datetime import datetime

from cmd_muhurta import _get_sun_moon_lons, _weekday_to_vara
from muhurta import calc_panchanga, calc_abhijit_muhurta


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
        "abhijit_muhurta": calc_abhijit_muhurta(),
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
    return {
        "scope": "muhurta_factor_probe",
        "created_at": "2026-07-19",
        "date": date_text,
        "production_tuning_allowed": False,
        "claim_status": "exploratory_muhurta_candidate",
        "verified_muhurta_verdict": False,
        "full_scoring_status": "blocked_until_oracle",
        "ephemeris_source": "swisseph" if has_swiss else "approximate_fallback",
        "factors": factors,
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
