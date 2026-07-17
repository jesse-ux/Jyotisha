from scripts.skill_experience import (
    build_rectification_questionnaire,
    build_skill_doctor,
    build_skill_onboarding,
    score_rectification_answers,
    summarize_execution_status,
)


def test_onboarding_requests_only_missing_birth_fields():
    packet = build_skill_onboarding({"year": 1993, "month": 4, "day": 17})

    assert packet["status"] == "needs_birth_data"
    assert packet["entry_mode"] == "pending"
    assert packet["missing_fields"] == ["hour", "minute", "lat", "lon"]
    assert packet["next_action"] == "collect_birth_data"


def test_onboarding_selects_rectification_for_uncertain_time():
    packet = build_skill_onboarding({
        "year": 1993,
        "month": 4,
        "day": 17,
        "hour": 14,
        "minute": 49,
        "lat": 36.68,
        "lon": 114.35,
        "time_uncertainty_minutes": 20,
    })

    assert packet["status"] == "ready"
    assert packet["entry_mode"] == "rectification"
    assert packet["next_action"] == "run_rectification_questionnaire"
    assert packet["first_question"]


def test_execution_status_makes_official_fallback_machine_readable():
    status = summarize_execution_status({
        "fallback_reason": "VedAstro official snapshot blocked: official_snapshot_budget_exhausted",
        "external_engine_cross_validation": {
            "engines": {"VedAstro": {"status": "local_fallback"}}
        },
    })

    assert status["official_evidence_status"] == "official_blocked"
    assert status["calculation_source"] == "local_fallback"
    assert status["fallback_reason"] == "VedAstro official snapshot blocked: official_snapshot_budget_exhausted"
    assert "official_verified" in status["allowed_claims"]


def test_doctor_has_machine_readable_core_and_adapter_state():
    packet = build_skill_doctor()

    assert packet["scope"] == "skill_doctor"
    assert "core_assets" in packet
    assert "external_engine_adapters" in packet
    assert packet["status"] in {"ready", "degraded"}


def test_mcp_exposes_skill_experience_tools():
    import mcp_server

    onboarding = mcp_server.skill_onboarding({})
    doctor = mcp_server.skill_doctor()

    assert onboarding["scope"] == "skill_onboarding"
    assert doctor["scope"] == "skill_doctor"


def test_rectification_contract_generates_and_scores_choice_answers():
    questionnaire = build_rectification_questionnaire({
        "year": 1993, "month": 4, "day": 17, "hour": 14, "minute": 49,
        "time_uncertainty_minutes": 20,
    })
    scored = score_rectification_answers(questionnaire, {
        "education_environment_shift": "A",
        "health_crisis_or_low_period": "C",
    })

    assert questionnaire["scope"] == "active_birth_time_rectification_questionnaire"
    assert scored["scope"] == "active_birth_time_rectification_scoring"
    assert scored["candidate_cluster_rankings"]
