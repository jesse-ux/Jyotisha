from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"


def test_skill_text_requires_effective_capability_view_before_claims() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "references/oracle/effective_skill_capability_view_2026_07_19.json" in text
    assert "references/oracle/skill_truth_overlay_2026_07_19.json" in text
    assert "不得直接把 `references/technique_registry.json` 的旧 `covered` 当作完整闭环" in text


def test_skill_text_does_not_overclaim_kp_muhurta_sahams() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "KP/Muhurta/Gochara/Sahams/Sphuta/Tajika等高阶分支必须按 skill truth overlay 降级使用" in text
    assert "KP系统 | reference-only / partial" in text
