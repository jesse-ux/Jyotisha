from scripts.vedastro_contract_arbitrator import arbitrate


def test_arbitrator_blocks_when_method_contract_changes_across_runs() -> None:
    runs = [
        {"contract_status": "blocked", "method_contract": {"status": "blocked"}, "time_contract": {"equivalent_local_utc": True}, "api_version_contract": {"status": "blocked"}, "normalized_vectors": {"x": {"Sun": 1}}},
        {"contract_status": "blocked", "method_contract": {"status": "resolved"}, "time_contract": {"equivalent_local_utc": True}, "api_version_contract": {"status": "blocked"}, "normalized_vectors": {"x": {"Sun": 2}}},
    ]
    report = arbitrate(runs)
    assert report["status"] == "blocked"
    assert report["cross_run_normalized_stable"] is False
    assert report["method_statuses"] == ["blocked", "resolved"]
