#!/usr/bin/env python3
"""Guard the non-negotiable high-rigor skill constraints."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_skill_declares_five_hard_constraints() -> None:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "五层硬约束（全球前三引擎强制调用）" in skill
    assert "PyJHora、VedAstro、jyotishganit" in skill
    assert "Narayana Dasha" in skill
    assert "D10 for career, D2/D11 for wealth, D9 for marriage" in skill
    assert "原始数据交付" in skill


def test_router_declares_rigorous_multi_engine_and_raw_data_policy() -> None:
    router = (ROOT / "references" / "strict-workflow-router.md").read_text(encoding="utf-8")

    assert "High-Rigor Override" in router
    assert "PyJHora / VedAstro / jyotishganit" in router
    assert "Narayana Dasha" in router
    assert "raw outputs" in router
    assert "blocked" in router
    assert "Functional Benefic/Malefic" in router
    assert "functional neutrals" in router.lower()
    assert "yogakarakas" in router


def test_agents_declares_functional_benefic_malefic_hard_constraint() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "Functional Benefic/Malefic Hard Constraint" in agents
    assert "强制调取 Functional Benefic / Malefic 判定" in agents
    assert "Vimshottari + Narayana Dasha" in agents
    assert "Technique Audit Table" in agents
    assert "blocked" in agents


def test_mevg_global_web_and_real_case_evidence_is_agent_hard_constraint() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "Existing MEVG Invocation Hard Constraint" in agents
    assert "所有星盘运势类问题" in agents
    assert "所有有关印度占星推运的问题" in agents
    assert "references/mandatory-verification-gate-protocol.md" in agents
    assert "MEVG" in agents
    assert "全球 / 全网外部资料采集" in agents
    assert "真实案例参考" in agents
    assert "MEVG / Global Web Evidence" in agents
    assert "Real Case Calibration" in agents
    assert "纯计算 / 纯代码 / 纯项目维护" in agents


def test_strict_router_makes_mevg_default_for_all_chart_readings() -> None:
    router = (ROOT / "references" / "strict-workflow-router.md").read_text(encoding="utf-8")

    assert "Existing MEVG Invocation Gate" in router
    assert "all chart interpretation readings" in router
    assert "annual/monthly timing" in router
    assert "event prediction" in router
    assert "rectification support" in router
    assert "MEVG / Global Web Evidence" in router
    assert "Real Case Calibration" in router
    assert "pure calculation / code / project-maintenance tasks are exempt" in router
    assert "MEVG external verification for all interpretive chart-reading claims" in router


def test_domain_event_adjudicators_require_mevg_and_real_case_contract() -> None:
    for filename in [
        "event_judgment_marriage.md",
        "event_judgment_career.md",
        "event_judgment_wealth.md",
    ]:
        text = (ROOT / "references" / filename).read_text(encoding="utf-8")

        assert "MEVG / Global Web Evidence" in text
        assert "Real Case Calibration" in text
        assert "source tier" in text
        assert "conflict arbitration" in text
        assert "pure calculation exemption" in text


def test_general_timing_workflow_requires_mevg_and_real_case_contract() -> None:
    skeleton = (ROOT / "references" / "event_judgment_skeleton.md").read_text(encoding="utf-8")
    assert "marriage / career / wealth / health / generic event verification" in skeleton
    assert "MEVG / Global Web Evidence" in skeleton
    assert "Real Case Calibration" in skeleton
    assert "source tier" in skeleton
    assert "conflict arbitration" in skeleton
    assert "pure calculation exemption" in skeleton

    workflow = (ROOT / "references" / "ai-reading-workflow-prompt.md").read_text(encoding="utf-8")
    assert "references/mandatory-verification-gate-protocol.md" in workflow
    assert "Step 3.11" in workflow
    assert "Step 4.10" in workflow
    assert "Step 5.5" in workflow
    assert "案例检索与对比" in workflow

    transit = (ROOT / "references" / "transit-actionable-output-guide.md").read_text(encoding="utf-8")
    assert "案例检索三步法" in transit
    assert "任何涉及具体事件类型的 Transit 预测" in transit
    assert "MEVG / Global Web Evidence" in transit
    assert "Real Case Calibration" in transit
