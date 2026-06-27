#!/usr/bin/env python3
"""Regression coverage for Lakshmi Yoga truth path in the main yoga engine."""

from __future__ import annotations

from scripts.yoga_engine import detect_yogas


RULES_PATH = "references/yoga_rules.json"


def _has_rule(results: list[dict], rule_id: str) -> bool:
    return any(item.get("rule_id") == rule_id for item in results)


def test_lakshmi_yoga_detects_when_ninth_lord_is_strong_in_lagna() -> None:
    planets = {
        "Sun": {"house": 1, "sign": "Aries", "degree": 10.0},
        "Moon": {"house": 2, "sign": "Taurus", "degree": 15.0},
        "Mars": {"house": 3, "sign": "Gemini", "degree": 20.0},
        "Mercury": {"house": 1, "sign": "Aries", "degree": 12.0},
        "Jupiter": {"house": 4, "sign": "Cancer", "degree": 18.0},
        "Venus": {"house": 7, "sign": "Libra", "degree": 5.0},
        "Saturn": {"house": 10, "sign": "Capricorn", "degree": 2.0},
        "Rahu": {"house": 11, "sign": "Aquarius", "degree": 8.0},
        "Ketu": {"house": 5, "sign": "Leo", "degree": 8.0},
    }

    results = detect_yogas(planets, "Aries", RULES_PATH)

    assert _has_rule(results, "lakshmi_yoga")


def test_lakshmi_yoga_rejects_when_ninth_lord_is_not_strong() -> None:
    planets = {
        "Sun": {"house": 1, "sign": "Aries", "degree": 10.0},
        "Moon": {"house": 2, "sign": "Taurus", "degree": 15.0},
        "Mars": {"house": 3, "sign": "Gemini", "degree": 20.0},
        "Mercury": {"house": 1, "sign": "Aries", "degree": 12.0},
        "Jupiter": {"house": 8, "sign": "Scorpio", "degree": 18.0},
        "Venus": {"house": 7, "sign": "Libra", "degree": 5.0},
        "Saturn": {"house": 10, "sign": "Capricorn", "degree": 2.0},
        "Rahu": {"house": 11, "sign": "Aquarius", "degree": 8.0},
        "Ketu": {"house": 5, "sign": "Leo", "degree": 8.0},
    }

    results = detect_yogas(planets, "Aries", RULES_PATH)

    assert not _has_rule(results, "lakshmi_yoga")
