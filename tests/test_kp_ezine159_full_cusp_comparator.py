from __future__ import annotations

import json
from pathlib import Path

from scripts.kp_ezine159_full_cusp_comparator import build_report


ROOT = Path(__file__).resolve().parents[1]


def test_ezine_159_compares_eleven_transcribed_cusp_lord_rows() -> None:
    raw = json.loads(
        (ROOT / "references/oracle/vedicastro_kp_ezine159_female_1983_2026_07_23.json").read_text(encoding="utf-8")
    )
    report = build_report(raw)

    assert report["status"] == "public_kp_eleven_cusp_lord_rows_match_observation"
    assert report["claim_status"] == "observation_only"
    assert report["summary"]["transcribed_cusp_count"] == 11
    assert report["summary"]["matched_field_count"] == 55
    assert report["summary"]["mismatched_field_count"] == 0
    assert report["summary"]["untranscribed_cusps"] == [12]
