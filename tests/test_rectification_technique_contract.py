from scripts.rectification_technique_contract import build_rectification_technique_contract


def test_zero_events_are_not_a_completed_rectification() -> None:
    contract = build_rectification_technique_contract(event_count=0, domain_count=0)
    assert contract["calculation_status"] == "not_started"
    assert contract["can_narrow_to_minute"] is False
    assert "insufficient_events" in contract["hard_blockers"]


def test_contract_discloses_used_and_missing_layers() -> None:
    contract = build_rectification_technique_contract(event_count=4, domain_count=3)
    assert {"D2", "D4", "D9", "D10", "D11", "D24", "D30"} <= set(contract["used_divisional_charts"])
    assert contract["dasha_tracks"] == ["vimshottari_md_ad_pd", "narayana_md_ad"]
    assert contract["used_arudha"] == ["A7", "UL", "A10"]
    assert contract["missing_layers"] == ["shadbala_kala_dig_chesta_total"]
    assert "D2" not in contract["partial_layers"]
    assert "D11" not in contract["partial_layers"]
    assert "functional_benefic_malefic" in contract["auxiliary_layers"]
    assert "controlled_transit" in contract["auxiliary_layers"]
    assert "ashtakavarga" in contract["auxiliary_layers"]
    assert "shadbala_verified_components" in contract["auxiliary_layers"]
    assert "shadbala_sthana_drik_naisargika" in contract["partial_layers"]
    assert contract["external_engines"]["status"] == "not_evaluated"


def test_high_rigor_requires_real_three_engine_evidence() -> None:
    contract = build_rectification_technique_contract(event_count=4, domain_count=3, high_rigor=True)
    assert contract["external_engines"]["status"] == "not_evaluated"
    assert "vedastro_validation_not_passed" in contract["hard_blockers"]
    assert contract["can_narrow_to_minute"] is False


def test_vedastro_minute_sensitive_validation_is_required_after_local_gates_pass() -> None:
    contract = build_rectification_technique_contract(
        event_count=4,
        domain_count=3,
        local_candidate_ready=True,
        required_layers_complete=True,
        canonical_input_hash="canonical-fixture",
        stability_diagnostics={
            "neighbor_stability": {"all_required_passed": True},
            "leave_one_event_out": {"status": "pass"},
        },
    )

    assert contract["canonical_input_hash"] == "canonical-fixture"
    assert contract["gates"]["neighbor_stability"]["status"] == "pass"
    assert contract["gates"]["leave_one_event_out"]["status"] == "pass"
    assert contract["gates"]["vedastro_minute_sensitive_validation"]["status"] == "not_evaluated"
    assert contract["confirmation_allowed"] is False
    assert contract["decision"] == "continue_rectification"


def test_semantic_vedastro_validation_allows_minute_confirmation() -> None:
    contract = build_rectification_technique_contract(
        event_count=5,
        domain_count=3,
        high_rigor=True,
        local_candidate_ready=True,
        required_layers_complete=True,
        stability_diagnostics={
            "neighbor_stability": {"all_required_passed": True},
            "leave_one_event_out": {"status": "pass"},
        },
        external_validation={
            "status": "pass",
            "vedastro_status": "official_verified",
            "mismatch_count": 0,
            "engine_status": {"local": "ok", "pyjhora": "ok", "jyotishganit": "ok"},
            "minute_sensitive_validation": {"status": "pass"},
        },
    )

    assert contract["gates"]["vedastro_official_response"]["status"] == "pass"
    assert contract["gates"]["vedastro_minute_sensitive_validation"]["status"] == "pass"
    assert contract["confirmation_allowed"] is True
    assert contract["decision"] == "confirm_minute"


def test_neighbor_and_leave_one_out_failures_remain_diagnostic_after_external_validation() -> None:
    contract = build_rectification_technique_contract(
        event_count=12,
        domain_count=5,
        high_rigor=True,
        local_candidate_ready=True,
        required_layers_complete=True,
        stability_diagnostics={
            "neighbor_stability": {"all_required_passed": False},
            "leave_one_event_out": {"status": "fail"},
        },
        external_validation={
            "status": "pass",
            "vedastro_status": "official_verified",
            "mismatch_count": 0,
            "engine_status": {"local": "ok", "pyjhora": "ok", "jyotishganit": "ok"},
            "minute_sensitive_validation": {"status": "pass"},
        },
    )

    assert contract["gates"]["neighbor_stability"]["status"] == "diagnostic_fail"
    assert contract["gates"]["leave_one_event_out"]["status"] == "diagnostic_fail"
    assert "neighbor_stability_not_passed" not in contract["hard_blockers"]
    assert "leave_one_event_out_not_passed" not in contract["hard_blockers"]
    assert contract["confirmation_allowed"] is True


def test_contract_reports_the_actual_missing_dasha_layer() -> None:
    contract = build_rectification_technique_contract(
        event_count=3,
        domain_count=2,
        required_layers_complete=False,
        missing_required_layers=["Narayana_MD_AD"],
    )

    assert "Narayana_MD_AD" in contract["missing_layers"]
    assert contract["gates"]["required_layers"]["status"] == "fail"
    assert "required_layers_incomplete" in contract["hard_blockers"]
