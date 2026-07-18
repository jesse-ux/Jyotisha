from scripts import vedastro_contract_probe as probe


def test_equivalent_time_gate_uses_normalized_values_not_raw_hashes() -> None:
    runs = {
        "local_minus_08": [{"normalized": {"Sun": 312.5}, "raw_hash": "a"}, {"normalized": {"Sun": 312.5}, "raw_hash": "b"}],
        "utc_equivalent": [{"normalized": {"Sun": 312.5}, "raw_hash": "c"}],
        "positive_08_control": [{"normalized": {"Sun": 100.0}, "raw_hash": "d"}],
    }
    result = probe.evaluate_time_contract(runs)
    assert result["equivalent_local_utc"] is True
    assert result["positive_offset_control_distinct"] is True
    assert result["repeat_normalized_stable"] is True
    assert result["raw_hash_stable"] is False


def test_method_gate_blocks_ambiguous_all_planet_longitude() -> None:
    result = probe.evaluate_method_contract(
        all_planet={"Sun": 311.84},
        all_planet_data={"Sun": 312.51},
        nirayana={"Sun": 312.51},
        tolerance=0.01,
    )
    assert result["all_planet_data_matches_nirayana"] is True
    assert result["all_planet_longitude_matches_nirayana"] is False
    assert result["status"] == "blocked"


def test_redact_headers_never_persists_credentials() -> None:
    assert probe.redact_headers({"x-api-key": "secret", "Server": "Kestrel"}) == {"server": "Kestrel"}
