from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "references/relationship_gender_role_technique_registry_2026_07_19.json"


def test_relationship_gender_role_registry_keeps_gender_out_of_base_chart() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert data["scope"] == "relationship_gender_role_technique_registry"
    assert data["default_profile_policy"] == "neutral_partner_a_b"
    assert data["base_chart_requires_gender"] is False
    assert data["production_tuning_allowed"] is False
    assert data["truth_policy"] == "technique_registry_not_prediction_truth"


def test_relationship_gender_role_registry_covers_core_indian_and_western_methods() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    ids = {row["id"] for row in data["techniques"]}
    for required in {
        "vedic_venus_jupiter_spouse_significators",
        "vedic_kuja_manglik_role_weighting",
        "ashtakoot_yoni_energy_not_user_gender",
        "ashtakoot_nadi_rajju_reproductive_safety",
        "jaimini_darakaraka_upapada_spouse_role",
        "d9_navamsa_gendered_interpretation_layer",
        "adhana_conception_gender_sensitive_scaffold",
        "western_venus_mars_sun_moon_partner_projection",
        "western_synastry_composite_role_neutral_mode",
        "western_progressed_angles_relationship_timing",
    }:
        assert required in ids


def test_relationship_gender_role_registry_marks_license_and_integration_boundaries() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    for row in data["techniques"]:
        assert row["integration_action"] in {
            "use_existing_local",
            "add_interpretation_layer",
            "oracle_only",
            "blocked_until_source_verified",
        }
        assert row["gender_dependency"] in {
            "none",
            "interpretation_only",
            "role_weighting",
            "traditional_rule_variant",
        }
        assert row["license_boundary"]
        assert row["claim_boundary"]

