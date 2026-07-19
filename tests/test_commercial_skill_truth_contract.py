"""Commercial-only claim boundaries for techniques not cleared for deterministic use."""

from __future__ import annotations

from scripts.commercial_skill_truth import (
    TECHNIQUE_TRUTH_IDS,
    apply_commercial_skill_truth,
    load_commercial_skill_truth,
)


def test_truth_overlay_has_all_restricted_techniques_and_no_research_paths() -> None:
    overlay = load_commercial_skill_truth()
    techniques = {item["technique_id"]: item for item in overlay["techniques"]}

    assert set(TECHNIQUE_TRUTH_IDS) == set(techniques)
    assert {item["status"] for item in techniques.values()} == {
        "reference_only",
        "partial",
        "blocked",
        "research_only_blocked",
        "partial_registry_only",
    }
    assert "/Users/" not in str(overlay)
    assert "research truth overlay" not in str(overlay).lower()


def test_truth_overlay_cannot_bypass_server_answer_contract() -> None:
    result = apply_commercial_skill_truth(
        {
            "route": "career",
            "answer_policy": {
                "can_answer_direction": True,
                "can_answer_precise_timing": True,
            },
        }
    )

    truth = result["technique_truth"]
    policy = result["answer_policy"]
    assert truth["status"] == "restricted"
    assert set(truth["blocked_techniques"]) == {
        "sahams",
        "sphuta_trisphuta_family",
        "conception_chart",
    }
    assert set(policy["deterministic_claims_forbidden_for"]) == set(TECHNIQUE_TRUTH_IDS)
    assert policy["can_answer_precise_timing"] is True
    evidence = result["commercial_evidence_status"]
    assert evidence["claim_audit"]["status"] == "contract_enforced"
    assert evidence["three_engine_mismatch"]["truth_policy"] == "no_majority_vote"
