#!/usr/bin/env python3
"""Regression tests for user-led Jyotish reading calibration guidance."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AI_WORKFLOW = ROOT / "references" / "ai-reading-workflow-prompt.md"
STRICT_ROUTER = ROOT / "references" / "strict-workflow-router.md"


def test_ai_workflow_contains_user_interrogation_calibration_protocol() -> None:
    text = AI_WORKFLOW.read_text(encoding="utf-8")

    required_phrases = [
        "用户追问校准与相似案例对标协议",
        "盲推隔离模式",
        "具体事件选项协议",
        "证据先行，结论最后",
        "相似案例分层对标",
        "反例与用户排除案例处理",
        "转型与机会的现实机制检查",
        "时间节点输出粒度",
        "User Feedback Isolation: used",
        "Contact",
        "Activation",
        "Confirmation",
        "Manifestation",
        "Responsibility Test",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_strict_router_requires_user_led_calibration_audit_rows() -> None:
    text = STRICT_ROUTER.read_text(encoding="utf-8")

    required_phrases = [
        "User-Led Reading Calibration Gate",
        "User Feedback Isolation",
        "Concrete Time/Event Options",
        "Evidence-First / Conclusion-Last",
        "Similarity-Weighted Case Calibration",
        "Transferability Boundary",
        "Counterexample Handling",
        "L0 same-domain only",
        "L5 material substrate",
        "Analog cases cannot be used as prophecy",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_case_calibration_requires_more_than_same_domain() -> None:
    text = STRICT_ROUTER.read_text(encoding="utf-8")

    assert "Same-topic cases alone cannot raise confidence" in text
    assert "Required for material-outcome claims" in text
    assert "Do not ask vague subjective questions" in text
