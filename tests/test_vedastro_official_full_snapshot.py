from __future__ import annotations

import json
import os
import subprocess
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_adapter(*args: str, env: dict[str, str] | None = None) -> dict:
    completed = subprocess.run(
        [sys.executable, "scripts/vedastro_service_adapter.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env=env,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    return json.loads(completed.stdout)


def test_schema_declares_official_full_snapshot_contract() -> None:
    report = _run_adapter("--print-schema")

    assert "official_full_snapshot_request_contract" in report
    assert "BirthTime" in report["official_full_snapshot_request_contract"]["common_body_fields"]
    assert report["official_full_snapshot_request_contract"]["primary_source"] == "vedastro_official"
    assert "official_full_snapshot_response_contract" in report
    assert "snapshot_sections" in report["official_full_snapshot_response_contract"]
    assert report["vedastro_calculation_coverage"]["official_api_builder_calculators"] == "600+"


def test_official_full_snapshot_unconfigured_builds_full_request_manifest() -> None:
    env = os.environ.copy()
    env.pop("VEDASTRO_API_ENDPOINT", None)
    env.pop("VEDASTRO_ENABLE_NETWORK", None)
    env["JYOTISH_SKIP_LOCAL_ENV"] = "1"

    report = _run_adapter("--official-full-snapshot", "--case", "user_REDACTED_YEAR_test", env=env)

    assert report["backend"] == "vedastro_service_adapter_candidate"
    assert report["operation"] == "official_full_snapshot"
    assert report["primary_source"] == "vedastro_official"
    assert report["status"] == "service_endpoint_not_configured"
    assert report["available"] is False
    assert report["snapshot_sections"] == {}
    assert report["request_manifest"]["source_role"] == "primary_official_raw_evidence"
    section_names = {item["section"] for item in report["request_manifest"]["requests"]}
    assert {"chart_core", "house_core", "dasha_all", "events_overview"}.issubset(section_names)
    backlog_names = {
        item["section"]
        for item in report["request_manifest"]["method_catalog"]["backlog_sections"]
    }
    assert {"varga_all", "shadbala", "ashtakavarga"}.issubset(backlog_names)
    assert report["user_visibility"] == "backend_raw_evidence_not_direct_user_report"
    assert report["source_metadata"]["provenance_mode"] == "vedastro_official_primary_candidate"


def test_official_full_snapshot_preview_when_network_disabled() -> None:
    env = os.environ.copy()
    env["VEDASTRO_API_ENDPOINT"] = "https://example.invalid/api"
    env.pop("VEDASTRO_ENABLE_NETWORK", None)
    env["JYOTISH_SKIP_LOCAL_ENV"] = "1"

    report = _run_adapter("--official-full-snapshot", "--case", "beijing_first_use_demo", env=env)

    assert report["status"] == "network_execution_disabled"
    assert report["request_manifest"]["requests"]
    assert report["source_metadata"]["endpoint"] == "https://example.invalid/api"
    assert report["source_metadata"]["provenance_mode"] == "vedastro_official_primary_candidate"


def test_official_full_snapshot_dasha_request_uses_official_range_contract(monkeypatch) -> None:
    from scripts import vedastro_service_adapter as adapter

    monkeypatch.delenv("VEDASTRO_API_ENDPOINT", raising=False)
    monkeypatch.delenv("VEDASTRO_ENABLE_NETWORK", raising=False)

    report = adapter.run_official_full_snapshot_for_case(
        {
            "year": REDACTED_YEAR,
            "month": 4,
            "day": 17,
            "hour": 14,
            "minute": 49,
            "lat": 36.42,
            "lon": 114.2,
            "tz": 8,
            "reference_date": "2026-06-29",
        },
        case_id="unit_dasha_contract",
    )

    dasha_request = next(
        item for item in report["request_manifest"]["requests"] if item["section"] == "dasha_all"
    )
    body = dasha_request["body"]

    assert report["request_manifest"]["reference_date"] == "2026-06-29"
    assert report["source_metadata"]["reference_date"] == "2026-06-29"
    assert dasha_request["calculator_name"] == "DasaAtRange"
    assert body["birthTime"]["StdTime"] == "REDACTED_TIME 17/04/REDACTED_YEAR +08:00"
    assert body["startTime"]["StdTime"] == "00:00 01/01/2026 +08:00"
    assert body["endTime"]["StdTime"] == "23:59 31/12/2026 +08:00"
    assert body["levels"] == 3
    assert body["precisionHours"] == 100
    assert body["Ayanamsa"] == "lahiri"
    assert "StartTime" not in body
    assert "EndTime" not in body
    assert "time" not in body


def test_official_full_snapshot_prioritizes_timing_sections_before_heavy_fanout(monkeypatch) -> None:
    from scripts import vedastro_service_adapter as adapter

    monkeypatch.delenv("VEDASTRO_API_ENDPOINT", raising=False)
    monkeypatch.delenv("VEDASTRO_ENABLE_NETWORK", raising=False)

    report = adapter.run_official_full_snapshot_for_case(
        {
            "year": REDACTED_YEAR,
            "month": 4,
            "day": 17,
            "hour": 14,
            "minute": 49,
            "lat": 36.42,
            "lon": 114.2,
            "tz": 8,
            "reference_date": "2026-06-29",
        },
        case_id="unit_timing_first",
    )

    order = [item["section"] for item in report["request_manifest"]["requests"]]

    assert order[:2] == ["events_overview", "dasha_all"]
    assert order.index("events_overview") < order.index("chart_core")
    assert order.index("dasha_all") < order.index("house_core")


def test_official_full_snapshot_marks_semantic_rate_limit_payloads(monkeypatch) -> None:
    from scripts import vedastro_service_adapter as adapter

    calls = []

    def fake_post(endpoint, request_item):
        calls.append((request_item["section"], request_item.get("fanout_value")))
        if request_item["section"] == "chart_core" and request_item.get("fanout_value") == "Mars":
            return {
                "Status": "Fail",
                "Payload": "Free tier rate limit exceeded (5 calls/minute).",
            }, 1, []
        return {
            "Status": "Pass",
            "Payload": {
                "AllPlanetData": {
                    "PlanetRasiD1Sign": {"Name": "Aries", "DegreesIn": {"TotalDegrees": "3.5"}},
                    "PlanetNirayanaLongitude": {"TotalDegrees": "3.5"},
                },
                "AllHouseData": {
                    "HouseRasiD1Sign": {"Name": "Leo", "DegreesIn": {"TotalDegrees": "13.0"}},
                },
                "DasaAtRange": {},
                "SearchEvents": [],
            },
        }, 1, []

    monkeypatch.setenv("VEDASTRO_API_ENDPOINT", "https://example.invalid/api")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "1")
    monkeypatch.setattr(adapter, "_post_official_snapshot_section", fake_post)

    result = adapter.run_official_full_snapshot_for_case(
        {
            "year": REDACTED_YEAR,
            "month": 4,
            "day": 17,
            "hour": 14,
            "minute": 49,
            "lat": 36.42,
            "lon": 114.2,
            "tz": 8,
            "reference_date": "2026-06-29",
        },
        case_id="unit_rate_limit",
    )

    assert ("chart_core", "Mars") in calls
    assert result["section_statuses"]["chart_core"] == "rate_limited"
    assert result["section_statuses"]["chart_core_fanout"]["Mars"] == "rate_limited"
    assert result["source_metadata"]["rate_limited_sections"] == ["chart_core"]
    assert result["source_metadata"]["production_hint"] == "configure_vedastro_api_key_or_self_host_official_api"


def test_orchestrator_attaches_official_full_snapshot_before_range_scan(monkeypatch) -> None:
    from scripts import vedastro_evidence_orchestrator as orchestrator

    calls: list[str] = []

    def fake_snapshot(birth_payload, *, case_id="user_chart"):
        calls.append("snapshot")
        assert birth_payload["reference_date"] == "2026-06-29"
        return {
            "backend": "vedastro_service_adapter_candidate",
            "operation": "official_full_snapshot",
            "primary_source": "vedastro_official",
            "available": False,
            "status": "network_execution_disabled",
            "snapshot_sections": {},
            "source_metadata": {"provenance_mode": "vedastro_official_primary_candidate"},
        }

    def fake_scan(case, domain, start_date, end_date, case_id):
        calls.append(f"range:{domain}")
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "network_execution_disabled",
            "operation": "range_scan",
            "domain": domain,
            "event_count": 0,
            "evidence_ledger": [],
        }

    monkeypatch.setattr(orchestrator, "run_official_full_snapshot_for_case", fake_snapshot)
    monkeypatch.setattr(orchestrator, "run_range_scan_for_case", fake_scan)

    result = orchestrator.orchestrate_vedastro_evidence(
        {
            "year": REDACTED_YEAR,
            "month": 4,
            "day": 17,
            "hour": 14,
            "minute": 49,
            "lat": 36.42,
            "lon": 114.2,
            "tz": 8.0,
        },
        route="overview",
        reference_date="2026-06-29",
    )

    assert calls[0] == "snapshot"
    assert result["official_full_snapshot"]["primary_source"] == "vedastro_official"
    assert result["source_metadata"]["node_coverage"]["official_full_snapshot_first"] is True


def test_shared_priority_promotes_official_chart_and_keeps_local_as_supplemental() -> None:
    from scripts.vedastro_priority import apply_vedastro_source_priority

    local_chart = {
        "source": "local_engine",
        "planets": {"Sun": {"sign": "Cancer"}},
        "ascendant": {"sign": "Virgo"},
        "houses": {"House1": {"sign": "Virgo"}},
        "birth_info": {"date": "REDACTED_DATE"},
    }
    report = {"chart": local_chart, "modules": {"chart": local_chart}}
    official_snapshot = {
        "status": "partial",
        "available": True,
        "operation": "official_full_snapshot",
        "primary_source": "vedastro_official",
        "official_chart": {
            "source": "vedastro_official",
            "primary_source": "vedastro_official",
            "planets": {"Sun": {"source": "vedastro_official", "sign": "Aries"}},
            "ascendant": {"source": "vedastro_official", "sign": "Leo"},
            "houses": {"House1": {"source": "vedastro_official", "sign": "Leo"}},
            "coverage": {"planet_count": 1, "house_count": 1},
        },
    }

    apply_vedastro_source_priority(report, official_snapshot=official_snapshot)

    assert report["chart"]["source"] == "vedastro_official_primary"
    assert report["chart"]["primary_source"] == "vedastro_official"
    assert report["chart"]["planets"]["Sun"]["sign"] == "Aries"
    assert report["chart"]["source_priority"][0] == "vedastro_official_snapshot"
    assert report["chart"]["local_engine_role"] == "supplemental_crosscheck_or_fallback"
    assert report["modules"]["local_engine_chart_fallback"]["planets"]["Sun"]["sign"] == "Cancer"
    assert report["modules"]["source_priority"]["mode"] == "vedastro_official_primary"
    assert report["modules"]["source_priority"]["local_engine_role"] == "supplemental_crosscheck_or_fallback"


def test_shared_priority_marks_local_fallback_only_when_official_blocked() -> None:
    from scripts.vedastro_priority import apply_vedastro_source_priority

    local_chart = {
        "source": "local_engine",
        "planets": {"Sun": {"sign": "Cancer"}},
        "ascendant": {"sign": "Virgo"},
        "houses": {"House1": {"sign": "Virgo"}},
    }
    report = {"chart": local_chart, "modules": {"chart": local_chart}}
    official_snapshot = {
        "status": "network_execution_disabled",
        "available": False,
        "operation": "official_full_snapshot",
        "primary_source": "vedastro_official",
        "reason": "network disabled",
    }

    apply_vedastro_source_priority(report, official_snapshot=official_snapshot)

    assert report["chart"]["source"] == "local_engine_fallback"
    assert report["chart"]["primary_source"] == "local_engine"
    assert report["chart"]["fallback_reason"] == "VedAstro official snapshot blocked: network_execution_disabled"
    assert report["modules"]["source_priority"]["mode"] == "local_fallback_official_blocked"
    assert report["modules"]["source_priority"]["official_snapshot_status"] == "network_execution_disabled"


def test_full_reading_prompt_pack_exposes_vedastro_official_snapshot_boundary() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/jyotish_engine.py",
            "full-reading",
            "--year",
            "REDACTED_YEAR",
            "--month",
            "4",
            "--day",
            "17",
            "--hour",
            "14",
            "--minute",
            "49",
            "--lat",
            "36.42",
            "--lon",
            "114.2",
            "--tz",
            "8",
            "--today",
            "2026-06-29",
            "--transit-date",
            "2026-06-29",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)

    snapshot = report["modules"]["vedastro_official_full_snapshot"]
    assert snapshot["operation"] == "official_full_snapshot"
    assert snapshot["primary_source"] == "vedastro_official"
    prompt_snapshot = report["ai_prompt_pack"]["evidence_snapshot"]["vedastro_official_full_snapshot"]
    assert prompt_snapshot["primary_source"] == "vedastro_official"
    assert prompt_snapshot["status"] in {"ok", "partial", "service_endpoint_not_configured", "network_execution_disabled", "blocked"}


def test_full_reading_official_snapshot_uses_requested_reference_date(monkeypatch) -> None:
    from scripts import jyotish_engine

    captured: dict[str, str] = {}

    def fake_snapshot(case, *, case_id="user_chart"):
        captured["reference_date"] = case.get("reference_date")
        return {
            "status": "network_execution_disabled",
            "available": False,
            "operation": "official_full_snapshot",
            "primary_source": "vedastro_official",
            "reason": "stub",
            "snapshot_sections": {},
            "source_metadata": {},
        }

    fake_adapter = types.SimpleNamespace(run_official_full_snapshot_for_case=fake_snapshot)
    fake_priority = types.SimpleNamespace(apply_vedastro_source_priority=lambda report, official_snapshot: report)
    monkeypatch.setitem(sys.modules, "vedastro_service_adapter", fake_adapter)
    monkeypatch.setitem(sys.modules, "vedastro_priority", fake_priority)

    class Args:
        year = REDACTED_YEAR
        month = 4
        day = 17
        hour = 14
        minute = 49
        lat = 36.42
        lon = 114.2
        tz = 8
        ayanamsa = "lahiri"
        node_mode = "mean"
        today = "2026-06-09"
        transit_date = "2026-06-09"

    report = {"modules": {}, "warnings": []}
    jyotish_engine._attach_vedastro_official_full_snapshot(report, Args())

    assert captured["reference_date"] == "2026-06-09"
    assert report["modules"]["vedastro_official_full_snapshot"]["operation"] == "official_full_snapshot"


def test_official_full_snapshot_extracts_official_chart_and_varga_from_pass_payload(monkeypatch) -> None:
    from scripts import vedastro_service_adapter as adapter

    calls = []

    def fake_post(endpoint, request_item):
        calls.append((request_item["section"], request_item.get("fanout_value")))
        section = request_item["section"]
        if section == "chart_core":
            planet = request_item["fanout_value"]
            return {
                "Status": "Pass",
                "Payload": {
                    "AllPlanetData": {
                        "PlanetRasiD1Sign": {"Name": "Aries", "DegreesIn": {"TotalDegrees": "3.5"}},
                        "PlanetHoraD2Signs": {"Name": "Leo", "DegreesIn": {"TotalDegrees": "7.0"}},
                        "PlanetNavamshaD9Sign": {"Name": "Taurus", "DegreesIn": {"TotalDegrees": "1.5"}},
                        "PlanetDashamamshaD10Sign": {"Name": "Taurus", "DegreesIn": {"TotalDegrees": "5.0"}},
                        "PlanetNirayanaLongitude": {"TotalDegrees": "3.5"},
                        "HousePlanetOccupiesBasedOnSign": "House9",
                    }
                },
            }, 1, []
        if section == "house_core":
            return {
                "Status": "Pass",
                "Payload": {
                    "AllHouseData": {
                        "HouseRasiD1Sign": {"Name": "Leo", "DegreesIn": {"TotalDegrees": "13.0"}},
                        "HouseHoraD2Sign": {"Name": "Leo", "DegreesIn": {"TotalDegrees": "26.0"}},
                        "HouseNavamshaD9Sign": {"Name": "Cancer", "DegreesIn": {"TotalDegrees": "27.7"}},
                        "HouseDashamamshaD10Sign": {"Name": "Sagittarius", "DegreesIn": {"TotalDegrees": "10.8"}},
                    }
                },
            }, 1, []
        return {"Status": "Fail", "Payload": "not mapped"}, 1, []

    monkeypatch.setenv("VEDASTRO_API_ENDPOINT", "https://example.invalid/api")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "1")
    monkeypatch.setattr(adapter, "_post_official_snapshot_section", fake_post)

    result = adapter.run_official_full_snapshot_for_case(
        {
            "year": REDACTED_YEAR,
            "month": 4,
            "day": 17,
            "hour": 14,
            "minute": 49,
            "lat": 36.42,
            "lon": 114.2,
            "tz": 8,
        },
        case_id="unit",
    )

    assert ("chart_core", "Sun") in calls
    assert ("house_core", "House1") in calls
    assert result["status"] == "partial"
    assert result["section_statuses"]["events_overview"] == "fail"
    official_chart = result["official_chart"]
    assert official_chart["source"] == "vedastro_official"
    assert official_chart["planets"]["Sun"]["sign"] == "Aries"
    assert official_chart["planets"]["Sun"]["source"] == "vedastro_official"
    assert official_chart["planets"]["Sun"]["vargas"]["D9"]["sign"] == "Taurus"
    assert official_chart["ascendant"]["sign"] == "Leo"
    assert official_chart["ascendant"]["vargas"]["D10"]["sign"] == "Sagittarius"
