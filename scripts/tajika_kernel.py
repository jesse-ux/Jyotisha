"""Strict seven-planet Tajika aspect kernel.

This module deliberately exposes only the auditable interaction layer. Named
Tajika chains remain blocked until their classical definitions have golden
cases; it never treats nodes as Tajika planets.
"""

from __future__ import annotations

from typing import Any


SEVEN_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
DEEPTAMSA = {"Sun": 15.0, "Moon": 12.0, "Mars": 8.0, "Mercury": 7.0, "Jupiter": 9.0, "Venus": 7.0, "Saturn": 9.0}
ASPECT_ANGLES = (0.0, 60.0, 90.0, 120.0, 180.0)


def _signed_angle(value: float) -> float:
    return (value + 180.0) % 360.0 - 180.0


def _nearest_aspect(delta: float) -> tuple[float, float]:
    candidates = []
    for aspect in ASPECT_ANGLES:
        for target in ({0.0} if aspect in (0.0, 180.0) else {aspect, -aspect}):
            candidates.append((target, _signed_angle(delta - target)))
    return min(candidates, key=lambda item: abs(item[1]))


def calculate_tajika_interactions(planets: dict[str, dict[str, Any]]) -> dict[str, Any]:
    missing = [planet for planet in SEVEN_PLANETS if planet not in planets or "longitude" not in planets[planet] or "speed" not in planets[planet]]
    if missing:
        return {
            "scope": "tajika_seven_planet_kernel",
            "status": "blocked",
            "reason": "longitude_and_speed_required_for_all_seven_planets",
            "missing": missing,
            "nodes_excluded": True,
        }
    interactions = []
    for index, left in enumerate(SEVEN_PLANETS):
        for right in SEVEN_PLANETS[index + 1:]:
            left_lon, right_lon = float(planets[left]["longitude"]) % 360, float(planets[right]["longitude"]) % 360
            aspect, residual = _nearest_aspect(right_lon - left_lon)
            orb = (DEEPTAMSA[left] + DEEPTAMSA[right]) / 2.0
            if abs(residual) > orb:
                continue
            relative_speed = float(planets[right]["speed"]) - float(planets[left]["speed"])
            future_residual = _signed_angle(residual + relative_speed)
            applying = abs(future_residual) < abs(residual)
            interactions.append({
                "planets": [left, right],
                "aspect": abs(aspect),
                "residual": round(residual, 6),
                "average_deeptamsa": orb,
                "motion": "applying" if applying else "separating",
                "within_deeptamsa": True,
            })
    return {
        "scope": "tajika_seven_planet_kernel",
        "status": "partial",
        "nodes_excluded": True,
        "interactions": interactions,
        "blocked_named_yogas": ["Nakta", "Yamaya", "Manahoo", "Ithasala chain"],
        "boundary": "Only aspect/applying evidence is computed. Named Tajika yoga chains and verdicts remain blocked pending classic golden cases.",
    }
