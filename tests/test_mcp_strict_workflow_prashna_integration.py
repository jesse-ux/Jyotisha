#!/usr/bin/env python3
"""Guardrails for Prashna question-moment evidence in strict reports."""

from __future__ import annotations

from copy import deepcopy

import mcp_server


def _strict_report() -> dict:
    return {
        "question_type": "career",
        "present_evidence": {},
        "event_judgement": {
            "score": 72,
            "verdict": "supportive_window",
            "dominant_label": "career_status",
            "primary_drivers": ["dasha_support"],
        },
        "score": 72,
        "verdict": "supportive_window",
        "dominant_label": "career_status",
        "confidence_cap": "medium",
        "technique_audit": [],
        "technique_audit_summary": {},
    }


def _judgement(strict: dict) -> dict:
    event = strict["event_judgement"]
    return {
        "score": strict["score"],
        "verdict": strict["verdict"],
        "dominant_label": strict["dominant_label"],
        "confidence_cap": strict["confidence_cap"],
        "event_score": event["score"],
        "event_verdict": event["verdict"],
        "event_label": event["dominant_label"],
        "primary_drivers": deepcopy(event["primary_drivers"]),
    }


def test_prashna_request_adds_guarded_evidence_without_adjudication_effect(monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.prashna_context.build_prashna_context",
        lambda payload: {
            "scope": "prashna_context",
            "status": "computed",
            "chart_source": "swiss_ephemeris_backend",
            "result_hash": "prashna-hash",
            "blocked_layers": ["Prashna verdict"],
        },
    )
    strict = _strict_report()
    before = _judgement(strict)

    result = mcp_server._attach_prashna_guarded_evidence(
        "career",
        strict,
        question="Will this project succeed?",
        prashna_request={
            "question_timestamp": "2026-07-16T12:00:00+08:00",
            "lat": 31.2304,
            "lon": 121.4737,
            "timezone": 8,
        },
    )

    assert _judgement(result) == before
    assert result["present_evidence"]["prashna_context"]["result_hash"] == "prashna-hash"
    integration = result["present_evidence"]["prashna_integration"]
    assert integration["status"] == "guarded_evidence"
    assert integration["adjudication_effect"] == "none"
    row = next(item for item in result["technique_audit"] if item["technique"] == "Prashna Integration")
    assert row["effect_on_score"] == "none"


def test_prashna_request_rejects_client_chart_injection() -> None:
    result = mcp_server._attach_prashna_guarded_evidence(
        "career",
        _strict_report(),
        question="Will this project succeed?",
        prashna_request={
            "question_timestamp": "2026-07-16T12:00:00+08:00",
            "lat": 31.2304,
            "lon": 121.4737,
            "timezone": 8,
            "planets": {"Sun": 0},
        },
    )

    integration = result["present_evidence"]["prashna_integration"]
    assert integration["status"] == "blocked"
    assert integration["reason"] == "client_supplied_prashna_chart_forbidden:planets"
    assert "prashna_context" not in result["present_evidence"]


def test_prashna_request_requires_question_moment_location() -> None:
    result = mcp_server._attach_prashna_guarded_evidence(
        "career",
        _strict_report(),
        question="Will this project succeed?",
        prashna_request={"question_timestamp": "2026-07-16T12:00:00+08:00"},
    )

    integration = result["present_evidence"]["prashna_integration"]
    assert integration["status"] == "blocked"
    assert integration["reason"] == "missing_prashna_fields:lat,lon,timezone"
