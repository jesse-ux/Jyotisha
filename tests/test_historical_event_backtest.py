#!/usr/bin/env python3
"""Regression tests for reusable historical event backtest reporting."""

from __future__ import annotations

from scripts import historical_event_backtest as backtest


def _payload(events: list[dict]) -> dict:
    return {
        "subject": {
            "year": REDACTED_YEAR,
            "month": 4,
            "day": 17,
            "hour": 14,
            "minute": 49,
            "lat": 36.42,
            "lon": 114.2,
            "tz": 8.0,
            "node_mode": "mean",
        },
        "events": events,
    }


def _strict_packet(
    route: str,
    *,
    verdict: str,
    dominant_label: str | None,
    score: int,
    blocked: bool = False,
    confidence_cap: str = "medium-high",
    missing_evidence: list[str] | None = None,
    official_level: str = "primary",
    source_priority_mode: str = "vedastro_official_primary",
) -> dict:
    return {
        "routing": {"question_type": route},
        "strict_workflow": {
            "question_type": route,
            "blocked": blocked,
            "confidence_cap": confidence_cap,
            "missing_evidence": missing_evidence or [],
            "present_evidence": {
                "vedastro_official_snapshot": {
                    "level": official_level,
                    "source": "vedastro_official",
                    "status": "partial" if official_level == "primary" else "fallback",
                },
                "source_priority": {
                    "mode": source_priority_mode,
                    "priority": [
                        "vedastro_official_snapshot",
                        "local_supplemental_modules",
                        "local_engine_fallback_when_official_blocked",
                    ],
                },
            },
            "event_judgement": {
                "event_family": route,
                "verdict": verdict,
                "dominant_label": dominant_label,
                "score": score,
                "primary_drivers": ["vimshottari_current", "narayana_current"],
                "secondary_context": ["functional_benefic_malefic_used"],
            },
            "technique_audit": [
                {
                    "technique": "VedAstro Official Full Snapshot",
                    "status": "used" if official_level == "primary" else "blocked",
                    "role": "primary_raw_evidence",
                }
            ],
            "life_event_graph": {
                "version": "life_event_graph_v1",
                "route": route,
                "dominant_label": dominant_label,
                "verdict": verdict,
                "event_nodes": [],
            },
        },
    }


def test_backtest_reports_strong_hit_with_official_snapshot_priority(monkeypatch) -> None:
    def fake_strict_workflow(**kwargs):
        assert kwargs["transit_date"] == "2019-12-15"
        return _strict_packet(
            "career",
            verdict="high_probability_window",
            dominant_label="career_status",
            score=84,
        )

    monkeypatch.setattr(backtest.mcp_server, "strict_workflow", fake_strict_workflow)

    report = backtest.build_report(
        _payload(
            [
                {
                    "id": "career_turn_2019",
                    "date": "2019-12-15",
                    "domain": "career",
                    "expected_label": "career_status",
                    "summary": "事业逐渐好转",
                }
            ]
        )
    )

    assert report["scope"] == "historical_event_backtest"
    assert report["summary"]["total_events"] == 1
    assert report["summary"]["strong_hits"] == 1
    assert report["summary"]["official_primary_events"] == 1
    event = report["events"][0]
    assert event["route"] == "career"
    assert event["result_class"] == "strong_hit"
    assert event["official_snapshot"]["level"] == "primary"
    assert event["evidence"]["source_priority_mode"] == "vedastro_official_primary"
    assert event["matched_expected_label"] is True


def test_backtest_marks_blocked_and_unsupported_domains(monkeypatch) -> None:
    def fake_strict_workflow(**kwargs):
        return _strict_packet(
            "relationship",
            verdict="insufficient_evidence",
            dominant_label=None,
            score=28,
            blocked=True,
            confidence_cap="low",
            missing_evidence=["d9_navamsa", "upapada_lagna"],
            official_level="fallback",
            source_priority_mode="local_fallback_only",
        )

    monkeypatch.setattr(backtest.mcp_server, "strict_workflow", fake_strict_workflow)

    report = backtest.build_report(
        _payload(
            [
                {
                    "id": "marriage_probe",
                    "date": "2026-06-09",
                    "domain": "marriage",
                    "expected_label": "legal_marriage",
                },
                {
                    "id": "move_1999",
                    "date": "1999-08-01",
                    "domain": "move",
                    "summary": "搬家",
                },
            ]
        )
    )

    assert report["summary"]["blocked_events"] == 1
    assert report["summary"]["unsupported_domain_events"] == 1
    blocked, unsupported = report["events"]
    assert blocked["result_class"] == "blocked"
    assert blocked["boundary"]["reason"] == "strict_workflow_blocked"
    assert unsupported["result_class"] == "unsupported_domain"
    assert unsupported["boundary"]["reason"] == "route_not_yet_implemented_for_event_backtest"


def test_backtest_distinguishes_weak_hit_and_miss(monkeypatch) -> None:
    def fake_strict_workflow(**kwargs):
        if kwargs["transit_date"] == "2025-02-28":
            return _strict_packet(
                "finance",
                verdict="moderate_probability_window",
                dominant_label="income_growth",
                score=66,
            )
        return _strict_packet(
            "career",
            verdict="insufficient_evidence",
            dominant_label=None,
            score=22,
            confidence_cap="low",
        )

    monkeypatch.setattr(backtest.mcp_server, "strict_workflow", fake_strict_workflow)

    report = backtest.build_report(
        _payload(
            [
                {
                    "id": "project_end_cashflow",
                    "date": "2025-02-28",
                    "domain": "wealth",
                    "expected_label": "public_wealth_status",
                    "summary": "项目结束但收到小额定金",
                },
                {
                    "id": "career_false_start",
                    "date": "2026-01-10",
                    "domain": "career",
                    "expected_label": "project_manifestation",
                    "summary": "短期项目未成",
                },
            ]
        )
    )

    assert report["summary"]["weak_hits"] == 1
    assert report["summary"]["misses"] == 1
    first, second = report["events"]
    assert first["result_class"] == "weak_hit"
    assert first["matched_expected_label"] is False
    assert first["boundary"]["reason"] == "label_mismatch_under_supported_route"
    assert second["result_class"] == "miss"
    assert second["boundary"]["reason"] == "insufficient_evidence"


def test_backtest_carries_conflicts_and_blocked_items_from_strict_contract(monkeypatch) -> None:
    def fake_strict_workflow(**kwargs):
        packet = _strict_packet(
            "career",
            verdict="high_probability_window",
            dominant_label="career_status",
            score=84,
        )
        packet["strict_workflow"]["blocked_items"] = ["official_event_radar_partial"]
        packet["strict_workflow"]["conflicts"] = [{"type": "official_local_dasha_conflict"}]
        return packet

    monkeypatch.setattr(backtest.mcp_server, "strict_workflow", fake_strict_workflow)

    report = backtest.build_report(
        _payload(
            [
                {
                    "id": "career_turn_2019",
                    "date": "2019-12-15",
                    "domain": "career",
                    "expected_label": "career_status",
                    "summary": "事业逐渐好转",
                }
            ]
        )
    )

    assert report["events"][0]["evidence"]["blocked_items"] == ["official_event_radar_partial"]
    assert report["events"][0]["evidence"]["conflicts"] == [{"type": "official_local_dasha_conflict"}]


def test_backtest_carries_top_reader_contract_summary_from_strict_contract(monkeypatch) -> None:
    def fake_strict_workflow(**kwargs):
        packet = _strict_packet(
            "career",
            verdict="high_probability_window",
            dominant_label="career_status",
            score=84,
        )
        packet["strict_workflow"]["adjudication_stages"] = {
            "promise": {"status": "present"},
            "activation": {
                "status": "present",
                "required_timing_systems": ["Vimshottari", "Narayana"],
            },
        }
        packet["strict_workflow"]["multi_reference_reading_summary"] = {
            "root_frame": {"signal": "career_promise"},
            "modifier_frame": {"functional_benefic_malefic": {"used": True}},
        }
        packet["strict_workflow"]["main_conflicts"] = [{"type": "official_local_dasha_conflict"}]
        return packet

    monkeypatch.setattr(backtest.mcp_server, "strict_workflow", fake_strict_workflow)

    report = backtest.build_report(
        _payload(
            [
                {
                    "id": "career_turn_2019",
                    "date": "2019-12-15",
                    "domain": "career",
                    "expected_label": "career_status",
                    "summary": "事业逐渐好转",
                }
            ]
        )
    )

    event = report["events"][0]
    assert event["evidence"]["adjudication_stages"]["activation"]["required_timing_systems"] == [
        "Vimshottari",
        "Narayana",
    ]
    assert event["evidence"]["multi_reference_reading_summary"]["root_frame"]["signal"] == "career_promise"
    assert event["evidence"]["main_conflicts"] == [{"type": "official_local_dasha_conflict"}]
