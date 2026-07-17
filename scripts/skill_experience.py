"""Stable user-facing contracts shared by Skill and MCP entry points."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.active_rectification_questions import build_questionnaire, score_answers
from scripts.diagnose_external_engine_adapters import build_report as adapter_report


ROOT = Path(__file__).resolve().parents[1]
_REQUIRED_BIRTH_FIELDS = ("year", "month", "day", "hour", "minute", "lat", "lon")


def _missing_birth_fields(payload: dict[str, Any]) -> list[str]:
    return [field for field in _REQUIRED_BIRTH_FIELDS if payload.get(field) is None]


def build_skill_onboarding(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the next minimal user action; never infer missing birth inputs."""
    payload = payload or {}
    missing = _missing_birth_fields(payload)
    if missing:
        return {
            "scope": "skill_onboarding",
            "status": "needs_birth_data",
            "entry_mode": "pending",
            "missing_fields": missing,
            "next_action": "collect_birth_data",
            "input_template": {
                "year": "YYYY", "month": "MM", "day": "DD",
                "hour": "0-23", "minute": "0-59", "lat": "decimal", "lon": "decimal",
                "time_uncertainty_minutes": "optional; use when birth time is approximate",
                "question": "optional; career, relationship, wealth, health, general",
            },
        }

    uncertainty = int(payload.get("time_uncertainty_minutes") or 0)
    if uncertainty > 0:
        birth_time = (
            f"{int(payload['year']):04d}-{int(payload['month']):02d}-{int(payload['day']):02d} "
            f"{int(payload['hour']):02d}:{int(payload['minute']):02d}"
        )
        questionnaire = build_questionnaire(birth_time, uncertainty_minutes=uncertainty)
        first_question = questionnaire.get("questions", [{}])[0]
        return {
            "scope": "skill_onboarding",
            "status": "ready",
            "entry_mode": "rectification",
            "next_action": "run_rectification_questionnaire",
            "first_question": first_question,
            "questionnaire": questionnaire,
        }

    return {
        "scope": "skill_onboarding",
        "status": "ready",
        "entry_mode": "direct_chart",
        "next_action": "run_consultation_workflow",
        "question": str(payload.get("question") or ""),
    }


def build_rectification_questionnaire(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the active-choice questionnaire from a minimal approximate time."""
    required = ("year", "month", "day", "hour", "minute")
    missing = [field for field in required if payload.get(field) is None]
    if missing:
        raise ValueError(f"missing rectification fields: {', '.join(missing)}")
    birth_time = (
        f"{int(payload['year']):04d}-{int(payload['month']):02d}-{int(payload['day']):02d} "
        f"{int(payload['hour']):02d}:{int(payload['minute']):02d}"
    )
    uncertainty = max(int(payload.get("time_uncertainty_minutes") or 30), 1)
    step = max(int(payload.get("step_minutes") or 1), 1)
    return build_questionnaire(birth_time, uncertainty_minutes=uncertainty, step_minutes=step)


def score_rectification_answers(questionnaire: dict[str, Any], answers: dict[str, str]) -> dict[str, Any]:
    """Score user choices; preserves the boundary against false minute precision."""
    return score_answers(questionnaire, answers or {})


def build_skill_doctor() -> dict[str, Any]:
    """Expose readiness, not an unsupported promise that all engines are usable."""
    assets = {
        "skill_instructions": (ROOT / "SKILL.md").is_file(),
        "mcp_server": (ROOT / "mcp_server.py").is_file(),
        "native_engine": (ROOT / "scripts" / "jyotish_engine.py").is_file(),
        "unified_orchestrator": (ROOT / "scripts" / "unified_consultation_orchestrator.py").is_file(),
    }
    adapters = adapter_report()
    adapter_status = adapters.get("status", "blocked")
    return {
        "scope": "skill_doctor",
        "status": "ready" if all(assets.values()) and adapter_status == "ready" else "degraded",
        "core_assets": assets,
        "external_engine_adapters": adapters,
        "boundary": "Readiness only. An available adapter is not external raw-oracle verification.",
    }


def _vedastro_status(result: dict[str, Any]) -> str:
    engines = result.get("external_engine_cross_validation")
    if isinstance(engines, dict):
        engines = engines.get("engines")
    vedastro = engines.get("VedAstro") if isinstance(engines, dict) else None
    if isinstance(vedastro, dict):
        return str(vedastro.get("status") or "")
    return ""


def summarize_execution_status(result: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize official/local evidence state for every conversational surface."""
    result = result or {}
    fallback_reason = str(result.get("fallback_reason") or "")
    vedastro = _vedastro_status(result)
    raw_status = str(result.get("official_evidence_status") or "")
    if raw_status == "official_verified" or vedastro == "official_verified":
        official, source = "official_verified", "official_raw"
    elif fallback_reason or vedastro in {"local_fallback", "official_blocked", "blocked"}:
        official, source = "official_blocked", "local_fallback"
    else:
        official, source = "official_not_requested", "local_or_unverified"
    return {
        "scope": "execution_status",
        "official_evidence_status": official,
        "calculation_source": source,
        "fallback_reason": fallback_reason or None,
        "allowed_claims": ["official_verified", "official_blocked", "local_fallback"],
        "claim_boundary": (
            "Only official_verified permits claims that VedAstro official raw evidence was used."
        ),
    }
