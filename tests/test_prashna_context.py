from datetime import datetime

import pytest

from scripts.prashna_context import PrashnaContextError, build_prashna_context


def test_prashna_context_uses_backend_chart_from_question_moment():
    packet = build_prashna_context({
        "question_text": "Will this proceed?",
        "question_timestamp": "2026-07-12T12:00:00+08:00",
        "lat": 39.9042,
        "lon": 116.4074,
        "timezone": 8,
        "ayanamsa": "lahiri",
        "node_mode": "mean",
        "location_convention": "wgs84",
    })

    assert packet["status"] == "computed"
    assert packet["chart_source"] == "swiss_ephemeris_backend"
    assert packet["ascendant"]["degree"] >= 0
    assert "Sun" in packet["planets"]
    assert "question_timestamp" in packet


def test_prashna_context_rejects_missing_time_or_non_wgs84_location():
    base = {"question_text": "x", "lat": 1, "lon": 1, "timezone": 0}
    with pytest.raises(PrashnaContextError, match="question_timestamp"):
        build_prashna_context(base)
    with pytest.raises(PrashnaContextError, match="location_convention"):
        build_prashna_context({**base, "question_timestamp": "2026-01-01T00:00:00+00:00", "location_convention": "unknown"})
