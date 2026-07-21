from scripts.rectification_input_contract import (
    candidate_input_fingerprint,
    canonical_birth_input,
    semantic_evidence_hash,
    stability_probe_contract,
)


CASE = {
    "year": 1955,
    "month": 2,
    "day": 24,
    "hour": 19,
    "minute": 15,
    "lat": 37.7749,
    "lon": -122.4194,
    "tz": -8,
}


def test_canonical_birth_input_is_order_independent_and_explicit_about_settings():
    reordered = {key: CASE[key] for key in reversed(CASE)}

    first = canonical_birth_input(CASE)
    second = canonical_birth_input(reordered)

    assert first == second
    assert first["ayanamsa"] == "lahiri"
    assert first["node_mode"] == "true"
    assert candidate_input_fingerprint(CASE) == candidate_input_fingerprint(reordered)


def test_candidate_fingerprint_changes_when_only_the_minute_changes():
    next_minute = {**CASE, "minute": 16}

    assert candidate_input_fingerprint(CASE) != candidate_input_fingerprint(next_minute)


def test_stability_probes_are_explicit_but_do_not_claim_minute_confirmation():
    contract = stability_probe_contract(CASE)

    assert contract["status"] == "pending_score_comparison"
    assert [probe["offset_minutes"] for probe in contract["probes"]] == [-5, -2, -1, 1, 2, 5]
    assert contract["minute_confirmation_allowed"] is False
    assert contract["blocker"] == "public_blind_minute_holdout_not_closed"
    assert all("input_fingerprint" in probe for probe in contract["probes"])


def test_semantic_evidence_hash_ignores_known_order_insensitive_aspect_lists_only():
    left = {"aspects": {"gives": ["Mars", "Saturn"], "receives": ["Moon", "Sun"]}, "value": [2, 1]}
    right = {"value": [2, 1], "aspects": {"receives": ["Sun", "Moon"], "gives": ["Saturn", "Mars"]}}
    changed = {"value": [1, 2], "aspects": {"receives": ["Sun", "Moon"], "gives": ["Saturn", "Mars"]}}

    assert semantic_evidence_hash(left) == semantic_evidence_hash(right)
    assert semantic_evidence_hash(left) != semantic_evidence_hash(changed)
