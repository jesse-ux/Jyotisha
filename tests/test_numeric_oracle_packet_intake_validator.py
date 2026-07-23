from scripts.numeric_oracle_packet_intake_validator import build_template, validate_document


def test_blank_numeric_oracle_template_stays_candidate() -> None:
    validation = validate_document(build_template())
    assert validation["claim_status"] == "candidate_queue"
    assert validation["summary"]["ready_packet_count"] == 0
    assert validation["rows"][0]["validation_status"] == "blocked_missing_numeric_or_replay_fields"
    assert {packet["domain"] for packet in build_template()["packets"]} >= {"kp_12_cusp", "advanced_ashtakavarga"}


def test_complete_kp_packet_can_be_ready_for_replay_packet() -> None:
    packet = build_template()["packets"][0]
    packet.update({
        "packet_id": "kp_complete",
        "birth_or_question_input": {"date": "2000-01-01"},
        "timezone": "+05:30",
        "ayanamsa": "KP",
        "house_system": "Placidus",
        "twelve_exact_cusp_longitudes": list(range(12)),
        "twelve_star_lords": ["Sun"] * 12,
        "twelve_sub_lords": ["Moon"] * 12,
        "twelve_sub_sub_lords": ["Mars"] * 12,
        "source_provenance": {"url": "https://example.test", "page_or_artifact_hash": "abc"},
        "local_replay": {"status": "within_tolerance", "delta_summary": "ok"},
    })
    validation = validate_document({"packets": [packet]})
    assert validation["summary"]["ready_packet_count"] == 1
    assert validation["rows"][0]["validation_status"] == "ready_for_replay_packet"


def test_advanced_ashtakavarga_requires_public_numeric_replay_contract() -> None:
    packet = {
        "packet_id": "advanced_av_complete",
        "domain": "advanced_ashtakavarga",
        "complete_chart_input": {"date": "2000-01-01"},
        "location_timezone": {"place": "Chennai", "timezone": "+05:30"},
        "ayanamsa_node_mode": "Lahiri/true",
        "technique_variant": "kakshya_transit",
        "expected_numeric_values": {"kakshya": 3},
        "source_provenance": {"url": "https://example.test", "page_or_artifact_hash": "abc"},
        "local_replay": {"status": "within_tolerance", "delta_summary": "ok"},
    }
    validation = validate_document({"packets": [packet]})
    assert validation["rows"][0]["validation_status"] == "ready_for_replay_packet"
