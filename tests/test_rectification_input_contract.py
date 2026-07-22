from scripts.rectification_input_contract import (
    candidate_input_fingerprint,
    canonical_birth_input,
    semantic_evidence_hash,
    stability_probe_contract,
)

CASE = {
    "year": 1990,
    "month": 1,
    "day": 1,
    "hour": 12,
    "minute": 0,
    "lat": 0.0,
    "lon": 0.0,
    "tz": 0.0,
}


def test_contract_uses_deployed_mean_node_default_and_stable_identity() -> None:
    reordered = {key: CASE[key] for key in reversed(CASE)}

    assert canonical_birth_input(CASE)["node_mode"] == "mean"
    assert candidate_input_fingerprint(CASE) == candidate_input_fingerprint(reordered)
    assert candidate_input_fingerprint(CASE) == candidate_input_fingerprint({**CASE, "nodeMode": "MEAN"})


def test_candidate_fingerprint_changes_with_calculation_input() -> None:
    assert candidate_input_fingerprint(CASE) != candidate_input_fingerprint({**CASE, "minute": 1})
    assert candidate_input_fingerprint(CASE) != candidate_input_fingerprint({**CASE, "node_mode": "true"})


def test_stability_contract_records_adjacent_probes_without_confirming() -> None:
    contract = stability_probe_contract(CASE)

    assert [probe["offset_minutes"] for probe in contract["probes"]] == [-5, -2, -1, 1, 2, 5]
    assert contract["minute_confirmation_allowed"] is False
    assert contract["status"] == "pending_score_comparison"


def test_semantic_hash_normalizes_only_known_order_insensitive_lists() -> None:
    left = {"aspects": {"gives": ["Mars", "Saturn"]}, "ordered_scores": [2, 1]}
    reordered_aspects = {"ordered_scores": [2, 1], "aspects": {"gives": ["Saturn", "Mars"]}}
    reordered_scores = {"ordered_scores": [1, 2], "aspects": {"gives": ["Saturn", "Mars"]}}

    assert semantic_evidence_hash(left) == semantic_evidence_hash(reordered_aspects)
    assert semantic_evidence_hash(left) != semantic_evidence_hash(reordered_scores)
