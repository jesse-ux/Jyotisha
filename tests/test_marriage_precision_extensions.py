from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from jaimini import calc_darapada  # noqa: E402
from kp_system import calc_kp_analysis, calc_kp_dba_timeline  # noqa: E402


USER_PLANET_LONS = {
    "Sun": 3.5036111111111112,
    "Moon": 311.8041666666667,
    "Mars": 91.31277777777778,
    "Mercury": 338.52805555555557,
    "Jupiter": 163.81833333333333,
    "Venus": 340.5394444444444,
    "Saturn": 304.28305555555556,
    "Rahu": 231.02916666666667,
    "Ketu": 51.028888888888886,
}

USER_PLANET_HOUSES = {
    "Sun": 9,
    "Moon": 7,
    "Mars": 12,
    "Mercury": 8,
    "Jupiter": 2,
    "Venus": 8,
    "Saturn": 7,
    "Rahu": 4,
    "Ketu": 10,
}


def test_calc_darapada_returns_a7_relationship_maintenance_fields():
    darapada = calc_darapada(4, USER_PLANET_LONS)

    assert darapada["name"] == "Darapada (A7)"
    assert darapada["source_house_num"] == 7
    assert darapada["sign"] == "Scorpio"
    assert darapada["second_from_a7"] == "Sagittarius"
    assert darapada["eighth_from_a7"] == "Gemini"


def test_kp_dba_timeline_scores_marriage_houses():
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]
    planet_positions = {
        planet: {
            "longitude": longitude,
            "sign": signs[int(longitude // 30)],
            "degree": longitude % 30,
            "house": USER_PLANET_HOUSES[planet],
        }
        for planet, longitude in USER_PLANET_LONS.items()
    }
    kp = calc_kp_analysis(planet_positions, "Leo")
    planet_significators = {
        planet: data["significators"]
        for planet, data in kp["planets"].items()
    }

    timeline = calc_kp_dba_timeline(
        datetime(REDACTED_YEAR, 4, 17, 14, 49),
        311.8041666666667,
        datetime(2027, 1, 1),
        datetime(2029, 12, 31),
        planet_significators,
    )

    assert timeline["birth_star_lord"] == "Rahu"
    assert timeline["target_start"].startswith("2027-01-01")
    assert timeline["periods"]
    assert any(row["judgement"] == "mixed" for row in timeline["periods"])
    assert all({"md_lord", "ad_lord", "pd_lord", "start", "end", "marriage_score"} <= set(row) for row in timeline["periods"])
