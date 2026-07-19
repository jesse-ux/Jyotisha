from scripts.rectification_technique_contract import build_rectification_technique_contract


def test_zero_events_are_not_a_completed_rectification() -> None:
    contract = build_rectification_technique_contract(event_count=0, domain_count=0)
    assert contract["calculation_status"] == "not_started"
    assert contract["can_narrow_to_minute"] is False
    assert "insufficient_events" in contract["hard_blockers"]


def test_contract_discloses_used_and_missing_layers() -> None:
    contract = build_rectification_technique_contract(event_count=4, domain_count=3)
    assert {"D4", "D9", "D10", "D24", "D30"} <= set(contract["used_divisional_charts"])
    assert contract["dasha_tracks"] == ["vimshottari_md_ad", "narayana_md_ad"]
    assert {"D2", "D11", "functional_benefic_malefic", "ashtakavarga", "shadbala"} <= set(contract["missing_layers"])
    assert contract["external_engines"]["status"] == "not_run"
