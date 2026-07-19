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
