#!/usr/bin/env python3
"""Tests for the shared consultation orchestrator contract."""

from __future__ import annotations

from scripts.unified_consultation_orchestrator import UnifiedConsultationOrchestrator


def test_unified_consultation_orchestrator_normalizes_themes_and_route() -> None:
    orchestrator = UnifiedConsultationOrchestrator()

    themes = orchestrator.normalize_themes(["事业", "relationship", "money"])
    route = orchestrator.resolve_route("我想看事业和工作机会", themes)

    assert themes == ["career", "marriage", "wealth"]
    assert route["question_type"] == "career"
    assert route["primary_theme"] == "career"
    assert "D10" in route["focus_techniques"]


def test_unified_consultation_orchestrator_exposes_surface_agnostic_contract() -> None:
    orchestrator = UnifiedConsultationOrchestrator()
    route = orchestrator.resolve_route("When will I marry?", ["marriage"])

    contract = orchestrator.shared_contract(
        entry_mode="direct_chart",
        question="When will I marry?",
        themes=["marriage"],
        route_packet=route,
        surface="skill_mcp",
    )

    assert contract["name"] == "UnifiedConsultationOrchestrator"
    assert contract["surface"] == "skill_mcp"
    assert contract["entry_mode"] == "direct_chart"
    assert contract["route"]["question_type"] == "relationship"
    assert contract["themes"] == ["marriage"]
    assert contract["source_priority"]["mode"] == "vedastro_official_snapshot_first"
    assert contract["source_priority"]["priority"][0] == "vedastro_official_snapshot"


def test_unified_consultation_orchestrator_builds_runtime_planner() -> None:
    orchestrator = UnifiedConsultationOrchestrator()
    themes = orchestrator.normalize_themes(["career", "wealth"])
    route = orchestrator.resolve_route("请直接排盘并重点看事业收入", themes)

    planner = orchestrator.runtime_planner(
        entry_mode="direct_chart",
        question="请直接排盘并重点看事业收入",
        themes=themes,
        route_packet=route,
        events=[{"id": "career_turn_2019"}],
        surface="api_web",
        high_rigor=False,
    )

    assert planner["planner_name"] == "UnifiedConsultationRuntimePlanner"
    assert planner["entry_mode"] == "direct_chart"
    assert planner["route"]["question_type"] == "career"
    assert planner["sync_steps"][0] == "compute_chart"
    assert "run_thematic_report" in planner["sync_steps"]
    assert planner["async_candidates"][0] == "historical_event_backtest"
    assert planner["source_priority"]["priority"][0] == "vedastro_official_snapshot"
    assert planner["question_context"]["event_count"] == 1


def test_unified_consultation_orchestrator_rectification_entry_runs_gate_first() -> None:
    orchestrator = UnifiedConsultationOrchestrator()
    themes = orchestrator.normalize_themes(["marriage"])
    route = orchestrator.resolve_route("我想先校正出生时间再看婚恋", themes)

    planner = orchestrator.runtime_planner(
        entry_mode="rectification",
        question="我想先校正出生时间再看婚恋",
        themes=themes,
        route_packet=route,
        events=[{"id": "relationship_turn_2015"}],
        surface="api_web",
        high_rigor=False,
    )

    assert planner["entry_mode"] == "rectification"
    assert planner["sync_steps"][0] == "run_rectification_gate"
    assert "compute_chart" in planner["sync_steps"]
    assert "run_thematic_report" in planner["sync_steps"]
