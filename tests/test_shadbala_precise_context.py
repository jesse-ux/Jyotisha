from scripts.shadbala import (
    build_shadbala_context,
    calc_dig_bala_precise,
    calc_drik_bala_precise,
    calc_sthana_bala_precise,
    classify_drik_planets,
)


PLANET_LONGITUDES = {
    "Sun": 312.51819523181405,
    "Moon": 344.51168181221095,
    "Mars": 5.862334338243072,
    "Mercury": 291.12589362817465,
    "Jupiter": 87.27055150216494,
    "Venus": 267.94211928370015,
    "Saturn": 207.92738390514674,
}
PYJHORA_DIG = {"Sun": 24.81, "Moon": 95.48, "Mars": 77.41, "Mercury": 12.64, "Jupiter": 80.60, "Venus": 69.95, "Saturn": 19.62}
PYJHORA_DRIK = {"Sun": 1.74, "Moon": 20.06, "Mars": 13.49, "Mercury": -10.63, "Jupiter": 6.89, "Venus": -2.75, "Saturn": 9.49}
PYJHORA_STHANA = {"Sun": 217.09, "Moon": 246.34, "Mars": 198.63, "Mercury": 167.96, "Jupiter": 201.80, "Venus": 154.06, "Saturn": 218.61}


def _planets() -> dict:
    return {
        planet: {
            "degree": longitude,
            "sign": ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"][int(longitude // 30)],
        }
        for planet, longitude in PLANET_LONGITUDES.items()
    }


def test_precise_dig_bala_matches_pyjhora_same_chart() -> None:
    context = build_shadbala_context(2435163.6354166665, 37.7749, -122.4194, "lahiri")
    for planet, longitude in PLANET_LONGITUDES.items():
        assert calc_dig_bala_precise(planet, longitude, context["house_midpoints"]) == PYJHORA_DIG[planet]


def test_drik_classification_matches_pyjhora_same_chart() -> None:
    benefics, malefics = classify_drik_planets(_planets())
    assert benefics == {"Moon", "Mercury", "Jupiter", "Venus"}
    assert malefics == {"Sun", "Mars", "Saturn"}


def test_precise_drik_bala_matches_pyjhora_same_chart() -> None:
    planets = _planets()
    for planet, expected in PYJHORA_DRIK.items():
        assert abs(calc_drik_bala_precise(planet, planets) - expected) <= 0.02


def test_precise_sthana_bala_matches_pyjhora_same_chart() -> None:
    planets = _planets()
    houses = {"Sun": 7, "Moon": 8, "Mars": 9, "Mercury": 6, "Jupiter": 11, "Venus": 5, "Saturn": 3}
    for planet, expected in PYJHORA_STHANA.items():
        assert calc_sthana_bala_precise(planet, planets, houses[planet])["total"] == expected
