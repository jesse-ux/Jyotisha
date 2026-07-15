"""Regression tests for native Western timing calculations."""

from __future__ import annotations

from scripts.western_timing_engine import (
    build_timing_techniques,
    calculate_secondary_progressions,
    calculate_solar_arc_directions,
    calculate_solar_return,
    calculate_transit_to_natal,
)


_BIRTH = {
    "year": 1993, "month": 4, "day": 17, "hour": 14, "minute": 49,
    "latitude": 36.683333, "longitude": 114.35, "timezone": "Asia/Shanghai",
}


def test_transit_to_natal_emits_orb_auditable_aspects() -> None:
    transit = calculate_transit_to_natal(**_BIRTH, target_date="2026-07-09")

    assert transit["technique"] == "transits"
    assert transit["target_date"] == "2026-07-09"
    assert transit["aspects"]
    assert all(row["orb"] <= row["allowed_orb"] for row in transit["aspects"])


def test_solar_return_calculates_return_moment_and_chart() -> None:
    solar_return = calculate_solar_return(**_BIRTH, target_year=2026)

    assert solar_return["technique"] == "solar_return"
    assert solar_return["target_year"] == 2026
    assert solar_return["return_chart"]["natal"]["planets"]["sun"]["sign"] == "Aries"
    assert solar_return["sun_longitude_delta"] < 0.001


def test_timing_builder_only_contains_requested_techniques() -> None:
    timing = build_timing_techniques(**_BIRTH, transit_date="2026-07-09", solar_return_year=2026)

    assert set(timing) == {"transits", "solar_return"}


def test_secondary_progressions_use_declared_day_for_year_contract() -> None:
    progressions = calculate_secondary_progressions(**_BIRTH, target_date="2026-07-09")

    assert progressions["technique"] == "secondary_progressions"
    assert progressions["method"] == "one_ephemeris_day_per_tropical_year"
    assert progressions["progressed_planets"]["sun"]["longitude"] != progressions["natal_sun_longitude"]
    assert progressions["aspects"]


def test_solar_arc_uses_secondary_progressed_sun_arc() -> None:
    directions = calculate_solar_arc_directions(**_BIRTH, target_date="2026-07-09")

    assert directions["technique"] == "solar_arc_directions"
    assert directions["method"] == "secondary_progressed_sun_arc"
    assert 0 < directions["solar_arc_degrees"] < 40
    assert directions["directed_points"]["sun"]["longitude"] != directions["natal_sun_longitude"]
