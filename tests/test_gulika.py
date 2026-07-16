from datetime import datetime

from scripts.gulika import GHATIKA_END, calculate_gulika


def test_gulika_uses_prasna_marga_weekday_table() -> None:
    assert GHATIKA_END[6] == {"day": 26, "night": 10}
    assert GHATIKA_END[0] == {"day": 22, "night": 6}


def test_gulika_returns_sidereal_segment_ascendant_with_audit_trace() -> None:
    result = calculate_gulika(datetime(1990, 6, 15, 12, 0), lat=39.9042, lon=116.4074, tz=8)

    assert result["status"] == "partial"
    assert 0 <= result["longitude"] < 360
    assert result["ghatika_end"] in range(0, 31)
    assert result["rule_source"].endswith("#3.5")
