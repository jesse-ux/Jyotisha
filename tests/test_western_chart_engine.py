"""Regression tests for the native tropical Western chart calculator."""

from __future__ import annotations

from scripts.western_chart_engine import (
    build_tropical_natal_chart,
    build_tropical_western_evidence_packet,
)
from scripts.jyotish_api_server import _western_evidence_packet_from_body
from scripts.skill_release_package import _edition_files


_BIRTH = {
    "year": 1993,
    "month": 4,
    "day": 17,
    "hour": 14,
    "minute": 49,
    "latitude": 36.683333,
    "longitude": 114.35,
    "timezone": "Asia/Shanghai",
}


def test_native_engine_calculates_auditable_tropical_natal_chart() -> None:
    chart = build_tropical_natal_chart(**_BIRTH)

    assert chart["source_engine"] == "pyswisseph_tropical"
    assert chart["zodiac"] == "tropical"
    assert chart["house_system"] == "P"
    assert chart["natal"]["planets"]["sun"]["sign"] == "Aries"
    assert 26 < chart["natal"]["planets"]["sun"]["longitude"] < 28
    assert set(chart["natal"]["angles"]) == {"ascendant", "mc", "descendant", "ic"}
    assert len(chart["natal"]["houses"]) == 12
    assert all(1 <= planet["house"] <= 12 for planet in chart["natal"]["planets"].values())
    assert chart["natal"]["aspects"]
    assert all(aspect["orb"] <= aspect["allowed_orb"] for aspect in chart["natal"]["aspects"])


def test_native_engine_marks_timing_and_interpretation_boundaries() -> None:
    packet = build_tropical_western_evidence_packet(**_BIRTH, route_packet={"primary_theme": "career"})

    assert packet["status"] == "partial"
    assert packet["calculation"]["status"] == "used"
    assert packet["calculation"]["source_engine"] == "pyswisseph_tropical"
    assert "timing_techniques" in packet["missing_sections"]
    assert "signals" in packet["missing_sections"]
    assert "does not calculate transits" in packet["boundary"]


def test_workflow_auto_materializes_native_western_natal_without_external_json() -> None:
    packet = _western_evidence_packet_from_body(
        {"entry_mode": "direct_chart", "western_mode": "auto"},
        {"primary_theme": "career"},
        birth_payload={
            "year": 1993, "month": 4, "day": 17, "hour": 14, "minute": 49,
            "second": 0, "lat": 36.683333, "lon": 114.35, "tz": 8,
        },
    )

    assert packet is not None
    assert packet["source_engine"] == "pyswisseph_tropical"
    assert packet["status"] == "partial"


def test_workflow_does_not_auto_attach_natal_western_data_to_prashna() -> None:
    packet = _western_evidence_packet_from_body(
        {"entry_mode": "prashna", "western_mode": "auto"},
        {"primary_theme": "career"},
        birth_payload={
            "year": 1993, "month": 4, "day": 17, "hour": 14, "minute": 49,
            "second": 0, "lat": 36.683333, "lon": 114.35, "tz": 8,
        },
    )

    assert packet is None


def test_workflow_adds_only_explicit_western_timing_layers() -> None:
    packet = _western_evidence_packet_from_body(
        {
            "entry_mode": "direct_chart",
            "western_timing": {
                "transit_date": "2026-07-09",
                "solar_return_year": 2026,
                "secondary_progression_date": "2026-07-09",
                "solar_arc_date": "2026-07-09",
            },
        },
        {"primary_theme": "career"},
        birth_payload={
            "year": 1993, "month": 4, "day": 17, "hour": 14, "minute": 49,
            "second": 0, "lat": 36.683333, "lon": 114.35, "tz": 8,
        },
    )

    assert set(packet["timing_techniques"]) == {
        "transits", "solar_return", "secondary_progressions", "solar_arc_directions",
    }
    assert packet["sections"]["timing_techniques"]["status"] == "used"


def test_release_editions_include_native_western_calculator() -> None:
    assert "scripts/western_chart_engine.py" in _edition_files("basic_git")
    assert "scripts/western_chart_engine.py" in _edition_files("premium_cloud_drive")
    assert "scripts/western_timing_engine.py" in _edition_files("basic_git")
    assert "scripts/western_timing_engine.py" in _edition_files("premium_cloud_drive")
