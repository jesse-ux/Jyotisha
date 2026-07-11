from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from scripts import vedastro_user_entrypoint


ROOT = Path(__file__).resolve().parents[1]


def test_capability_catalog_timeout_degrades_to_blocked(monkeypatch) -> None:
    def timeout_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs.get("timeout"))

    monkeypatch.setattr(vedastro_user_entrypoint.subprocess, "run", timeout_run)

    report = vedastro_user_entrypoint._run_capability_catalog({"year": 2000})

    assert report["available"] is False
    assert report["status"] == "official_full_capability_catalog_timeout"
    assert report["summary"] == {}


def test_user_entrypoint_runs_catalog_and_strict_workflow_contract() -> None:
    catalog_stub = {
        "available": True,
        "status": "ok",
        "capabilities": [
            {
                "method": "SearchEvents",
                "signature": "(birthTime, atTime, eventTagList)",
                "bucket": "event_time",
                "parameter_names": ["birthTime", "atTime", "eventTagList"],
                "callable": True,
            },
            {
                "method": "DasaAtRange",
                "signature": "(birthTime, startTime, endTime, levels, precisionHours)",
                "bucket": "dasha_at_range",
                "parameter_names": ["birthTime", "startTime", "endTime", "levels", "precisionHours"],
                "callable": True,
            },
            {
                "method": "AllPlanetDashamamshaSign",
                "signature": "(planetName, time)",
                "bucket": "planet_time",
                "parameter_names": ["planetName", "time"],
                "callable": True,
            },
            {
                "method": "HealthProblemEvent",
                "signature": "(birthTime, startTime, endTime)",
                "bucket": "event_range",
                "parameter_names": ["birthTime", "startTime", "endTime"],
                "callable": True,
            },
        ],
        "buckets": {
            "event_time": {"count": 1, "examples": ["SearchEvents"]},
            "dasha_at_range": {"count": 1, "examples": ["DasaAtRange"]},
            "planet_time": {"count": 1, "examples": ["AllPlanetDashamamshaSign"]},
            "event_range": {"count": 1, "examples": ["HealthProblemEvent"]},
        },
    }
    runner_stub = {
        "SearchEvents": {"available": True, "status": "ok", "result": {"Events": []}},
        "DasaAtRange": {"available": True, "status": "ok", "result": {"Periods": []}},
        "AllPlanetDashamamshaSign": {"available": True, "status": "ok", "result": {"Name": "Capricorn"}},
        "HealthProblemEvent": {"available": True, "status": "ok", "result": {}},
    }

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_user_entrypoint.py",
            "--year",
            "1955",
            "--month",
            "2",
            "--day",
            "24",
            "--hour",
            "19",
            "--minute",
            "15",
            "--lat",
            "37.7749",
            "--lon",
            "-122.4194",
            "--tz",
            "8",
            "--question",
            "事业机会什么时候出现",
            "--themes",
            "career,health",
            "--reference-date",
            "2026-07-02",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env={
            **os.environ,
            "JYOTISH_SKIP_LOCAL_ENV": "1",
            "VEDASTRO_API_ENDPOINT": "https://api.vedastro.org/api",
            "VEDASTRO_ENABLE_NETWORK": "1",
            "VEDASTRO_TIMEOUT_SECONDS": "20",
            "VEDASTRO_CACHE_TTL_SECONDS": "600",
            "VEDASTRO_OFFICIAL_FULL_SNAPSHOT_CACHE_TTL_SECONDS": "600",
            "VEDASTRO_FREE_TIER_QUEUE": "1",
            "VEDASTRO_FULL_CATALOG_SAMPLE_LIMIT": "8",
            "VEDASTRO_OFFICIAL_CAPABILITY_CATALOG_STUB": json.dumps(catalog_stub),
            "VEDASTRO_OFFICIAL_CAPABILITY_RUNNER_STUB": json.dumps(runner_stub),
        },
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)

    assert report["scope"] == "vedastro_user_entrypoint"
    assert report["runtime_mode"]["mode"] == "official_extended"
    assert report["input"]["themes"] == ["career", "health"]
    assert report["official_capability_catalog"]["summary"]["catalog_method_count"] == 4
    assert report["official_capability_catalog"]["summary"]["sample_limit"] == 8
    assert report["official_capability_catalog"]["dynamic_selection"]["career"]["selected_methods"]
    assert "health" in report["official_capability_catalog"]["domain_routing"]
    assert report["cache_and_queue"]["official_full_snapshot_cache_ttl_seconds"] == 600
    assert report["cache_and_queue"]["range_scan_cache_ttl_seconds"] == 600
    assert report["cache_and_queue"]["free_tier_queue_enabled"] is True
    assert report["runtime_mode"]["free_tier_possible_with_cache_queue"] is True
    assert report["runtime_mode"]["readiness_blockers"] == ["premium_key_missing"]
    assert report["cache_and_queue"]["free_tier_strategy"]["using_free_tier"] is True
    assert report["cache_and_queue"]["free_tier_strategy"]["queue_enabled"] is True
    assert report["cache_and_queue"]["free_tier_strategy"]["guard_status"] == "within_free_tier_strategy"
    assert report["strict_workflow"]["triggered"] is True
    assert report["strict_workflow"]["primary_route"] == "career"
    assert "career" in report["strict_workflow"]["routes_available"]
    assert report["honesty_boundary"]["all_641_methods_executed"] is False
    assert "official_full_capability_catalog" in report["user_commands"]["json"]


def test_user_entrypoint_emits_official_raw_response_when_requested() -> None:
    catalog_stub = {
        "available": True,
        "status": "ok",
        "capabilities": [
            {
                "method": "AllPlanetData",
                "signature": "(birthTime)",
                "bucket": "chart_core",
                "parameter_names": ["birthTime"],
                "callable": True,
            }
        ],
        "buckets": {"chart_core": {"count": 1, "examples": ["AllPlanetData"]}},
    }
    raw_response = {
        "source": "vedastro_official_full_snapshot",
        "sections": {"chart_core": {"Status": "Pass"}},
        "section_statuses": {"chart_core": "ok"},
    }
    snapshot_stub = {
        "status": "ok",
        "available": True,
        "operation": "official_full_snapshot",
        "raw_response": raw_response,
        "source_metadata": {"artifact_path": "scratch/local/vedastro_adapter/stub.json"},
    }

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_user_entrypoint.py",
            "--year",
            "1955",
            "--month",
            "2",
            "--day",
            "24",
            "--hour",
            "19",
            "--minute",
            "15",
            "--lat",
            "37.7749",
            "--lon",
            "-122.4194",
            "--tz",
            "8",
            "--question",
            "事业机会什么时候出现",
            "--themes",
            "career",
            "--reference-date",
            "2026-07-02",
            "--require-official-raw-response",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env={
            **os.environ,
            "JYOTISH_SKIP_LOCAL_ENV": "1",
            "VEDASTRO_API_ENDPOINT": "https://api.vedastro.org/api",
            "VEDASTRO_ENABLE_NETWORK": "1",
            "VEDASTRO_TIMEOUT_SECONDS": "20",
            "VEDASTRO_OFFICIAL_CAPABILITY_CATALOG_STUB": json.dumps(catalog_stub),
            "VEDASTRO_OFFICIAL_FULL_SNAPSHOT_STUB": json.dumps(snapshot_stub),
        },
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["vedastro_official_full_snapshot"]["status"] == "ok"
    assert report["vedastro_official_full_snapshot"]["raw_response_available"] is True
    assert report["official_raw_response"] == raw_response


def test_user_entrypoint_markdown_documents_boundaries() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_user_entrypoint.py",
            "--year",
            "1955",
            "--month",
            "2",
            "--day",
            "24",
            "--hour",
            "19",
            "--minute",
            "15",
            "--lat",
            "37.7749",
            "--lon",
            "-122.4194",
            "--tz",
            "8",
            "--question",
            "婚恋",
            "--themes",
            "marriage",
            "--reference-date",
            "2026-07-02",
            "--format",
            "markdown",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env={
            **os.environ,
            "JYOTISH_SKIP_LOCAL_ENV": "1",
            "VEDASTRO_API_ENDPOINT": "",
            "VEDASTRO_ENABLE_NETWORK": "",
            "VEDASTRO_TIMEOUT_SECONDS": "",
        },
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert "VedAstro 用户级入口" in completed.stdout
    assert "fast_local_fallback" in completed.stdout
    assert "不会把 641 项全部当作已执行" in completed.stdout
    assert "strict workflow" in completed.stdout
