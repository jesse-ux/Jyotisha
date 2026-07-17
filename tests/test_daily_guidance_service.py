from __future__ import annotations

from scripts.daily_guidance_service import build_daily_guidance


def test_daily_guidance_returns_short_positive_evidence_packet() -> None:
    packet = build_daily_guidance({
        "year": 1990,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "lat": 39.9,
        "lon": 116.4,
        "tz": 8,
        "date": "2026-07-17",
        "ayanamsa": "lahiri",
        "node_mode": "mean",
    })

    assert packet["success"] is True
    assert packet["endpoint"] == "daily_guidance"
    assert packet["word_count"] <= 100
    assert packet["daily_star_words"].startswith("今日星语：")
    assert packet["audit"]["not_a_prediction"] is True
    assert {"D1", "Daily Transit"} <= {row["layer"] for row in packet["evidence"]}
    assert packet["suggested_actions"]


def test_daily_guidance_endpoint_is_registered() -> None:
    source = __import__("pathlib").Path("scripts/jyotish_api_server.py").read_text(encoding="utf-8")
    assert "/api/daily_guidance" in source
    assert "daily_guidance_service" in source
