#!/usr/bin/env python3
"""Executable Yoga benchmark cases recovered from older scratch tests."""

from __future__ import annotations

from scripts.yoga_engine import detect_yogas_from_json


RAMAN_STATIC_CHART = {
    "ascendant": "Aquarius",
    "planets": {
        "Sun": {"sign": "Cancer", "house": 6, "degree": 23.0},
        "Moon": {"sign": "Taurus", "house": 4, "degree": 23.5},
        "Mars": {"sign": "Leo", "house": 7, "degree": 21.0},
        "Mercury": {"sign": "Leo", "house": 7, "degree": 14.0},
        "Jupiter": {"sign": "Scorpio", "house": 10, "degree": 13.0},
        "Venus": {"sign": "Leo", "house": 7, "degree": 2.0},
        "Saturn": {"sign": "Taurus", "house": 4, "degree": 10.0},
        "Rahu": {"sign": "Pisces", "house": 2, "degree": 25.0},
        "Ketu": {"sign": "Virgo", "house": 8, "degree": 25.0},
    },
    "context": {
        "d9": {
            "ascendant": "Aries",
        }
    },
}


def test_raman_static_chart_triggers_stable_yoga_rule_ids() -> None:
    detected = detect_yogas_from_json(RAMAN_STATIC_CHART)
    rule_ids = {row.get("rule_id") for row in detected}

    assert len(detected) >= 50
    assert {
        "dharma_karmadhipati",
        "chandra_yoga_exalted",
        "shakti_yoga_9_10_lord",
        "bvr_016_vesi_precise",
        "budha_shukra_yoga",
        "kalatra_yoga_venus_kendra",
        "raja_yoga_5_10_lord",
        "raja_yoga_4_10_lord",
    }.issubset(rule_ids)


def test_raman_static_chart_preserves_yoga_metadata_contract() -> None:
    detected = detect_yogas_from_json(RAMAN_STATIC_CHART)
    by_rule_id = {row.get("rule_id"): row for row in detected}

    dharma = by_rule_id["dharma_karmadhipati"]
    assert dharma["category"] == "raja"
    assert dharma["strength"] == "强"
    assert "9宫主金星Venus" in dharma["combination"]
    assert "10宫主火星Mars" in dharma["combination"]

    chandra = by_rule_id["chandra_yoga_exalted"]
    assert chandra["category"] == "chandra"
    assert chandra["strength"] == "强"
    assert chandra["source"] == "BPHS"
