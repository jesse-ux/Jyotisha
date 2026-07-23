from scripts.vedastro_keyed_capture_closure_2026_07_23 import build_packet


def test_keyed_capture_packet_preserves_secret_boundary() -> None:
    packet = build_packet()
    assert packet["claim_status"] == "keyed_observation_partial"
    assert packet["truth_matrix_allowed"] is False
    assert packet["production_tuning_allowed"] is False
    assert packet["api_key_policy"]["persisted_in_artifact"] is False


def test_keyed_capture_records_progress_and_remaining_blocks() -> None:
    packet = build_packet()
    findings = {row["gap"]: row for row in packet["closure_findings"]}

    assert findings["longitude_method_semantics"]["status"] == "observation_resolved_for_probe_case"
    assert findings["hosted_identity"]["status"] == "blocked"
    assert findings["kp_exact_12_cusp"]["status"] == "blocked"
    assert findings["prashna_saham_sphuta"]["status"] == "blocked"

    assert packet["method_catalog_hits"]["Gulika"] == ["GulikaLongitude"]
    assert "TajikaDateForYear" in packet["method_catalog_hits"]["Tajika"]
    assert packet["method_catalog_hits"]["KP"] == ["IsPlanetInHouseKP"]
    assert packet["method_catalog_hits"]["Prashna"] == []
    assert packet["method_catalog_hits"]["Saham"] == []
    assert packet["method_catalog_hits"]["Sphuta"] == []


def test_selected_methods_are_not_misreported_as_ready() -> None:
    packet = build_packet()
    statuses = packet["source_artifacts"]["selected_methods"]["statuses"]
    assert statuses
    assert {row["status"] for row in statuses.values()} == {"unsupported_signature"}
    assert "unsupported_signature" in packet["claim_boundary"] or "payload" in packet["claim_boundary"]
