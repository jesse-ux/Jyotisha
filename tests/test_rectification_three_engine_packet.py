from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from rectification_three_engine_packet import build_packet, case_hash

CASE = {"year": 1990, "month": 1, "day": 1, "hour": 12, "minute": 0, "lat": 0.0, "lon": 0.0, "tz": 0.0}

def test_packet_is_private_and_never_confirms(monkeypatch) -> None:
    import rectification_three_engine_packet as module
    monkeypatch.setattr(module, "_local_d1", lambda _: {"Sun": "Aries"})
    monkeypatch.setattr(module, "_pyjhora_d1", lambda _: {"Sun": "Aries"})
    monkeypatch.setattr(module, "_jyotishganit_d1", lambda _: {"Sun": "Aries"})
    packet = build_packet(CASE)
    assert packet["case_hash"] == case_hash(CASE)
    assert packet["input_contract_hash"]
    assert packet["stability_contract"]["minute_confirmation_allowed"] is False
    assert "year" not in str(packet)
    assert packet["can_confirm"] is False
    assert packet["vedastro"]["status"] == "requires_gateway_raw_archive"

def test_packet_queues_a_privacy_safe_vedastro_receipt(monkeypatch) -> None:
    import rectification_three_engine_packet as packet

    monkeypatch.setattr(packet, "_local_d1", lambda _case: {"Sun": "Aries"})
    monkeypatch.setattr(packet, "_pyjhora_d1", lambda _case: {"Sun": "Aries"})
    monkeypatch.setattr(packet, "_jyotishganit_d1", lambda _case: {"Sun": "Aries"})
    monkeypatch.setattr(
        packet,
        "_enqueue_vedastro_gateway_job",
        lambda *_args, **_kwargs: {
            "scope": "vedastro_gateway_job_receipt",
            "status": "queued",
            "job_id": "rectification-job",
            "poll_path": "/api/vedastro_gateway/jobs/rectification-job",
            "raw_response_archive": {
                "status": "pending",
                "official_raw_response_available": False,
            },
            "boundary": "VedAstro raw response remains server-side; this receipt never returns request data or raw evidence.",
        },
    )

    result = packet.build_packet(
        {
            "year": 1993,
            "month": 4,
            "day": 17,
            "hour": 14,
            "minute": 29,
            "lat": 36.683333,
            "lon": 114.35,
            "tz": 8,
        },
        enqueue_vedastro_gateway=True,
    )

    assert result["vedastro"]["status"] == "queued"
    assert result["can_confirm"] is False
    assert "1993" not in str(result["vedastro"])
