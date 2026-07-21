from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


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
