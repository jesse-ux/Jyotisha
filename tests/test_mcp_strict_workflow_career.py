#!/usr/bin/env python3
"""Regression tests for MCP career event adjudication."""

from __future__ import annotations

from mcp_server import _collect_strict_evidence


def _base_career_result() -> dict:
    return {
        "modules": {
            "varga_full": {"D10_Dasamsa": {"summary": "career varga present"}},
            "special_lagnas": {"A10_Karma_Pada": {"sign": "Capricorn", "lord": "Saturn"}},
            "jaimini": {
                "karakas": {
                    "Amatyakaraka": {"planet": "Mercury"},
                    "Atmakaraka": {"planet": "Sun"},
                },
                "karakamsha": {"karakamsha_sign": "Leo", "karakamsha_lord": "Sun"},
            },
            "dasha": {"current_dasha": {"mahadasha": "Mercury", "antardasha": "Sun"}},
            "narayana_dasha": {"current_dasha": {"sign": "Capricorn", "lord": "Saturn"}},
            "dasa_convergence": {
                "domain_activations": {
                    "career_status": {"convergence_level": "L2", "probability": "35-50%"}
                }
            },
            "argala": {
                "houses": {
                    "house_10": {
                        "net_result": "supported",
                        "argala_count": 2,
                        "virodhargala_count": 0,
                    }
                }
            },
        }
    }


def test_career_collects_a10_amk_karakamsha_as_strict_evidence() -> None:
    strict = _collect_strict_evidence("career", _base_career_result())

    assert strict["question_type"] == "career"
    assert strict["present_evidence"]["d10_dasamsa"] == {"summary": "career varga present"}
    assert strict["present_evidence"]["a10_karma_pada"] == {"sign": "Capricorn", "lord": "Saturn"}
    assert strict["present_evidence"]["amatyakaraka"] == {"planet": "Mercury"}
    assert strict["present_evidence"]["karakamsha"] == {
        "karakamsha_sign": "Leo",
        "karakamsha_lord": "Sun",
    }
    assert strict["event_judgement"]["event_family"] == "career"
    assert strict["event_judgement"]["dominant_label"] == "career_status"
    assert strict["event_judgement"]["secondary_context"] == [
        "a10_active",
        "amk_active",
        "karakamsha_context",
        "argala_support",
    ]


def test_career_blocks_label_when_d10_is_missing_but_preserves_jaimini_context() -> None:
    result = _base_career_result()
    del result["modules"]["varga_full"]["D10_Dasamsa"]

    strict = _collect_strict_evidence("career", result)

    assert "d10_dasamsa" in strict["missing_evidence"]
    assert strict["blocked"] is True
    assert strict["event_judgement"]["dominant_label"] is None
    assert strict["event_judgement"]["secondary_context"] == [
        "a10_active",
        "amk_active",
        "karakamsha_context",
        "argala_support",
    ]


def test_career_argala_bridge_uses_tenth_house_as_modifier_only() -> None:
    result = _base_career_result()

    strict = _collect_strict_evidence("career", result)

    assert strict["present_evidence"]["argala_support"] == {
        "level": "supportive",
        "target_house": 10,
        "source": "argala_house_bridge_v1",
        "signals": ["argala_support"],
        "raw": {
            "net_result": "supported",
            "argala_count": 2,
            "virodhargala_count": 0,
        },
    }
    assert strict["event_judgement"]["dominant_label"] == "career_status"
    assert "argala_support" in strict["event_judgement"]["secondary_context"]
