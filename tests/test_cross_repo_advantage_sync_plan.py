from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "research" / "cross_repo_advantage_sync_status_2026_07_19.md"
E2E = ROOT / "references" / "cross_project_contract" / "commercial_astrology_e2e_acceptance_questions_2026_07_19.json"
UX = ROOT / "docs" / "research" / "commercial_onboarding_ux_research_contract_2026_07_19.md"


def test_cross_repo_advantage_ledger_tracks_both_directions_and_blockers() -> None:
    text = LEDGER.read_text(encoding="utf-8")

    assert "Research → Commercial" in text
    assert "Commercial → Research" in text
    assert "not credits, billing, payment, or Supabase service-role runtime" in text
    assert "gender interpretation boundary" in text
    assert "day-level holdout" in text
    assert "VedAstro hosted identity" in text
    assert "Shadbala/AV worked example" in text


def test_commercial_e2e_acceptance_has_eight_real_user_questions() -> None:
    data = json.loads(E2E.read_text(encoding="utf-8"))

    assert data["contract_id"] == "commercial_astrology_e2e_acceptance_questions_2026_07_19"
    assert data["status"] == "acceptance_contract_not_runtime_claim"
    assert len(data["questions"]) == 8
    required_layers = {layer for q in data["questions"] for layer in q["required_layers"]}
    for layer in {
        "Vimshottari Dasha",
        "Narayana Dasha",
        "D9",
        "D10",
        "D2",
        "D11",
        "UL",
        "A10",
        "Shadbala",
        "Ashtakavarga",
        "VedAstro gateway boundary",
        "timing precision contract",
        "gender interpretation boundary",
    }:
        assert layer in required_layers


def test_commercial_onboarding_ux_contract_is_research_safe() -> None:
    text = UX.read_text(encoding="utf-8")

    assert "称呼 → 出生时间 → 出生地点 → 时间校正" in text
    assert "资料缺失时引导补全，不把缺失说成系统错误" in text
    assert "不迁移积分、支付、商业账户权益" in text
    assert "research interaction prototype" in text
