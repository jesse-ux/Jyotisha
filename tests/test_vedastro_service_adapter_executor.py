from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import types
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer


ROOT = Path(__file__).resolve().parents[1]


def test_vedastro_service_adapter_executor_schema_is_declared() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/vedastro_service_adapter.py", "--print-schema"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["adapter"] == "vedastro_service_adapter"
    assert report["transport"] == "http_json_service_boundary"
    assert 3 <= report["default_timeout_seconds"] <= 5
    assert report["retry_policy"]["max_attempts"] >= 1
    assert report["retry_policy"]["backoff_seconds"] >= 0
    assert "endpoint" in report["required_env"]
    assert "ayanamsa_policy" in report["request_contract"]
    assert "bodies" in report["response_contract"]
    assert "source_metadata" in report["response_contract"]
    assert "request_example" in report
    assert report["provenance_contract"]["external_service"] is True
    assert "endpoint" in report["provenance_contract"]["required_fields"]
    assert "range_scan_request_contract" in report
    assert "domain" in report["range_scan_request_contract"]
    assert "vedastro_event_method" in report["range_scan_request_contract"]
    assert "start_date" in report["range_scan_request_contract"]
    assert report["vedastro_calculation_coverage"] == {
        "official_python_library_calculations": "596+",
        "official_api_builder_calculators": "600+",
        "official_events_builder_events": "400+",
        "official_events_builder_methods": ["SearchEvents", "GetEventTiming", "ListEventTypes"],
        "range_scan_role": "high_frequency_life_event_radar",
        "intended_use": "external_timing_evidence_for_strict_workflow",
    }
    assert "range_scan_response_contract" in report
    assert "evidence_ledger" in report["range_scan_response_contract"]
    assert report["range_scan_event_allowlist"]["marriage"]["event_ids"]
    assert "marriage" in report["range_scan_event_allowlist"]["marriage"]["tags"]


def test_vedastro_official_subprocesses_use_adapter_timeout(monkeypatch) -> None:
    from scripts import vedastro_service_adapter as adapter

    monkeypatch.setenv("VEDASTRO_TIMEOUT_SECONDS", "7")
    seen_timeouts = []

    def fake_run(*args, **kwargs):
        seen_timeouts.append(kwargs.get("timeout"))
        return types.SimpleNamespace(returncode=1, stdout="", stderr="simulated failure")

    monkeypatch.setattr(adapter.subprocess, "run", fake_run)
    case = {
        "year": 1990,
        "month": 4,
        "day": 17,
        "hour": 14,
        "minute": 59,
        "lat": 36.42,
        "lon": 114.2,
        "tz": 8,
    }

    bridge = adapter._call_vedastro_python_bridge_high_value("official_full_snapshot_bundle", {})
    runner = adapter._try_official_capability_runner_snapshot_bundle(case)
    catalog = adapter._try_official_full_capability_catalog_bundle(case)

    assert seen_timeouts == [7.0, 7.0, 7.0]
    assert bridge["status"] == "python_bridge_runtime_error"
    assert runner["status"] == "official_capability_runner_runtime_error"
    assert catalog["status"] == "official_full_capability_catalog_runtime_error"


def test_vedastro_official_subprocess_timeouts_are_controlled(monkeypatch) -> None:
    from scripts import vedastro_service_adapter as adapter

    monkeypatch.setenv("VEDASTRO_TIMEOUT_SECONDS", "3")

    def fake_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs.get("timeout"))

    monkeypatch.setattr(adapter.subprocess, "run", fake_timeout)
    case = {
        "year": 1990,
        "month": 4,
        "day": 17,
        "hour": 14,
        "minute": 59,
        "lat": 36.42,
        "lon": 114.2,
        "tz": 8,
    }

    bridge = adapter._call_vedastro_python_bridge_high_value("official_full_snapshot_bundle", {})
    runner = adapter._try_official_capability_runner_snapshot_bundle(case)
    catalog = adapter._try_official_full_capability_catalog_bundle(case)

    assert bridge["status"] == "python_bridge_timeout"
    assert runner["status"] == "official_capability_runner_timeout"
    assert catalog["status"] == "official_full_capability_catalog_timeout"


def test_vedastro_official_snapshot_stops_when_foreground_budget_is_exhausted(monkeypatch) -> None:
    from scripts import vedastro_service_adapter as adapter

    monkeypatch.setenv("VEDASTRO_TIMEOUT_SECONDS", "4")
    monkeypatch.setattr(
        adapter,
        "_try_official_full_capability_catalog_bundle",
        lambda case: {
            "available": False,
            "status": "official_full_capability_catalog_timeout",
            "source": "vedastro_official_capability_runner",
            "bundle": "official_full_capability_catalog",
            "summary": {},
            "coverage": {},
            "domain_routing": {},
            "dynamic_selection": {},
        },
    )
    runner_called = {"value": False}
    bridge_called = {"value": False}

    def fail_runner(case):
        runner_called["value"] = True
        raise AssertionError("snapshot runner should not run after foreground budget is exhausted")

    def fail_bridge(case):
        bridge_called["value"] = True
        raise AssertionError("python bridge fallback should not run after foreground budget is exhausted")

    monkeypatch.setattr(adapter, "_try_official_capability_runner_snapshot_bundle", fail_runner)
    monkeypatch.setattr(adapter, "_try_official_python_bridge_snapshot_bundle", fail_bridge)

    ticks = iter([100.0, 104.1])
    monkeypatch.setattr(adapter.time, "monotonic", lambda: next(ticks))
    result = adapter._run_official_full_snapshot_case({
        "year": 1990,
        "month": 4,
        "day": 17,
        "hour": 14,
        "minute": 59,
        "lat": 36.42,
        "lon": 114.2,
        "tz": 8,
    })

    assert runner_called["value"] is False
    assert bridge_called["value"] is False
    assert result["status"] == "official_snapshot_budget_exhausted"
    assert result["available"] is False
    assert result["source_metadata"]["official_python_bundle"]["status"] == "official_snapshot_budget_exhausted"
    assert result["source_metadata"]["official_full_capability_catalog"]["status"] == "official_full_capability_catalog_skipped_budget_exhausted"


def test_vedastro_official_snapshot_skips_bridge_after_runner_consumes_budget(monkeypatch) -> None:
    from scripts import vedastro_service_adapter as adapter

    monkeypatch.setenv("VEDASTRO_API_ENDPOINT", "https://api.vedastro.org/api")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "1")
    monkeypatch.setenv("VEDASTRO_TIMEOUT_SECONDS", "4")
    monkeypatch.setattr(
        adapter,
        "_try_official_full_capability_catalog_bundle",
        lambda case: {
            "available": True,
            "status": "partial",
            "source": "vedastro_official_capability_runner",
            "bundle": "official_full_capability_catalog",
            "summary": {"catalog_method_count": 641},
            "coverage": {},
            "domain_routing": {},
            "dynamic_selection": {},
        },
    )
    monkeypatch.setattr(
        adapter,
        "_try_official_capability_runner_snapshot_bundle",
        lambda case: {
            "available": False,
            "status": "official_capability_runner_timeout",
            "source": "vedastro_official_capability_runner",
            "bundle": "official_full_snapshot",
            "snapshot_sections": {},
            "section_statuses": {},
            "coverage": {"source_mode": "official_capability_runner_bundle", "filled_sections": []},
        },
    )
    bridge_called = {"value": False}

    def fail_bridge(case):
        bridge_called["value"] = True
        raise AssertionError("python bridge fallback should not run after snapshot runner exhausts budget")

    monkeypatch.setattr(adapter, "_try_official_python_bridge_snapshot_bundle", fail_bridge)

    ticks = iter([100.0, 100.1, 104.2])
    monkeypatch.setattr(adapter.time, "monotonic", lambda: next(ticks))
    result = adapter._run_official_full_snapshot_case({
        "year": 1990,
        "month": 4,
        "day": 17,
        "hour": 14,
        "minute": 59,
        "lat": 36.42,
        "lon": 114.2,
        "tz": 8,
    })

    assert bridge_called["value"] is False
    assert result["status"] == "official_snapshot_budget_exhausted"
    assert result["source_metadata"]["official_python_bundle"]["status"] == "official_snapshot_budget_exhausted"
    assert result["source_metadata"]["official_full_capability_catalog"]["status"] == "official_full_capability_catalog_skipped_budget_exhausted"


def test_vedastro_official_snapshot_budget_does_not_mask_mock_rest_endpoint(monkeypatch) -> None:
    from scripts import vedastro_service_adapter as adapter

    monkeypatch.setenv("VEDASTRO_API_ENDPOINT", "http://127.0.0.1:12345/api")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "1")
    monkeypatch.setenv("VEDASTRO_TIMEOUT_SECONDS", "4")
    monkeypatch.setattr(
        adapter,
        "_try_official_full_capability_catalog_bundle",
        lambda case: {
            "available": False,
            "status": "official_full_capability_catalog_timeout",
            "source": "vedastro_official_capability_runner",
            "bundle": "official_full_capability_catalog",
            "summary": {},
            "coverage": {},
            "domain_routing": {},
            "dynamic_selection": {},
        },
    )
    monkeypatch.setattr(
        adapter,
        "_try_official_capability_runner_snapshot_bundle",
        lambda case: {
            "available": False,
            "status": "official_capability_runner_timeout",
            "source": "vedastro_official_capability_runner",
            "bundle": "official_full_snapshot",
            "snapshot_sections": {},
            "section_statuses": {},
            "coverage": {"source_mode": "official_capability_runner_bundle", "filled_sections": []},
        },
    )

    calls = []

    def fake_post(endpoint, request_item):
        calls.append((endpoint, request_item["section"], request_item.get("fanout_value")))
        return {"Status": "Pass", "Payload": {"ok": True}}, 1, []

    monkeypatch.setattr(adapter, "_try_official_python_bridge_snapshot_bundle", lambda case: {"available": False, "status": "blocked", "snapshot_sections": {}, "section_statuses": {}, "coverage": {"source_mode": "official_python_bridge_bundle", "filled_sections": []}})
    monkeypatch.setattr(adapter, "_post_official_snapshot_section", fake_post)
    ticks = iter([100.0, 100.1, 104.2])
    monkeypatch.setattr(adapter.time, "monotonic", lambda: next(ticks))

    result = adapter._run_official_full_snapshot_case({
        "year": 1990,
        "month": 4,
        "day": 17,
        "hour": 14,
        "minute": 59,
        "lat": 36.42,
        "lon": 114.2,
        "tz": 8,
    })

    assert calls
    assert result["status"] in {"ok", "partial"}
    assert result["source_metadata"]["official_python_bundle"]["status"] == "official_snapshot_budget_exhausted"


def test_vedastro_service_adapter_returns_controlled_unconfigured_status() -> None:
    env = os.environ.copy()
    env.pop("VEDASTRO_API_ENDPOINT", None)
    env.pop("VEDASTRO_ENABLE_NETWORK", None)
    env["JYOTISH_SKIP_LOCAL_ENV"] = "1"

    completed = subprocess.run(
        [sys.executable, "scripts/vedastro_service_adapter.py", "--case", "beijing_first_use_demo"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env=env,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["backend"] == "vedastro_service_adapter_candidate"
    assert report["available"] is False
    assert report["status"] == "service_endpoint_not_configured"
    assert "VEDASTRO" in report["reason"]
    assert report["source_metadata"]["transport"] == "http_json_service_boundary"
    assert report["source_metadata"]["retry_policy"]["max_attempts"] >= 1
    assert report["source_metadata"]["provenance_mode"] == "external_service_candidate"


def test_ephemeris_adapter_contract_can_call_vedastro_candidate_stub() -> None:
    env = os.environ.copy()
    env.pop("VEDASTRO_API_ENDPOINT", None)
    env.pop("VEDASTRO_ENABLE_NETWORK", None)
    env["JYOTISH_SKIP_LOCAL_ENV"] = "1"

    completed = subprocess.run(
        [sys.executable, "scripts/ephemeris_adapter_contract.py", "vedastro_service_adapter_candidate"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env=env,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["candidate_backend"] == "vedastro_service_adapter_candidate"
    first = report["rows"][0]["candidate_backend"]
    assert first["backend"] == "vedastro_service_adapter_candidate"
    assert first["status"] == "service_endpoint_not_configured"


def test_vedastro_service_adapter_builds_request_preview_before_real_network_use() -> None:
    env = os.environ.copy()
    env["VEDASTRO_API_ENDPOINT"] = "https://example.invalid/vedastro"
    env.pop("VEDASTRO_ENABLE_NETWORK", None)
    env["JYOTISH_SKIP_LOCAL_ENV"] = "1"

    completed = subprocess.run(
        [sys.executable, "scripts/vedastro_service_adapter.py", "--case", "beijing_first_use_demo"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env=env,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["backend"] == "vedastro_service_adapter_candidate"
    assert report["status"] == "network_execution_disabled"
    assert report["request_preview"]["year"] == 1990
    assert report["request_preview"]["ayanamsa_policy"] == "lahiri"
    assert report["source_metadata"]["endpoint"] == "https://example.invalid/vedastro"
    assert report["source_metadata"]["provenance_mode"] == "external_service_candidate"


def test_vedastro_service_adapter_builds_range_scan_preview_before_real_network_use() -> None:
    env = os.environ.copy()
    env["VEDASTRO_API_ENDPOINT"] = "https://example.invalid/vedastro"
    env.pop("VEDASTRO_ENABLE_NETWORK", None)
    env["JYOTISH_SKIP_LOCAL_ENV"] = "1"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_service_adapter.py",
            "--range-scan",
            "--domain",
            "marriage",
            "--case",
            "beijing_first_use_demo",
            "--start-date",
            "2026-01-01",
            "--end-date",
            "2031-01-01",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env=env,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["backend"] == "vedastro_service_adapter_candidate"
    assert report["status"] == "network_execution_disabled"
    assert report["request_preview"]["operation"] == "range_scan"
    assert report["request_preview"]["vedastro_event_method"] == "SearchEvents"
    assert report["request_preview"]["domain"] == "marriage"
    assert report["request_preview"]["start_date"] == "2026-01-01"
    assert report["request_preview"]["end_date"] == "2031-01-01"
    assert report["request_preview"]["event_model"] == "vedastro_events_at_range_candidate"
    assert report["source_metadata"]["endpoint"] == "https://example.invalid/vedastro"


def test_vedastro_range_scan_unconfigured_still_returns_official_search_events_preview() -> None:
    env = os.environ.copy()
    env.pop("VEDASTRO_API_ENDPOINT", None)
    env.pop("VEDASTRO_ENABLE_NETWORK", None)
    env["JYOTISH_SKIP_LOCAL_ENV"] = "1"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_service_adapter.py",
            "--range-scan",
            "--domain",
            "wealth",
            "--case",
            "beijing_first_use_demo",
            "--start-date",
            "2026-01-01",
            "--end-date",
            "2031-01-01",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env=env,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["status"] == "service_endpoint_not_configured"
    assert report["request_preview"]["operation"] == "range_scan"
    assert report["request_preview"]["vedastro_event_method"] == "SearchEvents"
    assert report["request_preview"]["domain"] == "wealth"
    assert report["request_preview"]["official_request_profile"]["endpoint_path"] == "/Calculate/SearchEvents"
    assert report["request_preview"]["official_request_profile"]["method"] == "POST"
    assert report["request_preview"]["official_request_profile"]["headers"] == {"Content-Type": "application/json"}
    assert report["request_preview"]["official_request_profile"]["body"]["Ayanamsa"] == "lahiri"
    assert report["request_preview"]["official_request_profile"]["body"]["EventTagList"] == ["LendingMoney", "BorrowingMoney", "BuyingSelling", "General"]
    assert "AtTime" not in report["request_preview"]["official_request_profile"]["body"]
    assert report["request_preview"]["official_request_profile"]["body"]["StartTime"]["StdTime"] == "12:00 01/01/2026 +08:00"
    assert report["request_preview"]["official_request_profile"]["body"]["EndTime"]["StdTime"] == "12:00 01/01/2031 +08:00"
    assert report["request_preview"]["official_request_profile"]["body"]["PrecisionHours"] == 100
    assert report["request_preview"]["live_sampling_request_profile"]["body"]["AtTime"]["StdTime"] == "12:00 01/01/2026 +08:00"


def test_vedastro_schema_declares_official_search_events_live_contract() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/vedastro_service_adapter.py", "--print-schema"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    contract = report["official_search_events_profile_contract"]
    assert contract["route_template"] == "/Calculate/SearchEvents"
    assert contract["method"] == "POST"
    assert contract["optional_auth_header"] == "x-api-key"
    assert "BirthTime" in contract["body_fields"]
    assert "EventTagList" in contract["body_fields"]
    assert "AtTime | StartTime + EndTime + PrecisionHours" in contract["range_mode_fields"]


def test_vedastro_service_adapter_posts_official_search_events_contract() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            assert self.path == "/api/Calculate/SearchEvents"
            assert self.headers.get("Content-Type") == "application/json"
            assert self.headers.get("x-api-key") == "sk_live_test"
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            assert payload["Ayanamsa"] == "lahiri"
            assert payload["EventTagList"] == ["Marriage", "Personal", "General"]
            assert payload["BirthTime"]["StdTime"] == "12:00 01/01/1990 +08:00"
            assert payload["AtTime"]["StdTime"] == "12:00 01/01/2026 +08:00"
            assert "StartTime" not in payload
            response = {
                "Status": "Pass",
                "Payload": [
                    {
                        "Name": "JupiterSupportsMarriageAxis",
                        "StartTime": "2026-05-01",
                        "EndTime": "2026-06-01",
                        "EventTags": ["marriage", "transit"],
                        "Nature": "Good",
                    }
                ],
            }
            body = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = os.environ.copy()
        env["VEDASTRO_API_ENDPOINT"] = f"http://127.0.0.1:{server.server_port}/api"
        env["VEDASTRO_ENABLE_NETWORK"] = "1"
        env["VEDASTRO_API_KEY"] = "sk_live_test"
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/vedastro_service_adapter.py",
                "--range-scan",
                "--domain",
                "marriage",
                "--case",
                "beijing_first_use_demo",
                "--start-date",
                "2026-01-01",
                "--end-date",
                "2026-01-01",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
            env=env,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["status"] == "ok"
    assert report["source_metadata"]["endpoint"].endswith("/api")
    assert report["source_metadata"]["official_endpoint_path"] == "/Calculate/SearchEvents"
    assert report["source_metadata"]["official_request_profile"]["method"] == "POST"
    metadata_headers = report["source_metadata"]["official_request_profile"]["headers"]
    assert metadata_headers == {"Content-Type": "application/json"}
    assert report["source_metadata"]["official_request_profile_hash"]
    assert report["source_metadata"]["request_hash"] != report["source_metadata"]["official_request_profile_hash"]


def test_vedastro_service_adapter_can_normalize_mock_http_response() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            assert payload["year"] == 1990
            response = {
                "ayanamsa_value": 23.717413,
                "node_policy": "mean",
                "body_list": ["Sun", "Moon", "Ascendant", "Rahu", "Ketu"],
                "bodies": {
                    "Sun": {"sidereal_longitude": 256.757014, "sign": "Sagittarius"},
                    "Moon": {"sidereal_longitude": 305.071255, "sign": "Aquarius"},
                    "Ascendant": {"sidereal_longitude": 348.1199, "sign": "Pisces"},
                    "Rahu": {"sidereal_longitude": 294.735223, "sign": "Capricorn"},
                    "Ketu": {"sidereal_longitude": 114.735223, "sign": "Cancer"},
                },
                "source_metadata": {
                    "service": "mock-vedastro",
                    "version": "test",
                },
            }
            body = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = os.environ.copy()
        env["VEDASTRO_API_ENDPOINT"] = f"http://127.0.0.1:{server.server_port}/vedastro"
        env["VEDASTRO_ENABLE_NETWORK"] = "1"
        completed = subprocess.run(
            [sys.executable, "scripts/vedastro_service_adapter.py", "--case", "beijing_first_use_demo"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
            env=env,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["backend"] == "vedastro_service_adapter_candidate"
    assert report["available"] is True
    assert report["status"] == "ok"
    assert report["ayanamsa_value"] == 23.717413
    assert report["bodies"]["Sun"]["sign"] == "Sagittarius"
    assert report["source_metadata"]["transport"] == "http_json_service_boundary"
    assert report["source_metadata"]["endpoint"].startswith("http://127.0.0.1:")


def test_vedastro_service_adapter_can_normalize_mock_range_scan_response() -> None:
    seen_at_times: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            assert payload["Ayanamsa"] == "lahiri"
            assert payload["EventTagList"] == ["Marriage", "Personal", "General"]
            assert payload["BirthTime"]["StdTime"] == "12:00 01/01/1990 +08:00"
            seen_at_times.append(payload["AtTime"]["StdTime"])
            response = {
                "events": [
                    {
                        "id": "GocharJupiterIn7th",
                        "name": "Jupiter supports marriage axis",
                        "start": "2026-05-01",
                        "end": "2026-06-01",
                        "score": 72,
                        "tags": ["marriage", "transit"],
                    }
                ],
                "source_metadata": {
                    "service": "mock-vedastro",
                    "version": "range-test",
                },
            }
            body = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = os.environ.copy()
        env["VEDASTRO_API_ENDPOINT"] = f"http://127.0.0.1:{server.server_port}/vedastro"
        env["VEDASTRO_ENABLE_NETWORK"] = "1"
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/vedastro_service_adapter.py",
                "--range-scan",
                "--domain",
                "marriage",
                "--case",
                "beijing_first_use_demo",
                "--start-date",
                "2026-01-01",
                "--end-date",
                "2031-01-01",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
            env=env,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["backend"] == "vedastro_service_adapter_candidate"
    assert report["available"] is True
    assert report["status"] == "ok"
    assert report["operation"] == "range_scan"
    assert report["domain"] == "marriage"
    assert report["event_count"] == 1
    assert report["top_event"] == {
        "event_id": "GocharJupiterIn7th",
        "signal_key": "gochar_jupiter_7th_marriage",
        "signal_label": "Jupiter in 7th marriage window",
        "signal_family": "marriage_trigger",
        "score": 72,
        "start": "2026-05-01",
        "end": "2026-06-01",
        "tags": ["marriage", "transit"],
    }
    assert report["evidence_ledger"][0]["event_id"] == "GocharJupiterIn7th"
    assert report["evidence_ledger"][0]["signal_key"] == "gochar_jupiter_7th_marriage"
    assert report["evidence_ledger"][0]["signal_label"] == "Jupiter in 7th marriage window"
    assert report["evidence_ledger"][0]["signal_family"] == "marriage_trigger"
    assert report["evidence_ledger"][0]["domain"] == "marriage"
    assert report["evidence_ledger"][0]["score"] == 72
    assert report["evidence_ledger"][0]["raw"]["name"] == "Jupiter supports marriage axis"
    assert report["source_metadata"]["endpoint"].startswith("http://127.0.0.1:")
    assert report["source_metadata"]["sampling_mode"] == "at_time_sweep"
    assert report["source_metadata"]["sample_count"] >= 2
    assert seen_at_times[0] == "12:00 01/01/2026 +08:00"
    assert len(set(seen_at_times)) >= 2


def test_vedastro_range_scan_records_hashes_and_artifact_path() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            response = {
                "events": [
                    {
                        "id": "GocharJupiterIn7th",
                        "name": "Jupiter enters 7th house",
                        "start": "2026-05-01",
                        "end": "2026-06-01",
                        "score": 72,
                        "tags": ["marriage", "transit"],
                    }
                ],
                "source_metadata": {
                    "service": "mock-vedastro",
                    "version": "artifact-test",
                },
            }
            body = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = os.environ.copy()
        env["VEDASTRO_API_ENDPOINT"] = f"http://127.0.0.1:{server.server_port}/vedastro"
        env["VEDASTRO_ENABLE_NETWORK"] = "1"
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/vedastro_service_adapter.py",
                "--range-scan",
                "--domain",
                "marriage",
                "--case",
                "beijing_first_use_demo",
                "--start-date",
                "2026-01-01",
                "--end-date",
                "2031-01-01",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
            env=env,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    metadata = report["source_metadata"]
    assert len(metadata["request_hash"]) == 64
    assert len(metadata["response_hash"]) == 64
    assert metadata["method"] == "POST"
    assert metadata["operation"] == "range_scan"
    assert metadata["vedastro_event_method"] == "SearchEvents"
    assert metadata["official_endpoint_path"] == "/Calculate/SearchEvents"
    assert metadata["official_request_profile"]["method"] == "POST"
    assert metadata["official_request_profile"]["body"]["EventTagList"] == ["Marriage", "Personal", "General"]
    assert metadata["official_request_profile_hash"]
    assert metadata["allowlist_domain"] == "marriage"
    assert metadata["allowlist_event_count"] == 1
    assert metadata["filtered_event_count"] == 1
    assert metadata["attempt_count"] >= 1
    assert metadata["sample_count"] >= 1
    assert metadata["sampling_mode"] == "at_time_sweep"
    artifact_path = ROOT / metadata["artifact_path"]
    assert artifact_path.exists()
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["source_metadata"]["request_hash"] == metadata["request_hash"]
    assert artifact["source_metadata"]["response_hash"] == metadata["response_hash"]
    assert artifact["evidence_ledger"][0]["event_id"] == "GocharJupiterIn7th"


def test_vedastro_range_scan_retries_transient_http_error() -> None:
    class Handler(BaseHTTPRequestHandler):
        attempts = 0

        def do_POST(self) -> None:  # noqa: N802
            Handler.attempts += 1
            if Handler.attempts == 1:
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                return
            response = {
                "events": [
                    {
                        "id": "GocharJupiterIn7th",
                        "name": "Jupiter enters 7th house",
                        "start": "2026-05-01",
                        "end": "2026-06-01",
                        "score": 72,
                        "tags": ["marriage", "transit"],
                    }
                ]
            }
            body = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = os.environ.copy()
        env["VEDASTRO_API_ENDPOINT"] = f"http://127.0.0.1:{server.server_port}/vedastro"
        env["VEDASTRO_ENABLE_NETWORK"] = "1"
        env["VEDASTRO_RETRY_BACKOFF_SECONDS"] = "0"
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/vedastro_service_adapter.py",
                "--range-scan",
                "--domain",
                "marriage",
                "--case",
                "beijing_first_use_demo",
                "--start-date",
                "2026-01-01",
                "--end-date",
                "2031-01-01",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
            env=env,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["status"] == "ok"
    assert report["event_count"] == 1
    assert report["source_metadata"]["attempt_count"] >= 2
    assert 503 in report["source_metadata"]["retry_error_codes"]
    assert report["source_metadata"]["sampling_mode"] == "at_time_sweep"


def test_vedastro_range_scan_reuses_cached_live_response() -> None:
    class Handler(BaseHTTPRequestHandler):
        calls = 0

        def do_POST(self) -> None:  # noqa: N802
            Handler.calls += 1
            response = {
                "events": [
                    {
                        "id": "GocharJupiterIn7th",
                        "name": "Jupiter enters 7th house",
                        "start": "2026-05-01",
                        "end": "2026-06-01",
                        "score": 72,
                        "tags": ["marriage", "transit"],
                    }
                ]
            }
            body = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = os.environ.copy()
        env["VEDASTRO_API_ENDPOINT"] = f"http://127.0.0.1:{server.server_port}/vedastro"
        env["VEDASTRO_ENABLE_NETWORK"] = "1"
        env["VEDASTRO_CACHE_TTL_SECONDS"] = "600"
        env["JYOTISH_SKIP_LOCAL_ENV"] = "1"

        first = subprocess.run(
            [
                sys.executable,
                "scripts/vedastro_service_adapter.py",
                "--range-scan",
                "--domain",
                "marriage",
                "--case",
                "beijing_first_use_demo",
                "--start-date",
                "2026-01-01",
                "--end-date",
                "2026-01-01",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
            env=env,
        )
        second = subprocess.run(
            [
                sys.executable,
                "scripts/vedastro_service_adapter.py",
                "--range-scan",
                "--domain",
                "marriage",
                "--case",
                "beijing_first_use_demo",
                "--start-date",
                "2026-01-01",
                "--end-date",
                "2026-01-01",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
            env=env,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert first.returncode == 0, first.stderr or first.stdout
    assert second.returncode == 0, second.stderr or second.stdout
    first_report = json.loads(first.stdout)
    second_report = json.loads(second.stdout)
    assert Handler.calls == 1
    assert first_report["source_metadata"].get("cache_hit") is False
    assert second_report["source_metadata"].get("cache_hit") is True
    assert second_report["event_count"] == first_report["event_count"] == 1


def test_vedastro_service_adapter_applies_domain_allowlist_to_range_scan_noise() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            response = {
                "events": [
                    {
                        "id": "GocharJupiterIn7th",
                        "name": "Jupiter enters 7th house",
                        "start": "2026-05-01",
                        "end": "2026-06-01",
                        "score": 72,
                        "tags": ["marriage", "transit"],
                    },
                    {
                        "id": "RandomMoonMoodShift",
                        "name": "Random moon mood shift",
                        "start": "2026-05-08",
                        "end": "2026-05-09",
                        "score": 91,
                        "tags": ["emotion", "noise"],
                    },
                ]
            }
            body = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = os.environ.copy()
        env["VEDASTRO_API_ENDPOINT"] = f"http://127.0.0.1:{server.server_port}/vedastro"
        env["VEDASTRO_ENABLE_NETWORK"] = "1"
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/vedastro_service_adapter.py",
                "--range-scan",
                "--domain",
                "marriage",
                "--case",
                "beijing_first_use_demo",
                "--start-date",
                "2026-01-01",
                "--end-date",
                "2031-01-01",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
            env=env,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["event_count"] == 1
    assert report["top_event"]["event_id"] == "GocharJupiterIn7th"
    assert report["evidence_ledger"][0]["event_id"] == "GocharJupiterIn7th"


def test_vedastro_service_adapter_preserves_match_metadata_for_official_tag_and_alias_hits() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            response = {
                "Status": "Pass",
                "Payload": [
                    {
                        "Name": "GoodForMarriage",
                        "Nature": "Good",
                        "Description": "Marriage event support.",
                        "StartTime": "2026-05-01",
                        "EndTime": "2026-05-02",
                        "EventTags": ["Marriage"],
                    },
                    {
                        "Name": "PartnershipBlessingWindow",
                        "Nature": "Good",
                        "Description": "Spouse alignment and relationship blessing.",
                        "StartTime": "2026-05-03",
                        "EndTime": "2026-05-04",
                        "EventTags": ["Personal"],
                    },
                ],
            }
            body = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = os.environ.copy()
        env["VEDASTRO_API_ENDPOINT"] = f"http://127.0.0.1:{server.server_port}/api"
        env["VEDASTRO_ENABLE_NETWORK"] = "1"
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/vedastro_service_adapter.py",
                "--range-scan",
                "--domain",
                "marriage",
                "--case",
                "beijing_first_use_demo",
                "--start-date",
                "2026-01-01",
                "--end-date",
                "2026-12-31",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
            env=env,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["event_count"] == 2
    exact = {item["event_id"]: item for item in report["evidence_ledger"]}
    assert exact["GoodForMarriage"]["matched_by"] == "official_tag"
    assert exact["PartnershipBlessingWindow"]["matched_by"] == "alias"
    assert exact["GoodForMarriage"]["confidence"] == "medium_high"
    assert exact["PartnershipBlessingWindow"]["confidence"] == "low"
    assert report["source_metadata"]["mapping_replay"]["match_counts"]["official_tag"] == 1
    assert report["source_metadata"]["mapping_replay"]["match_counts"]["alias"] == 1


def test_vedastro_service_adapter_classifies_http_error() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = os.environ.copy()
        env["VEDASTRO_API_ENDPOINT"] = f"http://127.0.0.1:{server.server_port}/vedastro"
        env["VEDASTRO_ENABLE_NETWORK"] = "1"
        completed = subprocess.run(
            [sys.executable, "scripts/vedastro_service_adapter.py", "--case", "beijing_first_use_demo"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
            env=env,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["status"] == "http_error"
    assert "503" in report["reason"]


def test_vedastro_service_adapter_classifies_invalid_json_response() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            body = b"not-json"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = os.environ.copy()
        env["VEDASTRO_API_ENDPOINT"] = f"http://127.0.0.1:{server.server_port}/vedastro"
        env["VEDASTRO_ENABLE_NETWORK"] = "1"
        completed = subprocess.run(
            [sys.executable, "scripts/vedastro_service_adapter.py", "--case", "beijing_first_use_demo"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
            env=env,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["status"] == "invalid_json"


def test_vedastro_service_adapter_classifies_timeout() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            import time

            time.sleep(0.2)
            body = b"{}"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = os.environ.copy()
        env["VEDASTRO_API_ENDPOINT"] = f"http://127.0.0.1:{server.server_port}/vedastro"
        env["VEDASTRO_ENABLE_NETWORK"] = "1"
        env["VEDASTRO_TIMEOUT_SECONDS"] = "0.05"
        completed = subprocess.run(
            [sys.executable, "scripts/vedastro_service_adapter.py", "--case", "beijing_first_use_demo"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
            env=env,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["status"] == "timeout"
