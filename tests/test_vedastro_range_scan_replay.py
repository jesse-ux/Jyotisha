from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

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


def test_normalize_official_live_payload_supports_nested_searchevents_and_tag_string() -> None:
    payload = {
        "Status": "Pass",
        "Payload": {
            "SearchEvents": [
                {
                    "Name": "BadLunarMonthForBuilding",
                    "Nature": "Bad",
                    "Description": "Building work should be avoided in this lunar month.",
                    "StartTime": {"StdTime": "12:00 01/01/2026 +08:00"},
                    "EndTime": {"StdTime": "12:00 01/01/2026 +08:00"},
                    "Tag": "Building,General",
                }
            ]
        },
    }

    report = vedastro_service_adapter._normalize_range_scan_success(  # noqa: SLF001
        payload,
        "https://api.vedastro.org/api",
        _request_preview("career"),
    )

    assert report["event_count"] == 1
    assert report["evidence_ledger"][0]["event_id"] == "BadLunarMonthForBuilding"
    assert report["evidence_ledger"][0]["matched_by"] == "official_tag"
    assert report["evidence_ledger"][0]["matched_terms"] == ["Building"]
    assert report["evidence_ledger"][0]["tags"] == ["Building", "General"]


def test_run_range_scan_case_refreshes_live_sampling_request_profile_for_each_sample_date() -> None:
    case = vedastro_service_adapter.PARITY_CASES["beijing_first_use_demo"]
    captured_at_times: list[str] = []

    def fake_post_json_with_retry(endpoint: str, request_preview: dict[str, object]):
        live_profile = request_preview.get("live_sampling_request_profile") or {}
        body = live_profile.get("body") if isinstance(live_profile, dict) else {}
        at_time = body.get("AtTime") if isinstance(body, dict) else {}
        std_time = at_time.get("StdTime") if isinstance(at_time, dict) else None
        captured_at_times.append(std_time)
        return {"Status": "Pass", "Payload": {"SearchEvents": []}}, 1, []

    with mock.patch.dict(
        vedastro_service_adapter.os.environ,
        {
            "VEDASTRO_API_ENDPOINT": "https://api.vedastro.org/api",
            "VEDASTRO_ENABLE_NETWORK": "1",
        },
        clear=False,
    ), mock.patch.object(
        vedastro_service_adapter,
        "_iter_sample_dates",
        return_value=["2026-01-01", "2026-03-01"],
    ), mock.patch.object(
        vedastro_service_adapter,
        "_post_json_with_retry",
        side_effect=fake_post_json_with_retry,
    ):
        vedastro_service_adapter._run_range_scan_case(  # noqa: SLF001
            case,
            "wealth",
            "2026-01-01",
            "2026-12-31",
        )

    assert captured_at_times == [
        "12:00 01/01/2026 +08:00",
        "12:00 01/03/2026 +08:00",
    ]
