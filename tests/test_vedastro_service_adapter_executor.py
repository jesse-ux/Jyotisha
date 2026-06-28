from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
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
    assert report["default_timeout_seconds"] >= 3
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
    assert "start_date" in report["range_scan_request_contract"]
    assert "range_scan_response_contract" in report
    assert "evidence_ledger" in report["range_scan_response_contract"]
    assert report["range_scan_event_allowlist"]["marriage"]["event_ids"]
    assert "marriage" in report["range_scan_event_allowlist"]["marriage"]["tags"]


def test_vedastro_service_adapter_returns_controlled_unconfigured_status() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/vedastro_service_adapter.py", "--case", "beijing_first_use_demo"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
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
    completed = subprocess.run(
        [sys.executable, "scripts/ephemeris_adapter_contract.py", "vedastro_service_adapter_candidate"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
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
    assert report["request_preview"]["domain"] == "marriage"
    assert report["request_preview"]["start_date"] == "2026-01-01"
    assert report["request_preview"]["end_date"] == "2031-01-01"
    assert report["request_preview"]["event_model"] == "vedastro_events_at_range_candidate"
    assert report["source_metadata"]["endpoint"] == "https://example.invalid/vedastro"


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
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            assert payload["operation"] == "range_scan"
            assert payload["domain"] == "marriage"
            assert payload["start_date"] == "2026-01-01"
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
