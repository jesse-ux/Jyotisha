#!/usr/bin/env python3
"""Guardrails for the birth-time rectification decision tree document."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "references" / "birth-time-rectification-decision-tree.md"


def test_rectification_decision_tree_doc_exists_and_covers_priority_layers() -> None:
    assert DOC.exists()
    text = DOC.read_text(encoding="utf-8")
    assert "Dasha + dated events" in text
    assert "D9" in text
    assert "D10" in text
    assert "D12" in text
    assert "D30" in text
    assert "D60" in text
    assert "不是所有分盘一股脑上" in text
    assert "Dasha 定框，D9/D10 定核心" in text


def test_rectification_decision_tree_doc_maps_event_groups_to_vargas() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "婚姻/关系" in text
    assert "事业/升职/换工作" in text
    assert "子女/生育" in text
    assert "父母/家族" in text
    assert "教育/考试" in text
    assert "房产/搬迁" in text
    assert "健康/事故/创伤" in text
