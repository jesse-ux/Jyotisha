from scripts.rectification_technique_contract import build_rectification_technique_contract


def test_zero_events_are_not_a_completed_rectification() -> None:
    contract = build_rectification_technique_contract(event_count=0, domain_count=0)
    assert contract["calculation_status"] == "not_started"
    assert contract["can_narrow_to_minute"] is False
    assert "insufficient_events" in contract["hard_blockers"]


def test_contract_discloses_used_and_missing_layers() -> None:
    contract = build_rectification_technique_contract(event_count=4, domain_count=3)
    assert {"D4", "D9", "D10", "D24", "D30"} <= set(contract["used_divisional_charts"])
    assert contract["dasha_tracks"] == ["vimshottari_md_ad_pd", "narayana_md_ad"]
    assert contract["used_arudha"] == ["A7", "UL", "A10"]
    assert contract["missing_layers"] == ["shadbala_kala_dig_chesta_total"]
    assert "D2" in contract["partial_layers"]
    assert "D11" in contract["partial_layers"]
    assert "functional_benefic_malefic" in contract["auxiliary_layers"]
    assert "controlled_transit" in contract["auxiliary_layers"]
    assert "ashtakavarga" in contract["auxiliary_layers"]
    assert "shadbala_verified_components" in contract["auxiliary_layers"]
    assert "shadbala_sthana_drik_naisargika" in contract["partial_layers"]
    assert contract["external_engines"]["status"] == "not_run"


def test_high_rigor_requires_real_three_engine_evidence() -> None:
    contract = build_rectification_technique_contract(event_count=4, domain_count=3, high_rigor=True)
    assert contract["external_engines"]["status"] == "required_not_run"
    assert "three_engine_parity_not_passed" in contract["hard_blockers"]
    assert contract["can_narrow_to_minute"] is False
