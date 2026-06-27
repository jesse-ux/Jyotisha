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


def test_agents_declares_functional_benefic_malefic_hard_constraint() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "Functional Benefic/Malefic Hard Constraint" in agents
    assert "强制调取 Functional Benefic / Malefic 判定" in agents
    assert "Vimshottari + Narayana Dasha" in agents
    assert "Technique Audit Table" in agents
    assert "blocked" in agents
