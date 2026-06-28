from __future__ import annotations

import json
from pathlib import Path

from scripts import vedastro_service_adapter


ROOT = Path(__file__).resolve().parents[1]


def _request_preview(domain: str = "marriage") -> dict:
    return vedastro_service_adapter._range_scan_preview(  # noqa: SLF001
        vedastro_service_adapter.PARITY_CASES["beijing_first_use_demo"],
        domain,
        "2026-01-01",
        "2026-12-31",
    )


def test_official_sample_replay_reports_exact_tag_alias_and_rejected_matches() -> None:
    sample = json.loads((ROOT / "tests" / "test-data" / "vedastro_range_scan_official_sample.json").read_text(encoding="utf-8"))

    report = vedastro_service_adapter._normalize_range_scan_success(  # noqa: SLF001
        sample,
        "https://api.vedastro.org/api",
        _request_preview("marriage"),
    )

    replay = report["source_metadata"]["mapping_replay"]
    assert replay["raw_event_count"] == 4
    assert replay["filtered_event_count"] == 3
    assert replay["match_counts"] == {
        "exact_id": 1,
        "official_tag": 1,
        "alias": 1,
        "rejected": 1,
    }
    assert replay["zero_event_domains"] == []
    assert "Marriage" in replay["matched_tags"]

    by_id = {item["event_id"]: item for item in report["evidence_ledger"]}
    assert by_id["JupiterSupportsMarriageAxis"]["matched_by"] == "exact_id"
    assert by_id["GoodForMarriage"]["matched_by"] == "official_tag"
    assert by_id["PartnershipBlessingWindow"]["matched_by"] == "alias"


def test_replay_stats_track_zero_event_domain_and_rejected_alias_noise() -> None:
    payload = {
        "Status": "Pass",
        "Payload": [
            {
                "Name": "RandomMoonMoodShift",
                "Nature": "Neutral",
                "Description": "Generic transit noise without finance significance.",
                "StartTime": "2026-06-01",
                "EndTime": "2026-06-02",
                "EventTags": ["General", "Gochara"],
            }
        ],
    }

    report = vedastro_service_adapter._normalize_range_scan_success(  # noqa: SLF001
        payload,
        "https://api.vedastro.org/api",
        _request_preview("wealth"),
    )

    assert report["event_count"] == 0
    replay = report["source_metadata"]["mapping_replay"]
    assert replay["raw_event_count"] == 1
    assert replay["filtered_event_count"] == 0
    assert replay["zero_event_domains"] == ["wealth"]
    assert replay["match_counts"]["rejected"] == 1
    assert replay["recommended_allowlist_candidates"] == []
