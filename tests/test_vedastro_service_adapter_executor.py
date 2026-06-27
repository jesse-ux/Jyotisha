from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


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
