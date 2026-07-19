from __future__ import annotations

import json
from pathlib import Path

from scripts.capability_evidence_pool import build_capability_evidence_pool_summary


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "references" / "technique_registry.json"
README = ROOT / "README.md"


def test_registry_is_backend_evidence_pool_not_flat_user_skill_list() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    techniques = registry["techniques"]

    assert registry["registry_role"] == "backend_capability_evidence_pool"
    assert registry["public_label"] == "89 capability entries"
    assert "question-domain router" in registry["ordinary_user_policy"]

    allowed_entry_types = {
        "core_technique",
        "supporting_indicator",
        "composite_adjudicator",
        "workflow_or_engineering",
        "alias_entry",
    }
    allowed_roles = {"primary", "secondary", "context", "audit_only", "alias"}
    allowed_visibility = {"ordinary_topic_router", "expert_audit", "hidden"}
    allowed_prediction = {
        "case_validated_partial",
        "support_only",
        "not_claimed",
        "not_applicable",
    }

    for tech_id, tech in techniques.items():
        assert tech["entry_type"] in allowed_entry_types, tech_id
        assert tech["evidence_role"] in allowed_roles, tech_id
        assert tech["user_visibility"] in allowed_visibility, tech_id
        assert tech["verification_level"]["calculation"] in {"verified", "partial", "not_applicable"}, tech_id
        assert tech["verification_level"]["rule"] in {"verified", "partial", "not_applicable"}, tech_id
        assert tech["verification_level"]["prediction"] in allowed_prediction, tech_id
        assert tech["conclusion_policy"], tech_id

    assert techniques["case_validator"]["evidence_role"] == "audit_only"
    assert techniques["thematic_report_orchestrator"]["entry_type"] == "workflow_or_engineering"
    assert techniques["neechabhanga"]["evidence_role"] == "alias"
    assert techniques["special_lagnas"]["evidence_role"] == "alias"


def test_evidence_pool_summary_routes_few_primary_items_and_many_support_items() -> None:
    summary = build_capability_evidence_pool_summary()

    assert summary["scope"] == "backend_capability_evidence_pool"
    assert summary["total_entries"] == 91
    assert summary["ordinary_user_policy"].startswith("Users see topic-level")
    assert summary["evidence_role_counts"]["primary"] >= 8
    assert summary["evidence_role_counts"]["secondary"] > summary["evidence_role_counts"]["primary"]
    assert summary["evidence_role_counts"]["audit_only"] >= 3
    assert summary["prediction_verification_counts"]["not_claimed"] > 0
    assert summary["conclusion_policy"]["primary_chain_required"] is True
    assert summary["conclusion_policy"]["all_89_entries_must_not_be_flattened_into_conclusions"] is True


def test_readme_uses_capability_entries_language_instead_of_89_techniques_claim() -> None:
    readme = README.read_text(encoding="utf-8")

    assert "89 capability entries" in readme
    assert "89 techniques" not in readme
    assert "backend evidence pool" in readme
