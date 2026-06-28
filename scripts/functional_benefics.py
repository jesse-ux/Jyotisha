#!/usr/bin/env python3
"""Functional benefic/malefic classification by ascendant."""

from __future__ import annotations

from typing import Any


SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_TO_INDEX = {name: idx for idx, name in enumerate(SIGNS)}
SIGN_LORDS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}
PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
SOURCE = "strict_functional_benefic_malefic_v1"


def normalize_sign(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    lowered = value.strip().lower()
    for sign in SIGNS:
        if sign.lower() == lowered:
            return sign
    return None


def derive_functional_benefic_malefic(ascendant: Any) -> dict[str, Any]:
    """Return functional benefics, malefics and ownership roles for a Lagna."""
    asc_sign = normalize_sign(ascendant)
    if asc_sign is None:
        return {
            "status": "blocked",
            "ascendant": ascendant if isinstance(ascendant, str) else None,
            "functional_benefics": [],
            "functional_malefics": [],
            "functional_neutrals": [],
            "yogakarakas": [],
            "owned_houses": {},
            "effect_on_confidence": "Functional layer blocked: unknown ascendant sign.",
            "source": SOURCE,
        }

    asc_idx = SIGN_TO_INDEX[asc_sign]
    owned_houses: dict[str, list[int]] = {}
    for house_num in range(1, 13):
        sign = SIGNS[(asc_idx + house_num - 1) % 12]
        lord = SIGN_LORDS.get(sign)
        if lord:
            owned_houses.setdefault(lord, []).append(house_num)

    trines = {1, 5, 9}
    kendras = {1, 4, 7, 10}
    challenging = {3, 6, 8, 11, 12}
    benefics: set[str] = set()
    malefics: set[str] = set()
    yogakarakas: set[str] = set()
    neutrals: set[str] = set()

    for planet in PLANETS:
        houses = owned_houses.get(planet, [])
        if not houses:
            continue
        owns_trine = any(house in trines for house in houses)
        owns_kendra = any(house in kendras for house in houses)
        owns_challenge = any(house in challenging for house in houses)

        if owns_trine and owns_kendra and planet not in {"Sun", "Moon"}:
            yogakarakas.add(planet)
            benefics.add(planet)
        elif owns_trine:
            benefics.add(planet)
        elif owns_challenge and 1 not in houses:
            malefics.add(planet)
        elif owns_kendra and planet in {"Jupiter", "Venus", "Mercury", "Moon"}:
            neutrals.add(planet)
        else:
            neutrals.add(planet)

    eighth_lord = next((planet for planet, houses in owned_houses.items() if 8 in houses), None)
    if eighth_lord in {"Sun", "Moon"} and eighth_lord in malefics:
        malefics.remove(eighth_lord)
        neutrals.add(eighth_lord)

    return {
        "status": "used",
        "ascendant": asc_sign,
        "functional_benefics": sorted(benefics),
        "functional_malefics": sorted(malefics),
        "functional_neutrals": sorted(neutrals - benefics - malefics),
        "yogakarakas": sorted(yogakarakas),
        "owned_houses": {planet: houses for planet, houses in sorted(owned_houses.items())},
        "effect_on_confidence": (
            "高严谨模式下必须叠加功能性宫主吉凶与自然吉凶；"
            "若功能属性与自然属性冲突，应降低置信度或显式标记冲突。"
        ),
        "source": SOURCE,
    }
