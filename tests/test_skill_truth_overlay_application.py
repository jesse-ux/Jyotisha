from __future__ import annotations

from pathlib import Path

from scripts.skill_truth_overlay_view import build_effective_registry

ROOT = Path(__file__).resolve().parents[1]


def test_skill_truth_overlay_view_applies_corrected_statuses() -> None:
    view = build_effective_registry(
        ROOT / "references/technique_registry.json",
        ROOT / "references/oracle/skill_truth_overlay_2026_07_19.json",
    )
    effective = {row["technique_id"]: row["effective_status"] for row in view["techniques"]}
    assert effective["kp_system"] == "reference_only"
    assert effective["muhurta"] == "reference_only"
    assert effective["sahams"] == "blocked"
    assert effective["sphuta_trisphuta_family"] == "blocked"
    assert effective["tajika_yogas"] == "partial"


def test_skill_truth_overlay_view_preserves_registry_status_as_raw_field() -> None:
    view = build_effective_registry(
        ROOT / "references/technique_registry.json",
        ROOT / "references/oracle/skill_truth_overlay_2026_07_19.json",
    )
    kp = next(row for row in view["techniques"] if row["technique_id"] == "kp_system")
    assert kp["registry_status"] == "covered"
    assert kp["effective_status"] == "reference_only"
    assert kp["overlay_evidence"] == "references/oracle/technique_promotion_audit_kp_gochara_muhurta_2026_07_19.json"
    assert view["truth_source_order"][0].endswith("references/oracle/skill_truth_overlay_2026_07_19.json")
    assert view["truth_source_order"][1].endswith("references/technique_registry.json")


def test_commercial_agent_must_not_promote_reference_only_or_blocked_techniques() -> None:
    source = (ROOT / "frontend" / "src" / "mastra" / "index.ts").read_text(encoding="utf-8")

    assert "effective_skill_capability_view" in source
    assert "effective_status, not registry_status" in source
    assert "reference_only or blocked techniques" in source
