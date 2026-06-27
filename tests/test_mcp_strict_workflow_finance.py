#!/usr/bin/env python3
"""Regression tests for MCP finance event adjudication."""

from __future__ import annotations

from mcp_server import _collect_strict_evidence, _derive_event_judgement


def test_finance_public_wealth_label_requires_at_least_moderate_window() -> None:
    judgement = _derive_event_judgement(
        "finance",
        {
            "wealth_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "gains_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "career_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "vimshottari_current": {"mahadasha": "Venus", "antardasha": "Mercury"},
            "narayana_current": {"sign": "Taurus", "lord": "Venus"},
        },
        [],
    )

    assert judgement["event_family"] == "finance"
    assert judgement["score"] == 40
    assert judgement["verdict"] == "weak_window_needs_confirmation"
    assert judgement["payout_label"] is None


def test_finance_public_wealth_label_can_lift_visible_wealth_cases() -> None:
    judgement = _derive_event_judgement(
        "finance",
        {
            "wealth_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "gains_convergence": {"convergence_level": "L2", "probability": "35-50%"},
            "career_convergence": {"convergence_level": "L2", "probability": "35-50%"},
            "vimshottari_current": {"mahadasha": "Jupiter", "antardasha": "Venus"},
            "narayana_current": {"sign": "Libra", "lord": "Venus"},
        },
        [],
    )

    assert judgement["event_family"] == "finance"
    assert judgement["score"] == 60
    assert judgement["verdict"] == "moderate_probability_window"
    assert judgement["payout_label"] == "public_wealth_status"


def test_finance_prefers_income_growth_when_gains_outrun_public_status_signals() -> None:
    judgement = _derive_event_judgement(
        "finance",
        {
            "wealth_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "gains_convergence": {"convergence_level": "L3", "probability": "50-65%"},
            "vimshottari_current": {"mahadasha": "Venus", "antardasha": "Moon"},
            "narayana_current": {"sign": "Gemini", "lord": "Mercury"},
        },
        [],
    )

    assert judgement["event_family"] == "finance"
    assert judgement["score"] == 80
    assert judgement["verdict"] == "moderate_probability_window"
    assert judgement["payout_label"] == "income_growth"


def test_finance_strong_wealth_promise_can_unlock_public_wealth_status() -> None:
    judgement = _derive_event_judgement(
        "finance",
        {
            "wealth_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "gains_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "career_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "vimshottari_current": {"mahadasha": "Venus", "antardasha": "Mercury"},
            "narayana_current": {"sign": "Taurus", "lord": "Venus"},
            "wealth_promise_strength": {"level": "strong", "source": "dhana_yogas"},
        },
        [],
    )

    assert judgement["event_family"] == "finance"
    assert judgement["score"] == 60
    assert judgement["verdict"] == "moderate_probability_window"
    assert judgement["payout_label"] == "public_wealth_status"


def test_collect_strict_evidence_finance_derives_wealth_promise_from_dhana_yogas() -> None:
    result = {
        "modules": {
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {"planets": {"Venus": {"total_rupa": 8.2}}},
            "ashtakavarga": {"house_scores": {"2": 31, "11": 36}},
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                    "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    "career_status": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
            "yogas_doshas": {
                "dhana_yogas": {
                    "yogas": [
                        {"type": "Dhana Yoga", "strength": "strong"},
                        {"type": "Dhana Yoga", "strength": "moderate"},
                    ],
                    "summary": "Dhana Yoga检测：共2个格局",
                }
            },
        }
    }

    strict = _collect_strict_evidence("finance", result)
    present = strict["present_evidence"]
    assert present["wealth_promise_strength"] == {
        "level": "strong",
        "source": "dhana_yogas",
        "count": 2,
    }
    assert strict["event_judgement"]["score"] == 100
    assert strict["event_judgement"]["verdict"] == "moderate_probability_window"
    assert strict["event_judgement"]["payout_label"] == "public_wealth_status"
