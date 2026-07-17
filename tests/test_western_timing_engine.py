"""Regression tests for native Western timing calculations."""

from __future__ import annotations

from scripts.western_timing_engine import (
    build_timing_techniques,
    calculate_converse_secondary_progressions,
    calculate_converse_solar_arc_directions,
    calculate_lunar_return,
    calculate_midpoints,
    calculate_parans_status,
    calculate_secondary_progressions,
    calculate_solar_arc_directions,
    calculate_solar_return,
    calculate_transit_duration_scan,
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


def test_converse_progressions_and_solar_arc_are_auditable() -> None:
    progressions = calculate_converse_secondary_progressions(**_BIRTH, target_date="2026-07-09")
    assert progressions["technique"] == "converse_secondary_progressions"
    assert progressions["progressed_angles"]["status"] == "blocked"
    directions = calculate_converse_solar_arc_directions(**_BIRTH, target_date="2026-07-09")
    assert directions["technique"] == "converse_solar_arc_directions"
    assert 0 < directions["converse_solar_arc_degrees"] < 40
    assert directions["directed_points"]["sun"]["longitude"] != directions["natal_sun_longitude"]


def test_midpoints_emit_geometry_and_optional_transit_hits() -> None:
    midpoints = calculate_midpoints(**_BIRTH, target_date="2026-07-09")
    assert midpoints["technique"] == "midpoints"
    assert "sun/moon" in midpoints["natal_midpoints"]
    assert isinstance(midpoints["transit_midpoint_hits"], list)


def test_lunar_return_calculates_next_exact_return_chart() -> None:
    lunar_return = calculate_lunar_return(**_BIRTH, start_date="2026-07-01")
    assert lunar_return["technique"] == "lunar_return"
    assert lunar_return["moon_longitude_delta"] < 0.01
    assert lunar_return["return_chart"]["natal"]["planets"]["moon"]["sign"]


def test_transit_duration_scan_groups_daily_windows() -> None:
    scan = calculate_transit_duration_scan(**_BIRTH, start_date="2026-07-01", end_date="2026-07-03")
    assert scan["technique"] == "transit_duration_scan"
    assert scan["days_scanned"] == 3
    assert len(scan["daily_hits"]) == 3
    assert isinstance(scan["windows"], list)


def test_parans_emit_latitude_aware_angular_events() -> None:
    parans = calculate_parans_status(**_BIRTH, target_date="2026-07-09")
    assert parans["technique"] == "parans"
    assert parans["status"] == "used"
    assert parans["method"].startswith("Swiss Ephemeris rise_trans")
    assert parans["event_count"] > 0


def test_timing_builder_can_emit_advanced_layers() -> None:
    timing = build_timing_techniques(
        **_BIRTH,
        converse_secondary_progression_date="2026-07-09",
        converse_solar_arc_date="2026-07-09",
        midpoint_date="2026-07-09",
        lunar_return_start_date="2026-07-01",
        duration_scan_start_date="2026-07-01",
        duration_scan_end_date="2026-07-02",
        parans_date="2026-07-09",
    )
    assert {
        "converse_secondary_progressions",
        "converse_solar_arc_directions",
        "midpoints",
        "lunar_return",
        "transit_duration_scan",
        "parans",
    } <= set(timing)
    progressed = build_timing_techniques(**_BIRTH, secondary_progression_date="2026-07-09")["secondary_progressions"]
    assert progressed["progressed_angles"]["status"] == "used"
    assert set(progressed["progressed_angles"]["angles"]) == {"ascendant", "mc", "descendant", "ic"}
    parans = timing["parans"]
    assert parans["status"] == "used"
    assert parans["event_count"] > 0
    assert all(row["separation_minutes"] <= 4 for row in parans["paran_pairs_within_4_minutes"])
