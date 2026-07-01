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
    assert report["request_manifest"]["source_role"] == "primary_official_raw_evidence"
    section_names = {item["section"] for item in report["request_manifest"]["requests"]}
    assert {"chart_core", "house_core", "dasha_all", "events_overview"}.issubset(section_names)
    backlog_names = {
        item["section"]
        for item in report["request_manifest"]["method_catalog"]["backlog_sections"]
    }
    assert {"varga_all"}.issubset(backlog_names)
    assert "shadbala" not in backlog_names
    assert "ashtakavarga" not in backlog_names
    assert report["user_visibility"] == "backend_raw_evidence_not_direct_user_report"
    assert report["source_metadata"]["provenance_mode"] == "vedastro_official_primary_candidate"
    assert report["status"] in {"service_endpoint_not_configured", "partial", "ok"}
    if report["status"] == "service_endpoint_not_configured":
        assert report["available"] is False
        assert report["snapshot_sections"] == {}
    else:
        assert report["available"] is True
        assert report["source_metadata"]["official_python_path"] in {
            "vedastro_official_capability_runner",
            "vedastro_python_bridge_bundle_fallback",
        }


def test_official_full_snapshot_preview_when_network_disabled() -> None:
    env = os.environ.copy()
    env["VEDASTRO_API_ENDPOINT"] = "https://example.invalid/api"
    env.pop("VEDASTRO_ENABLE_NETWORK", None)
    env["JYOTISH_SKIP_LOCAL_ENV"] = "1"

    report = _run_adapter("--official-full-snapshot", "--case", "beijing_first_use_demo", env=env)

    assert report["request_manifest"]["requests"]
    assert report["source_metadata"]["endpoint"] == "https://example.invalid/api"
    assert report["source_metadata"]["provenance_mode"] == "vedastro_official_primary_candidate"
    assert report["status"] in {"network_execution_disabled", "partial", "ok"}
    if report["status"] != "network_execution_disabled":
        assert report["source_metadata"]["official_python_path"] in {
            "vedastro_official_capability_runner",
            "vedastro_python_bridge_bundle_fallback",
        }


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


def test_post_json_with_retry_waits_for_free_tier_slot(monkeypatch) -> None:
    from scripts import vedastro_service_adapter as adapter

    monotonic_values = iter([0.0, 0.1, 0.2, 0.9, 1.2, 1.3])
    sleep_calls: list[float] = []

    def fake_monotonic() -> float:
        return next(monotonic_values)

    def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    def fake_post(endpoint: str, request_preview: dict[str, object]) -> dict[str, object]:
        return {"Status": "Pass", "Payload": {"echo": request_preview}}

    monkeypatch.delenv("VEDASTRO_API_KEY", raising=False)
    monkeypatch.setenv("VEDASTRO_FREE_TIER_MAX_REQUESTS", "1")
    monkeypatch.setenv("VEDASTRO_FREE_TIER_WINDOW_SECONDS", "1")
    monkeypatch.setenv("VEDASTRO_CACHE_TTL_SECONDS", "0")
    monkeypatch.setattr(adapter.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(adapter.time, "sleep", fake_sleep)
    monkeypatch.setattr(adapter, "_post_json", fake_post)
    monkeypatch.setattr(adapter, "_FREE_TIER_REQUEST_TIMESTAMPS", [])

    first, first_attempts, first_retries = adapter._post_json_with_retry(
        "https://api.vedastro.org/api",
        {"operation": "range_scan", "official_request_profile": {"endpoint_path": "/Calculate/SearchEvents", "body": {"foo": "bar"}}},
    )
    second, second_attempts, second_retries = adapter._post_json_with_retry(
        "https://api.vedastro.org/api",
        {"operation": "range_scan", "official_request_profile": {"endpoint_path": "/Calculate/SearchEvents", "body": {"foo": "baz"}}},
    )

    assert first_attempts == 1
    assert second_attempts == 1
    assert first_retries == []
    assert second_retries == []
    assert sleep_calls and sleep_calls[0] > 0
    assert first["source_metadata"]["free_tier_rate_limit"]["waited_seconds"] == 0
    assert second["source_metadata"]["free_tier_rate_limit"]["waited_seconds"] > 0


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
    env = os.environ.copy()
    env.pop("VEDASTRO_API_ENDPOINT", None)
    env.pop("VEDASTRO_ENABLE_NETWORK", None)
    env["JYOTISH_SKIP_LOCAL_ENV"] = "1"

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
        env=env,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)

    snapshot = report["modules"]["vedastro_official_full_snapshot"]
    assert snapshot["operation"] == "official_full_snapshot"
    assert snapshot["primary_source"] == "vedastro_official"
    prompt_snapshot = report["ai_prompt_pack"]["evidence_snapshot"]["vedastro_official_full_snapshot"]
    assert prompt_snapshot["primary_source"] == "vedastro_official"
    assert prompt_snapshot["status"] in {"ok", "partial", "service_endpoint_not_configured", "network_execution_disabled", "blocked"}
    assert "strict_workflow_contracts" in prompt_snapshot
    assert "strict_workflow_routes_available" in prompt_snapshot
    for route in ("relationship", "career", "finance"):
        contract = prompt_snapshot["strict_workflow_contracts"][route]
        assert "adjudication_stages" in contract
        assert "multi_reference_reading_summary" in contract


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

    if ("chart_core", "Sun") not in calls:
        assert result["source_metadata"]["python_bridge"]["coverage"]["source_mode"] == "official_python_bridge_bundle"
        assert result["section_statuses"]["chart_core"] == "ok"
        assert result["section_statuses"]["house_core"] == "ok"
    else:
        assert ("house_core", "House1") in calls or result["section_statuses"]["house_core"] == "ok"
    assert result["status"] in {"partial", "ok"}
    assert result["section_statuses"]["events_overview"] in {"fail", "ok"}
    official_chart = result["official_chart"]
    assert official_chart["source"] == "vedastro_official"
    assert official_chart["planets"]["Sun"]["sign"] == "Aries"
    assert official_chart["planets"]["Sun"]["source"] == "vedastro_official"
    assert official_chart["planets"]["Sun"]["vargas"]["D9"]["sign"] == "Taurus"
    assert official_chart["ascendant"]["sign"] == "Leo"
    assert official_chart["ascendant"]["vargas"]["D10"]["sign"] == "Sagittarius"


def test_official_full_snapshot_can_use_python_bridge_bundle_without_rest_endpoint(monkeypatch) -> None:
    from scripts import vedastro_service_adapter as adapter

    monkeypatch.delenv("VEDASTRO_API_ENDPOINT", raising=False)
    monkeypatch.delenv("VEDASTRO_ENABLE_NETWORK", raising=False)
    monkeypatch.setattr(
        adapter,
        "_try_official_capability_runner_snapshot_bundle",
        lambda case: {
            "available": False,
            "status": "blocked",
            "source": "vedastro_official_capability_runner",
            "snapshot_sections": {},
            "section_statuses": {},
            "coverage": {"source_mode": "official_capability_runner_bundle", "filled_sections": []},
        },
    )

    def fake_bundle(case: dict[str, object]) -> dict[str, object]:
        assert case["year"] == REDACTED_YEAR
        assert case["reference_date"] == "2026-06-29"
        return {
            "available": True,
            "status": "ok",
            "source": "vedastro_python_bridge",
            "snapshot_sections": {
                "chart_core": {
                    "Sun": {
                        "Payload": {
                            "AllPlanetData": {
                                "PlanetRasiD1Sign": {"Name": "Aries", "DegreesIn": {"TotalDegrees": "3.5"}},
                                "PlanetNavamshaD9Sign": {"Name": "Taurus", "DegreesIn": {"TotalDegrees": "1.5"}},
                                "PlanetDashamamshaD10Sign": {"Name": "Taurus", "DegreesIn": {"TotalDegrees": "5.0"}},
                                "PlanetNirayanaLongitude": {"TotalDegrees": "3.5"},
                                "HousePlanetOccupiesBasedOnSign": "House9",
                            }
                        }
                    }
                },
                "house_core": {
                    "House1": {
                        "Payload": {
                            "AllHouseData": {
                                "HouseBhavaChalitSign": {"Name": "Leo", "DegreesIn": {"TotalDegrees": "13.0"}},
                                "HouseNavamshaD9Sign": {"Name": "Cancer", "DegreesIn": {"TotalDegrees": "27.7"}},
                                "HouseDashamamshaD10Sign": {"Name": "Sagittarius", "DegreesIn": {"TotalDegrees": "10.8"}},
                            }
                        }
                    }
                },
                "dasha_all": {"Status": "Pass", "Payload": {"DasaAtRange": [{"Lord": "Venus"}]}},
                "vimshottari_now": {"Status": "Pass", "Payload": {"DasaAtTime": {"Lord": "Venus"}}},
                "chara_dasha_now": {"Status": "Pass", "Payload": {"GetCharaDasaAtTime": {"Sign": "Leo"}}},
                "shadbala": {"Status": "Pass", "Payload": {"AllPlanetStrength": {"Sun": 527.36}}},
                "ashtakavarga": {"Status": "Pass", "Payload": {"AshtakvargaLifeMap": {"TotalBindus": 337}}},
            },
            "section_statuses": {
                "chart_core": "ok",
                "house_core": "ok",
                "dasha_all": "ok",
                "vimshottari_now": "ok",
                "chara_dasha_now": "ok",
                "shadbala": "ok",
                "ashtakavarga": "ok",
            },
            "coverage": {
                "source_mode": "official_python_bridge_bundle",
                "filled_sections": [
                    "chart_core",
                    "house_core",
                    "dasha_all",
                    "vimshottari_now",
                    "chara_dasha_now",
                    "shadbala",
                    "ashtakavarga",
                ],
            },
        }

    monkeypatch.setattr(adapter, "_try_official_python_bridge_snapshot_bundle", fake_bundle)

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
        case_id="python_bundle_only",
    )

    assert result["available"] is True
    assert result["status"] == "ok"
    assert result["primary_source"] == "vedastro_official"
    assert result["source_metadata"]["python_bridge"]["status"] == "ok"
    assert result["source_metadata"]["python_bridge"]["coverage"]["source_mode"] == "official_python_bridge_bundle"
    assert result["official_chart"]["planets"]["Sun"]["sign"] == "Aries"
    assert result["official_chart"]["ascendant"]["sign"] == "Leo"
    assert result["snapshot_sections"]["shadbala"]["Payload"]["AllPlanetStrength"]["Sun"] == 527.36
    assert result["snapshot_sections"]["ashtakavarga"]["Payload"]["AshtakvargaLifeMap"]["TotalBindus"] == 337


def test_official_full_snapshot_prefers_official_capability_runner_bundle(monkeypatch) -> None:
    from scripts import vedastro_service_adapter as adapter

    monkeypatch.delenv("VEDASTRO_API_ENDPOINT", raising=False)
    monkeypatch.delenv("VEDASTRO_ENABLE_NETWORK", raising=False)

    def fake_runner(case: dict[str, object]) -> dict[str, object]:
        assert case["reference_date"] == "2026-06-29"
        return {
            "available": True,
            "status": "ok",
            "source": "vedastro_official_capability_runner",
            "bundle": "official_full_snapshot",
            "snapshot_sections": {
                "chart_core": {
                    "Sun": {
                        "Payload": {
                            "AllPlanetData": {
                                "PlanetRasiD1Sign": {"Name": "Aries", "DegreesIn": {"TotalDegrees": "3.5"}},
                                "PlanetNavamshaD9Sign": {"Name": "Taurus", "DegreesIn": {"TotalDegrees": "1.5"}},
                            }
                        }
                    }
                },
                "house_core": {
                    "House1": {
                        "Payload": {
                            "AllHouseData": {
                                "HouseBhavaChalitSign": {"Name": "Leo", "DegreesIn": {"TotalDegrees": "13.0"}},
                            }
                        }
                    }
                },
                "dasha_all": {"Status": "Pass", "Payload": {"DasaAtRange": [{"Lord": "Venus"}]}},
                "vimshottari_now": {"Status": "Pass", "Payload": {"DasaAtTime": {"Lord": "Venus"}}},
                "chara_dasha_now": {"Status": "Pass", "Payload": {"GetCharaDasaAtTime": {"Sign": "Leo"}}},
                "shadbala": {"Status": "Pass", "Payload": {"AllPlanetStrength": {"Sun": 527.36}}},
                "ashtakavarga": {"Status": "Pass", "Payload": {"AshtakvargaLifeMap": {"TotalBindus": 337}}},
            },
            "section_statuses": {
                "chart_core": "ok",
                "house_core": "ok",
                "dasha_all": "ok",
                "vimshottari_now": "ok",
                "chara_dasha_now": "ok",
                "shadbala": "ok",
                "ashtakavarga": "ok",
            },
            "coverage": {
                "source_mode": "official_capability_runner_bundle",
                "filled_sections": [
                    "chart_core",
                    "house_core",
                    "dasha_all",
                    "vimshottari_now",
                    "chara_dasha_now",
                    "shadbala",
                    "ashtakavarga",
                ],
            },
        }

    monkeypatch.setattr(adapter, "_try_official_capability_runner_snapshot_bundle", fake_runner)
    monkeypatch.setattr(
        adapter,
        "_try_official_python_bridge_snapshot_bundle",
        lambda case: {"available": False, "status": "blocked", "snapshot_sections": {}, "section_statuses": {}, "coverage": {"source_mode": "official_python_bridge_bundle", "filled_sections": []}},
    )

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
        case_id="runner_primary",
    )

    assert result["status"] == "ok"
    assert result["source_metadata"]["official_python_path"] == "vedastro_official_capability_runner"
    assert result["source_metadata"]["official_python_bundle"]["status"] == "ok"
    assert result["official_chart"]["planets"]["Sun"]["sign"] == "Aries"
    assert result["official_chart"]["ascendant"]["sign"] == "Leo"


def test_official_full_snapshot_attaches_full_capability_catalog_summary(monkeypatch) -> None:
    from scripts import vedastro_service_adapter as adapter

    monkeypatch.delenv("VEDASTRO_API_ENDPOINT", raising=False)
    monkeypatch.delenv("VEDASTRO_ENABLE_NETWORK", raising=False)

    monkeypatch.setattr(
        adapter,
        "_try_official_capability_runner_snapshot_bundle",
        lambda case: {
            "available": True,
            "status": "ok",
            "source": "vedastro_official_capability_runner",
            "bundle": "official_full_snapshot",
            "snapshot_sections": {
                "chart_core": {
                    "Sun": {
                        "Payload": {
                            "AllPlanetData": {
                                "PlanetRasiD1Sign": {"Name": "Aries", "DegreesIn": {"TotalDegrees": "3.5"}},
                            }
                        }
                    }
                },
                "house_core": {
                    "House1": {
                        "Payload": {
                            "AllHouseData": {
                                "HouseBhavaChalitSign": {"Name": "Leo", "DegreesIn": {"TotalDegrees": "13.0"}},
                            }
                        }
                    }
                },
            },
            "section_statuses": {"chart_core": "ok", "house_core": "ok"},
            "coverage": {"source_mode": "official_capability_runner_bundle", "filled_sections": ["chart_core", "house_core"]},
        },
    )
    monkeypatch.setattr(
        adapter,
        "_try_official_full_capability_catalog_bundle",
        lambda case: {
            "available": True,
            "status": "partial",
            "source": "vedastro_official_capability_runner",
            "bundle": "official_full_capability_catalog",
            "summary": {
                "catalog_method_count": 641,
                "executed_method_count": 80,
                "ok_method_count": 72,
                "unsupported_method_count": 420,
                "blocked_method_count": 149,
                "sample_limit": 80,
            },
            "coverage": {"source_mode": "official_full_capability_catalog", "safe_sampling": True},
            "domain_routing": {
                "career": {
                    "method_count": 30,
                    "auto_method_count": 18,
                    "needs_user_context_count": 0,
                    "needs_user_text_count": 0,
                    "blocked_method_count": 12,
                    "high_priority_methods": ["SearchEvents", "DasaAtRange"],
                }
            },
            "dynamic_selection": {
                "career": {
                    "requested_theme": "career",
                    "selected_methods": [
                        {"method": "SearchEvents", "citation_id": "vedastro:career:SearchEvents", "execution_policy": "auto"},
                        {"method": "DasaAtRange", "citation_id": "vedastro:career:DasaAtRange", "execution_policy": "auto"},
                    ],
                    "needs_user_context_methods": [],
                    "report_reference": {
                        "theme": "career",
                        "citation_ids": ["vedastro:career:SearchEvents", "vedastro:career:DasaAtRange"],
                        "auto_count": 2,
                        "needs_user_context_count": 0,
                        "blocked_count": 0,
                    },
                }
            },
            "bucket_statuses": {"time_only": {"total": 137, "executed": 10, "ok": 10, "unsupported": 0, "blocked": 127}},
            "method_statuses": {"AllPlanetData": {"status": "ok", "executed": True}},
        },
    )
    monkeypatch.setattr(
        adapter,
        "_try_official_python_bridge_snapshot_bundle",
        lambda case: {"available": False, "status": "blocked", "snapshot_sections": {}, "section_statuses": {}, "coverage": {"source_mode": "official_python_bridge_bundle", "filled_sections": []}},
    )

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
        case_id="with_full_catalog",
    )

    catalog = result["official_full_capability_catalog"]
    assert catalog["summary"]["catalog_method_count"] == 641
    assert catalog["summary"]["executed_method_count"] == 80
    assert result["source_metadata"]["official_full_capability_catalog"]["status"] == "partial"
    assert result["source_metadata"]["official_full_capability_catalog"]["summary"]["sample_limit"] == 80
    assert result["source_metadata"]["official_full_capability_catalog"]["domain_routing"]["career"]["auto_method_count"] == 18
    assert result["source_metadata"]["official_full_capability_catalog"]["dynamic_selection"]["career"]["report_reference"]["auto_count"] == 2


def test_official_full_snapshot_marks_ok_when_fast_primary_sections_are_filled(monkeypatch) -> None:
    from scripts import vedastro_service_adapter as adapter

    monkeypatch.delenv("VEDASTRO_API_ENDPOINT", raising=False)
    monkeypatch.delenv("VEDASTRO_ENABLE_NETWORK", raising=False)
    monkeypatch.setattr(
        adapter,
        "_try_official_capability_runner_snapshot_bundle",
        lambda case: {
            "available": False,
            "status": "blocked",
            "source": "vedastro_official_capability_runner",
            "snapshot_sections": {},
            "section_statuses": {},
            "coverage": {"source_mode": "official_capability_runner_bundle", "filled_sections": []},
        },
    )

    monkeypatch.setattr(
        adapter,
        "_try_official_python_bridge_snapshot_bundle",
        lambda case: {
            "available": True,
            "status": "ok",
            "source": "vedastro_python_bridge",
            "snapshot_sections": {
                "chart_core": {"Sun": {"Payload": {"AllPlanetData": {"PlanetRasiD1Sign": {"Name": "Aries", "DegreesIn": {"TotalDegrees": "3.5"}}}}}},
                "house_core": {"House1": {"Payload": {"AllHouseData": {"HouseBhavaChalitSign": {"Name": "Leo", "DegreesIn": {"TotalDegrees": "13.0"}}}}}},
                "dasha_all": {"Status": "Pass", "Payload": {"DasaAtRange": []}},
                "vimshottari_now": {"Status": "Pass", "Payload": {"DasaAtTime": {}}},
                "chara_dasha_now": {"Status": "Pass", "Payload": {"GetCharaDasaAtTime": {}}},
                "shadbala": {"Status": "Pass", "Payload": {"AllPlanetStrength": {"Sun": 527.36}}},
                "ashtakavarga": {"Status": "Pass", "Payload": {"AshtakvargaLifeMap": {"TotalBindus": 337}}},
            },
            "section_statuses": {
                "chart_core": "ok",
                "house_core": "ok",
                "dasha_all": "ok",
                "vimshottari_now": "ok",
                "chara_dasha_now": "ok",
                "shadbala": "ok",
                "ashtakavarga": "ok",
            },
            "coverage": {
                "source_mode": "official_python_bridge_bundle",
                "filled_sections": [
                    "chart_core",
                    "house_core",
                    "dasha_all",
                    "vimshottari_now",
                    "chara_dasha_now",
                    "shadbala",
                    "ashtakavarga",
                ],
            },
        },
    )

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
        case_id="fast_primary_ok",
    )

    assert result["status"] == "ok"
    assert result["source_metadata"]["fast_primary_ok"] is True


def test_official_full_snapshot_skips_rest_sections_already_filled_by_python_bundle(monkeypatch) -> None:
    from scripts import vedastro_service_adapter as adapter

    rest_calls: list[tuple[str, object]] = []
    monkeypatch.setattr(
        adapter,
        "_try_official_capability_runner_snapshot_bundle",
        lambda case: {
            "available": False,
            "status": "blocked",
            "source": "vedastro_official_capability_runner",
            "snapshot_sections": {},
            "section_statuses": {},
            "coverage": {"source_mode": "official_capability_runner_bundle", "filled_sections": []},
        },
    )

    def fake_bundle(case: dict[str, object]) -> dict[str, object]:
        return {
            "available": True,
            "status": "partial",
            "source": "vedastro_python_bridge",
            "snapshot_sections": {
                "chart_core": {
                    "Sun": {
                        "Payload": {
                            "AllPlanetData": {
                                "PlanetRasiD1Sign": {"Name": "Aries", "DegreesIn": {"TotalDegrees": "3.5"}},
                                "PlanetNirayanaLongitude": {"TotalDegrees": "3.5"},
                            }
                        }
                    }
                },
                "house_core": {
                    "House1": {
                        "Payload": {
                            "AllHouseData": {
                                "HouseBhavaChalitSign": {"Name": "Leo", "DegreesIn": {"TotalDegrees": "13.0"}}
                            }
                        }
                    }
                },
                "shadbala": {"Status": "Pass", "Payload": {"AllPlanetStrength": {"Sun": 527.36}}},
                "ashtakavarga": {"Status": "Pass", "Payload": {"AshtakvargaLifeMap": {"TotalBindus": 337}}},
            },
            "section_statuses": {
                "chart_core": "ok",
                "house_core": "ok",
                "shadbala": "ok",
                "ashtakavarga": "ok",
            },
            "coverage": {"source_mode": "official_python_bridge_bundle", "filled_sections": ["chart_core", "house_core", "shadbala", "ashtakavarga"]},
        }

    def fake_post(endpoint, request_item):
        rest_calls.append((request_item["section"], request_item.get("fanout_value")))
        return {"Status": "Pass", "Payload": {"echo": request_item["section"]}}, 1, []

    monkeypatch.setenv("VEDASTRO_API_ENDPOINT", "https://example.invalid/api")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "1")
    monkeypatch.setattr(adapter, "_try_official_python_bridge_snapshot_bundle", fake_bundle)
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
        case_id="python_bundle_plus_rest",
    )

    called_sections = {section for section, _ in rest_calls}
    assert "chart_core" not in called_sections
    assert "house_core" not in called_sections
    assert "events_overview" in called_sections
    assert "dasha_all" in called_sections
    assert result["source_metadata"]["python_bridge"]["status"] == "partial"


def test_official_full_snapshot_semantic_cache_reuses_full_bundle(monkeypatch, tmp_path) -> None:
    from scripts import vedastro_service_adapter as adapter

    calls = {"count": 0}

    def fake_run(case, case_id="user_chart"):
        calls["count"] += 1
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": True,
            "status": "ok",
            "operation": "official_full_snapshot",
            "primary_source": "vedastro_official",
            "snapshot_sections": {"chart_core": {"Sun": {"Status": "Pass"}}},
            "official_chart": {"planets": {"Sun": {"sign": "Aries"}}, "ascendant": {"sign": "Leo"}},
            "official_full_capability_catalog": {},
            "section_statuses": {"chart_core": "ok"},
            "request_manifest": {"requests": [{"section": "chart_core"}]},
            "user_visibility": "backend_raw_evidence_not_direct_user_report",
            "source_metadata": {},
        }

    monkeypatch.setenv("VEDASTRO_OFFICIAL_FULL_SNAPSHOT_CACHE_TTL_SECONDS", "600")
    monkeypatch.setattr(adapter, "_run_official_full_snapshot_case", fake_run)
    monkeypatch.setattr(adapter, "ARTIFACT_DIR", tmp_path)

    payload = {
        "year": REDACTED_YEAR,
        "month": 4,
        "day": 17,
        "hour": 14,
        "minute": 49,
        "lat": 36.42,
        "lon": 114.2,
        "tz": 8,
        "reference_date": "2026-06-30",
    }

    first = adapter.run_official_full_snapshot_for_case(payload, case_id="semantic_cache_demo")
    second = adapter.run_official_full_snapshot_for_case(payload, case_id="semantic_cache_demo")

    assert calls["count"] == 1
    assert first["source_metadata"]["semantic_cache"]["cache_hit"] is False
    assert second["source_metadata"]["semantic_cache"]["cache_hit"] is True
    assert second["source_metadata"]["semantic_cache"]["scope"] == "official_full_snapshot"


def test_official_full_snapshot_semantic_cache_reuses_bundle_across_case_ids(monkeypatch, tmp_path) -> None:
    from scripts import vedastro_service_adapter as adapter

    calls = {"count": 0}

    def fake_run(case, case_id="user_chart"):
        calls["count"] += 1
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": True,
            "status": "ok",
            "operation": "official_full_snapshot",
            "primary_source": "vedastro_official",
            "snapshot_sections": {"chart_core": {"Sun": {"Status": "Pass"}}},
            "official_chart": {"planets": {"Sun": {"sign": "Aries"}}, "ascendant": {"sign": "Leo"}},
            "official_full_capability_catalog": {},
            "section_statuses": {"chart_core": "ok"},
            "request_manifest": {"case_id": case_id, "requests": [{"section": "chart_core"}]},
            "user_visibility": "backend_raw_evidence_not_direct_user_report",
            "source_metadata": {},
        }

    monkeypatch.setenv("VEDASTRO_OFFICIAL_FULL_SNAPSHOT_CACHE_TTL_SECONDS", "600")
    monkeypatch.setattr(adapter, "_run_official_full_snapshot_case", fake_run)
    monkeypatch.setattr(adapter, "ARTIFACT_DIR", tmp_path)

    payload = {
        "year": REDACTED_YEAR,
        "month": 4,
        "day": 17,
        "hour": 14,
        "minute": 49,
        "lat": 36.42,
        "lon": 114.2,
        "tz": 8,
        "reference_date": "2026-06-30",
    }

    first = adapter.run_official_full_snapshot_for_case(payload, case_id="api_chart_official_full_snapshot")
    second = adapter.run_official_full_snapshot_for_case(payload, case_id="full_reading_official_primary")

    assert calls["count"] == 1
    assert first["source_metadata"]["semantic_cache"]["cache_hit"] is False
    assert second["source_metadata"]["semantic_cache"]["cache_hit"] is True
    assert second["request_manifest"]["case_id"] == "full_reading_official_primary"
