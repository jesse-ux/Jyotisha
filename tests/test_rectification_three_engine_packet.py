from scripts.rectification_three_engine_packet import build_packet, case_hash


CASE = {"year": 1990, "month": 1, "day": 1, "hour": 12, "minute": 0, "lat": 0.0, "lon": 0.0, "tz": 0.0}


def test_packet_is_private_and_never_confirms(monkeypatch) -> None:
    monkeypatch.setattr("scripts.rectification_three_engine_packet._local_d1", lambda _: {"Sun": "Aries"})
    monkeypatch.setattr("scripts.rectification_three_engine_packet._pyjhora_d1", lambda _: {"Sun": "Aries"})
    monkeypatch.setattr("scripts.rectification_three_engine_packet._jyotishganit_d1", lambda _: {"Sun": "Aries"})
    packet = build_packet(CASE)
    assert packet["case_hash"] == case_hash(CASE)
    assert "year" not in str(packet)
    assert packet["can_confirm"] is False
    assert packet["vedastro"]["status"] == "requires_gateway_raw_archive"


def test_case_hash_uses_only_normalized_calculation_input() -> None:
    equivalent = {
        **CASE,
        "second": 0.0,
        "ayanamsa": " LAHIRI ",
        "nodeMode": "MEAN",
        "display_name": "must not affect calculation identity",
    }

    assert case_hash(equivalent) == case_hash({**CASE, "ayanamsa": "lahiri", "node_mode": "mean"})


def test_high_rigor_packet_queues_safe_vedastro_receipt_without_raw(monkeypatch) -> None:
    monkeypatch.setattr("scripts.rectification_three_engine_packet._local_d1", lambda _: {"Sun": "Aries"})
    monkeypatch.setattr("scripts.rectification_three_engine_packet._pyjhora_d1", lambda _: {"Sun": "Aries"})
    monkeypatch.setattr("scripts.rectification_three_engine_packet._jyotishganit_d1", lambda _: {"Sun": "Aries"})
    monkeypatch.setattr(
        "scripts.vedastro_gateway.enqueue_gateway_job",
        lambda *_args, **_kwargs: {
            "job_id": "vgw_safe_receipt",
            "status": "queued",
            "poll_path": "/api/vedastro_gateway/jobs/vgw_safe_receipt",
            "request": CASE,
            "result": {"official_raw_response": {"private": "never expose"}},
            "raw_response_archive": {
                "status": "pending",
                "official_raw_response_available": False,
            },
        },
    )

    packet = build_packet(CASE, enqueue_vedastro_gateway=True)

    assert packet["vedastro"] == {
        "scope": "vedastro_gateway_job_receipt",
        "status": "queued",
        "job_id": "vgw_safe_receipt",
        "poll_path": "/api/vedastro_gateway/jobs/vgw_safe_receipt",
        "raw_response_archive": {
            "status": "pending",
            "official_raw_response_available": False,
        },
        "boundary": "VedAstro raw response remains server-side; this receipt never returns request data or raw evidence.",
    }
    assert "year" not in str(packet)
    assert "private" not in str(packet)
