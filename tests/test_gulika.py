from datetime import datetime

import json
from pathlib import Path

from scripts.gulika import GHATIKA_END, SATURN_PART_START, calculate_gulika


def test_gulika_uses_prasna_marga_weekday_table() -> None:
    assert GHATIKA_END[6] == {"day": 26, "night": 10}
    assert GHATIKA_END[0] == {"day": 22, "night": 6}
    assert SATURN_PART_START[0] == {"day": 5, "night": 1}


def test_gulika_returns_sidereal_segment_ascendant_with_audit_trace() -> None:
    result = calculate_gulika(datetime(1990, 6, 15, 12, 0), lat=39.9042, lon=116.4074, tz=8)

    assert result["status"] == "partial"
    assert 0 <= result["longitude"] < 360
    assert result["part_index"] in range(0, 8)
    assert result["ghatika_end"] is None
    assert result["rule_source"].endswith("#3.5")


def test_gulika_matches_public_pyjhora_smoke_oracle() -> None:
    packet = json.loads(
        Path("references/oracle/prashna_sphuta_pyjhora_public_smoke.json").read_text(encoding="utf-8")
    )
    expected = packet["outputs"]["gulika"]
    result = calculate_gulika(datetime(1990, 1, 1, 12, 0), lat=39.9042, lon=116.4074, tz=8)

    assert result["method"] == "saturn_part_start"
    assert result["sign_idx"] == expected["sign_index"]
    assert abs(result["degree_in_sign"] - expected["degree_in_sign"]) <= 0.5


def test_gulika_night_uses_weekday_of_preceding_sunset() -> None:
    result = calculate_gulika(datetime(2023, 1, 27, 2, 30, 15), lat=23.0225, lon=72.5714, tz=5.5)
    assert result["period"] == "night"
    assert result["weekday"] == 3
    assert result["sign_idx"] == 7
