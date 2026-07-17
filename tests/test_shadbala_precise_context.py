from scripts.shadbala import (
    build_shadbala_context,
    calc_dig_bala_precise,
    calc_drik_bala_precise,
    calc_kala_bala_precise,
    calc_chesta_bala_precise,
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
PYJHORA_KALA = {"Sun": 140.99, "Moon": 149.58, "Mars": 127.93, "Mercury": 121.78, "Jupiter": 199.31, "Venus": 113.44, "Saturn": 136.77}


def _planets() -> dict:
    return {
        planet: {
            "degree": longitude,
            "sign": ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"][int(longitude // 30)],
        }
        for planet, longitude in PLANET_LONGITUDES.items()
    }


def test_precise_dig_bala_matches_pyjhora_same_chart() -> None:
    context = build_shadbala_context(2435163.6354166665, 37.7749, -122.4194, "lahiri", -8.0)
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


def test_precise_kala_bala_matches_pyjhora_same_chart() -> None:
    planets = _planets()
    context = build_shadbala_context(2435163.6354166665, 37.7749, -122.4194, "lahiri", -8.0)
    assert abs(context["sunrise_hour"] - 6.886306) < 0.00001
    assert abs(context["sunset_hour"] - 17.890427) < 0.00001
    for planet, expected in PYJHORA_KALA.items():
        assert calc_kala_bala_precise(planet, planets, context)["total"] == expected


def test_precise_chesta_uses_classical_bounded_variant() -> None:
    planets = _planets()
    context = build_shadbala_context(2435163.6354166665, 37.7749, -122.4194, "lahiri", -8.0)
    kala = {planet: calc_kala_bala_precise(planet, planets, context) for planet in planets}
    result = {planet: calc_chesta_bala_precise(planet, planets, kala[planet], context) for planet in planets}
    assert result["Sun"] == kala["Sun"]["ayana"]
    assert result["Moon"] == kala["Moon"]["paksha"]
    for planet in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        assert 0.0 <= result[planet] <= 60.0
    vedastro = {"Mars": 21.7377, "Mercury": 47.5107, "Jupiter": 46.0549, "Venus": 30.8469, "Saturn": 39.4390}
    tolerances = {"Mars": 1.0, "Mercury": 2.0, "Jupiter": 1.0, "Venus": 2.0, "Saturn": 3.5}
    for planet, expected in vedastro.items():
        assert abs(result[planet] - expected) <= tolerances[planet]
