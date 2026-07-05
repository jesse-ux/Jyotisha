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


def test_unified_consultation_orchestrator_prashna_entry_runs_prashna_before_thematic() -> None:
    orchestrator = UnifiedConsultationOrchestrator()
    themes = orchestrator.normalize_themes(["wealth"])
    route = orchestrator.resolve_route("时间问事：这个合作能成吗", themes)

    planner = orchestrator.runtime_planner(
        entry_mode="prashna",
        question="时间问事：这个合作能成吗",
        themes=themes,
        route_packet=route,
        events=[],
        surface="api_web",
        high_rigor=False,
    )

    assert planner["entry_mode"] == "prashna"
    assert planner["sync_steps"][0] == "run_prashna"
    assert "compute_chart" not in planner["sync_steps"]


def test_unified_consultation_orchestrator_timing_route_adds_muhurta_sidecar() -> None:
    orchestrator = UnifiedConsultationOrchestrator()
    themes = orchestrator.normalize_themes(["career"])
    route = orchestrator.resolve_route("2026年何时适合谈合作和推进项目的应期", themes)
    planner = orchestrator.runtime_planner(
        entry_mode="direct_chart",
        question="2026年何时适合谈合作和推进项目的应期",
        themes=themes,
        route_packet=route,
        events=[],
        surface="api_web",
        high_rigor=False,
    )
    assert planner["route"]["question_type"] == "timing"
    assert "run_muhurta_panchanga" in planner["sync_steps"]
    assert planner["sync_steps"].index("run_muhurta_panchanga") < planner["sync_steps"].index("run_thematic_report")


def test_unified_consultation_orchestrator_prefers_timing_when_career_question_asks_when() -> None:
    orchestrator = UnifiedConsultationOrchestrator()
    themes = orchestrator.normalize_themes(["career"])
    route = orchestrator.resolve_route("2026年什么时候会有事业机会", themes)
    assert route["question_type"] == "timing"


def test_runtime_evidence_log_classifies_official_verified_local_fallback_and_blocked() -> None:
    orchestrator = UnifiedConsultationOrchestrator()
    route = {"question_type": "career", "primary_theme": "career"}

    verified = orchestrator.runtime_evidence_log(
        surface="api_web",
        entry_mode="direct_chart",
        route_packet=route,
        executed_steps=["compute_chart"],
        skipped_steps=[],
        vedastro_official={
            "runtime_truth": {
                "status": "ok",
                "official_execution_layers": {"chart_core": "ok"},
                "fallback_active": False,
            },
            "raw_response": {"source": "official"},
        },
    )
    assert verified["vedastro_cloud_state"] == "official_verified"

    fallback = orchestrator.runtime_evidence_log(
        surface="skill_mcp",
        entry_mode="direct_chart",
        route_packet=route,
        executed_steps=["compute_chart"],
        skipped_steps=[],
        vedastro_official={"runtime_truth": {"status": "network_execution_disabled", "fallback_active": True}},
    )
    assert fallback["vedastro_cloud_state"] == "local_fallback"

    blocked = orchestrator.runtime_evidence_log(
        surface="skill_mcp",
        entry_mode="direct_chart",
        route_packet=route,
        executed_steps=[],
        skipped_steps=["compute_chart"],
        vedastro_official={"runtime_truth": {"status": "service_endpoint_not_configured", "fallback_active": False}},
    )
    assert blocked["vedastro_cloud_state"] == "official_blocked"


def test_runtime_evidence_log_exposes_blind_packet_case_and_quality_gate_contracts() -> None:
    orchestrator = UnifiedConsultationOrchestrator()
    log = orchestrator.runtime_evidence_log(
        surface="api_web",
        entry_mode="direct_chart",
        route_packet={"question_type": "finance", "primary_theme": "wealth"},
        executed_steps=["compute_chart", "run_thematic_report"],
        skipped_steps=["run_historical_event_backtest"],
        vedastro_official={"runtime_truth": {"status": "partial", "fallback_active": True}},
        blind=True,
    )

    assert log["blind_technical_mode"]["enabled"] is True
    assert "conversation_feedback" in log["blind_technical_mode"]["disallowed_sources"]
    assert log["evidence_packet_contract"]["required_sections"][:5] == ["D1", "D9", "D10", "D2", "D4"]
    assert "external_oracle_status" in log["evidence_packet_contract"]["required_sections"]
    assert log["real_case_calibration"]["status"] == "required_not_satisfied"
    assert log["quality_gate"]["technique_audit_table_required"] is True
    assert [row["technique"] for row in log["quality_gate"]["technique_audit_table"]] == [
        "VedAstro Cloud State",
        "External Engine Cross-Validation",
        "Evidence Packet",
        "Blind Technical Mode",
        "MEVG / Global Web Evidence",
        "Real Case Calibration",
        "Functional Benefic/Malefic",
    ]
    engines = log["external_engine_cross_validation"]["engines"]
    assert engines["VedAstro"]["status"] == "local_fallback"
    assert engines["PyJHora/JHora"]["status"] == "reference_available_not_runtime_invoked"
    assert engines["PyJHora/JHora"]["adapter_command"] == "python3 benchmarks/jyotish/scripts/run_pyjhora_compare.py"
    assert engines["PyJHora/JHora"]["adapter_status"] in {
        "available",
        "blocked_missing_python_module:jhora",
    }
    assert engines["jyotishganit"]["status"] == "reference_available_not_runtime_invoked"
    assert engines["jyotishganit"]["adapter_path"] == "references/open_source_sources/jyotishganit"
    assert engines["jyotishganit"]["adapter_status"] == "available"
    assert engines["jyotishganit"]["license"] == "MIT"
    assert log["external_engine_cross_validation"]["status"] == "partial"
    assert log["quality_gate"]["blocked_items"]

    packet = orchestrator.machine_evidence_packet(
        chart={"chart": {"planets": {"Sun": {}}, "ascendant": {"sign": "Leo"}}},
        route_packet={"question_type": "career", "primary_theme": "career"},
    )
    log_with_functional = orchestrator.runtime_evidence_log(
        surface="api_web",
        entry_mode="direct_chart",
        route_packet={"question_type": "career", "primary_theme": "career"},
        executed_steps=["compute_chart"],
        skipped_steps=[],
        machine_evidence_packet=packet,
    )
    functional_row = log_with_functional["quality_gate"]["technique_audit_table"][-1]
    assert functional_row["technique"] == "Functional Benefic/Malefic"
    assert functional_row["status"] == "used"
    assert "Mars" in functional_row["yogakarakas"]


def test_machine_evidence_packet_materializes_required_section_statuses() -> None:
    orchestrator = UnifiedConsultationOrchestrator()
    packet = orchestrator.machine_evidence_packet(
        chart={
            "chart": {
                "planets": {"Sun": {"lon": 12.3}},
                "ascendant": {"lon": 91.2, "sign": "Leo"},
                "houses": {"1": {"lon": 91.2}},
            },
            "modules": {
                "varga_full": {"D9_Navamsa": {}, "D10_Dasamsa": {"summary": "present"}},
                "dasha": {"current": "Saturn"},
                "shadbala": {"Sun": 1.0},
            },
            "special_lagnas": {"UL": {"sign": "Capricorn"}, "A10_Karma_Pada": {"sign": "Aries"}},
        },
        route_packet={"question_type": "career", "primary_theme": "career"},
        vedastro_official={
            "runtime_truth": {
                "status": "ok",
                "official_execution_layers": {"chart_core": "ok"},
                "fallback_active": False,
            },
            "raw_response": {"source": "official"},
        },
    )

    assert packet["status"] == "partial"
    assert packet["sections"]["D1"]["status"] == "used"
    assert packet["sections"]["D10"]["status"] == "used"
    assert packet["sections"]["functional_benefic_malefic"]["status"] == "used"
    assert packet["functional_benefic_malefic"]["ascendant"] == "Leo"
    assert "Mars" in packet["functional_benefic_malefic"]["yogakarakas"]
    assert packet["sections"]["external_oracle_status"]["status"] == "official_verified"
    assert packet["sections"]["vedastro_official_raw_response"]["status"] == "used"
    assert "D2" in packet["missing_sections"]


def test_machine_evidence_packet_requires_vedastro_raw_response_for_official_closure() -> None:
    packet = UnifiedConsultationOrchestrator().machine_evidence_packet(
        chart={"chart": {"planets": {"Sun": {}}, "ascendant": {"sign": "Leo"}}},
        route_packet={"question_type": "career"},
        vedastro_official={
            "runtime_truth": {
                "status": "ok",
                "official_execution_layers": {"chart_core": "ok"},
                "fallback_active": False,
            }
        },
    )

    assert packet["sections"]["external_oracle_status"]["status"] == "official_verified"
    assert packet["sections"]["vedastro_official_raw_response"]["status"] == "missing"
    assert "vedastro_official_raw_response" in packet["missing_sections"]


def test_real_case_calibration_catalog_exposes_local_sources_without_claiming_match() -> None:
    orchestrator = UnifiedConsultationOrchestrator()
    packet = orchestrator.machine_evidence_packet(
        chart={
            "chart": {"planets": {"Venus": {"lon": 1}}, "ascendant": {"lon": 2}},
            "modules": {"varga_full": {"D9_Navamsa": {"summary": "present"}}, "dasha": {"current": "Venus"}},
            "special_lagnas": {"UL": {"sign": "Cancer"}},
        },
        route_packet={"question_type": "relationship", "primary_theme": "marriage"},
    )
    catalog = orchestrator.real_case_calibration_catalog(
        route_packet={"question_type": "relationship", "primary_theme": "marriage"},
        machine_evidence_packet=packet,
    )

    assert catalog["status"] == "partial_scored"
    assert catalog["batch_id"] == "real_case_studies_batch1"
    assert "relationship" in catalog["case_index_by_domain"]
    assert catalog["reference_grade"] == "partial_reference"
    assert catalog["scored_candidates"][0]["event_trigger_match"]["status"] == "partial_match_official_timing_blocked"
    assert catalog["scored_candidates"][0]["event_trigger_match"]["checks"]["dasha_boundaries"] == "used"
    assert catalog["scored_candidates"][0]["event_trigger_match"]["checks"]["recorded_trigger_keywords"]
    assert catalog["scored_candidates"][0]["outcome_validation"]["status"] == "local_outcome_recorded_trigger_not_replayed"
    assert "D9" in catalog["scored_candidates"][0]["similarities"]["evidence_section_overlap"]
