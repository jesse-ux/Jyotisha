from scripts.minute_rectification_fact_ranker_v4 import (
    ALGORITHM_VERSION,
    LAYER_FAMILIES,
    rank_fact_rows,
    score_fact_ranker_v4,
)


def _fact(event_id: str, domain: str, *, varga_house: int, av: int) -> dict:
    return {
        "event_id": event_id,
        "domain": domain,
        "vimshottari": {"md": "Sun", "ad": "Moon", "pd": "Mars"},
        "narayana": {"md_sign": 0, "ad_sign": 1},
        "d1": {
            "ascendant_sign": 0,
            "target_house_lords": ["Moon"],
            "active_lord_houses": {"md": 1, "ad": 7, "pd": 3},
        },
        "vargas": [{
            "chart": "D9" if domain == "relationship" else "D10",
            "ascendant_sign": 0,
            "active_lord_houses": {"md": varga_house, "ad": 3, "pd": 4},
        }],
        "arudha_signs": {"A7": 0} if domain == "relationship" else {"A10": 0},
        "ashtakavarga_target_house_scores": {"7": av},
        "verified_shadbala_state": ["shadbala_sthana_drik_naisargika_support_auxiliary"],
    }


def _rows() -> list[dict]:
    return [
        {
            "time": candidate,
            "feature_contract_version": "minute-rectification-feature-facts-v4-shadow",
            "event_facts": [
                _fact("event-career", "career", varga_house=varga_house, av=av),
                _fact("event-relationship", "relationship", varga_house=varga_house, av=av),
            ],
            "missing_layers": [],
        }
        for candidate, varga_house, av in (
            ("10:00", 3, 20),
            ("10:01", 10, 32),
            ("10:02", 3, 20),
        )
    ]


def _events() -> list[dict]:
    return [
        {"id": "event-career", "domain": "career", "date": "2020", "precision": "year"},
        {"id": "event-relationship", "domain": "relationship", "date": "2021-03", "precision": "month"},
    ]


def test_fact_ranker_uses_candidate_differences_and_balances_domains() -> None:
    rows, contract = rank_fact_rows(_rows(), _events())

    assert max(rows, key=lambda row: row["score"])["time"] == "10:01"
    assert contract["algorithm_version"] == ALGORITHM_VERSION
    assert contract["shadow_only"] is True
    assert set(contract["layer_weights"]) == set(LAYER_FAMILIES)
    assert set(contract["candidate_domain_scores"]["10:01"]) == {"career", "relationship"}


def test_fact_ranker_ablation_and_safety_gates_never_apply_a_minute() -> None:
    result = score_fact_ranker_v4(_rows(), _events())

    assert result["can_apply"] is False
    assert result["shadow_only"] is True
    assert "fact_ranker_v4_holdout_not_ready" in result["reasons"]
    assert {
        run["removed_layer"] for run in result["stability_diagnostics"]["ablation"]["runs"]
    } == set(LAYER_FAMILIES)
    assert result["stability_diagnostics"]["neighbor_stability"]["all_required_passed"] is False
    assert result["stability_diagnostics"]["leave_one_event_out"]["status"] == "pass"


def test_constant_fact_layers_contribute_zero_candidate_preference() -> None:
    rows = _rows()
    for row in rows:
        for fact in row["event_facts"]:
            fact["vargas"][0]["active_lord_houses"]["md"] = 3
            fact["ashtakavarga_target_house_scores"]["7"] = 28

    ranked, contract = rank_fact_rows(rows, _events())

    assert len({row["score"] for row in ranked}) == 1
    assert all(score == 0 for score in contract["event_raw_scores"]["event-career"].values())
