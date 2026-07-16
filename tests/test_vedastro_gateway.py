from __future__ import annotations

import json


def test_gateway_status_defaults_to_local_first_cn_safe(monkeypatch):
    from scripts import vedastro_gateway

    monkeypatch.delenv("VEDASTRO_GATEWAY_MODE", raising=False)
    monkeypatch.setenv("JYOTISH_SKIP_LOCAL_ENV", "1")
    monkeypatch.delenv("VEDASTRO_SELF_HOST_ENDPOINT", raising=False)
    monkeypatch.delenv("VEDASTRO_API_ENDPOINT", raising=False)
    monkeypatch.delenv("VEDASTRO_CACHE_TTL_SECONDS", raising=False)
    monkeypatch.delenv("VEDASTRO_GATEWAY_QUEUE_ENABLED", raising=False)
    monkeypatch.delenv("VEDASTRO_QUEUE_ENABLED", raising=False)

    status = vedastro_gateway.gateway_status()

    assert status["scope"] == "vedastro_gateway"
    assert status["mode"] == "local_first"
    assert status["direct_browser_access_allowed"] is False
    assert status["frontend_secret_safe"] is True
    assert status["backend_priority"] == ["self_host", "official", "cache", "queue", "local_fallback"]
    assert status["active_backend"] == "local_fallback"
    assert status["official_readiness"]["official_ready"] is False
    assert "missing_endpoint" in status["official_readiness"]["readiness_blockers"]
    assert status["boundary"] == "Users never call VedAstro directly; backend gateway owns cache, queue, and fallback."


def test_gateway_status_reports_cn_gateway_self_host(monkeypatch):
    from scripts import vedastro_gateway

    monkeypatch.setenv("VEDASTRO_GATEWAY_MODE", "cn_gateway")
    monkeypatch.setenv("VEDASTRO_SELF_HOST_ENDPOINT", "https://jyotish-gateway.example.com/vedastro")
    monkeypatch.setenv("VEDASTRO_CACHE_TTL_SECONDS", "604800")
    monkeypatch.setenv("VEDASTRO_GATEWAY_QUEUE_ENABLED", "1")

    status = vedastro_gateway.gateway_status()

    assert status["mode"] == "cn_gateway"
    assert status["self_host_configured"] is True
    assert status["active_backend"] == "self_host"
    assert status["cache_ttl_seconds"] == 604800
    assert status["queue_enabled"] is True


def test_gateway_status_exposes_official_readiness_gate(monkeypatch):
    from scripts import vedastro_gateway

    monkeypatch.setenv("VEDASTRO_API_ENDPOINT", "https://api.vedastro.org/api")
    monkeypatch.setenv("JYOTISH_SKIP_LOCAL_ENV", "1")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "1")
    monkeypatch.setenv("VEDASTRO_TIMEOUT_SECONDS", "20")
    monkeypatch.setenv("VEDASTRO_FREE_TIER_QUEUE", "1")

    status = vedastro_gateway.gateway_status()

    assert status["official_configured"] is True
    assert status["official_readiness"]["official_ready"] is True
    assert status["official_readiness"]["free_tier_possible_with_cache_queue"] is True


def test_gateway_status_never_exposes_vedastro_secret(monkeypatch):
    from scripts import vedastro_gateway

    monkeypatch.setenv("JYOTISH_SKIP_LOCAL_ENV", "1")
    monkeypatch.setenv("VEDASTRO_API_KEY", "sk_live_test_secret")
    status = vedastro_gateway.gateway_status()
    text = json.dumps(status, sort_keys=True)
    assert "sk_live_test_secret" not in text
    assert status["credential_configured"] is True


def test_gateway_run_packet_uses_user_entrypoint_and_marks_not_all_641(monkeypatch):
    from scripts import vedastro_gateway

    monkeypatch.setenv("JYOTISH_SKIP_LOCAL_ENV", "1")
    monkeypatch.setenv("VEDASTRO_GATEWAY_MODE", "cn_gateway")
    monkeypatch.setenv("VEDASTRO_CACHE_TTL_SECONDS", "604800")
    monkeypatch.setenv("VEDASTRO_GATEWAY_QUEUE_ENABLED", "1")
    monkeypatch.setenv("VEDASTRO_FULL_CATALOG_SAMPLE_LIMIT", "0")

    packet = vedastro_gateway.run_gateway_packet(
        {
            "year": 1955,
            "month": 2,
            "day": 24,
            "hour": 19,
            "minute": 15,
            "second": 0,
            "lat": 37.7749,
            "lon": -122.4194,
            "tz": 8,
        },
        question="事业机会什么时候出现",
        themes=["career", "health"],
        reference_date="2026-07-02",
    )

    assert packet["scope"] == "vedastro_gateway_run"
    assert packet["status"] in {"ok", "partial", "queued", "blocked", "cached", "local_fallback"}
    assert packet["official_closure_state"] in {"official_verified", "official_blocked", "local_fallback"}
    assert packet["gateway_status"]["mode"] == "cn_gateway"
    assert packet["official_capability_catalog"]["summary"]["catalog_method_count"] >= 0
    assert packet["honesty_boundary"]["all_641_methods_executed"] is False
    assert packet["user_visibility"]["mainland_cn_safe"] is True


def test_gateway_official_closure_requires_raw_response(monkeypatch):
    from scripts import vedastro_gateway, vedastro_user_entrypoint

    monkeypatch.setenv("JYOTISH_SKIP_LOCAL_ENV", "1")
    monkeypatch.setenv("VEDASTRO_API_ENDPOINT", "https://api.vedastro.org/api")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "1")
    monkeypatch.setenv("VEDASTRO_TIMEOUT_SECONDS", "20")

    def fake_report(_args):
        return {
            "input": {},
            "runtime_mode": {},
            "official_capability_catalog": {"status": "partial", "available": True, "summary": {"catalog_method_count": 641}},
            "cache_and_queue": {},
            "strict_workflow": {},
            "honesty_boundary": {},
        }

    monkeypatch.setattr(vedastro_user_entrypoint, "build_report", fake_report)
    packet = vedastro_gateway.run_gateway_packet({"year": 1955}, question="x")

    assert packet["official_closure_state"] == "official_blocked"
    assert packet["official_closure_reason"] == "official_raw_response_missing"


def test_gateway_official_closure_verified_when_raw_response_present(monkeypatch):
    from scripts import vedastro_gateway, vedastro_user_entrypoint

    monkeypatch.setenv("JYOTISH_SKIP_LOCAL_ENV", "1")
    monkeypatch.setenv("VEDASTRO_API_ENDPOINT", "https://api.vedastro.org/api")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "1")
    monkeypatch.setenv("VEDASTRO_TIMEOUT_SECONDS", "20")

    def fake_report(_args):
        return {
            "input": {},
            "runtime_mode": {},
            "official_capability_catalog": {"status": "partial", "available": True, "summary": {"catalog_method_count": 641}},
            "official_raw_response": {"Status": "Pass"},
            "cache_and_queue": {},
            "strict_workflow": {},
            "honesty_boundary": {},
        }

    monkeypatch.setattr(vedastro_user_entrypoint, "build_report", fake_report)
    packet = vedastro_gateway.run_gateway_packet({"year": 1955}, question="x")

    assert packet["official_closure_state"] == "official_verified"
    assert packet["official_raw_response"] == {"Status": "Pass"}


def test_gateway_requires_and_propagates_entrypoint_official_raw_response(monkeypatch):
    from scripts import vedastro_gateway, vedastro_user_entrypoint

    raw_response = {
        "source": "vedastro_official_full_snapshot",
        "sections": {"chart_core": {"Status": "Pass"}},
    }
    monkeypatch.setenv("JYOTISH_SKIP_LOCAL_ENV", "1")
    monkeypatch.setenv("VEDASTRO_API_ENDPOINT", "https://api.vedastro.org/api")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "1")
    monkeypatch.setenv("VEDASTRO_GATEWAY_REQUIRE_OFFICIAL_RAW_RESPONSE", "1")
    monkeypatch.setattr(
        vedastro_user_entrypoint,
        "build_runtime_mode_report",
        lambda: {"mode": "official_extended", "official_ready": True, "readiness_blockers": []},
    )
    monkeypatch.setattr(
        vedastro_user_entrypoint,
        "_run_capability_catalog",
        lambda _case: {"status": "ok", "available": True, "summary": {"catalog_method_count": 1}},
    )
    monkeypatch.setattr(
        vedastro_user_entrypoint,
        "_run_official_full_snapshot",
        lambda _case: {"status": "ok", "available": True, "raw_response": raw_response},
    )

    packet = vedastro_gateway.run_gateway_packet(
        {"year": 1955, "month": 2, "day": 24, "hour": 19, "minute": 15, "lat": 37.7749, "lon": -122.4194, "tz": 8},
        question="事业机会什么时候出现",
        themes=["career"],
        reference_date="2026-07-02",
    )

    assert packet["official_closure_state"] == "official_verified"
    assert packet["official_closure_reason"] == "official_raw_response_present"
    assert packet["official_raw_response"] == raw_response


def test_gateway_queue_lifecycle_uses_file_job_store(monkeypatch, tmp_path):
    from scripts import vedastro_gateway

    monkeypatch.setenv("VEDASTRO_GATEWAY_QUEUE_DIR", str(tmp_path))
    job = vedastro_gateway.enqueue_gateway_job(
        {
            "year": 1955,
            "month": 2,
            "day": 24,
            "hour": 19,
            "minute": 15,
            "second": 0,
            "lat": 37.7749,
            "lon": -122.4194,
            "tz": 8,
        },
        question="事业机会什么时候出现",
        themes=["career"],
        reference_date="2026-07-02",
    )

    assert job["status"] == "queued"
    assert job["poll_path"].startswith("/api/vedastro_gateway/jobs/")

    stored = vedastro_gateway.get_gateway_job(job["job_id"])
    assert stored["status"] == "queued"
    assert stored["raw_response_archive"]["status"] == "pending"
    assert stored["raw_response_archive"]["official_raw_response_available"] is False

    completed = vedastro_gateway.complete_gateway_job(
        job["job_id"],
        {"scope": "vedastro_gateway_run", "status": "local_fallback"},
    )
    assert completed["status"] == "completed"

    polled = vedastro_gateway.get_gateway_job(job["job_id"])
    assert polled["result"]["status"] == "local_fallback"
    assert polled["raw_response_archive"]["status"] == "stored_gateway_packet_not_official_raw"


def test_gateway_completion_archives_official_raw_response(monkeypatch, tmp_path):
    from scripts import vedastro_gateway

    monkeypatch.setenv("VEDASTRO_GATEWAY_QUEUE_DIR", str(tmp_path))
    job = vedastro_gateway.enqueue_gateway_job({"year": 1955}, question="x")
    completed = vedastro_gateway.complete_gateway_job(
        job["job_id"],
        {
            "scope": "vedastro_gateway_run",
            "status": "ok",
            "official_raw_response": {
                "source": "vedastro_official",
                "payload": {"Status": "Pass"},
            },
        },
    )

    archive = completed["raw_response_archive"]
    assert archive["status"] == "official_raw_response_archived"
    assert archive["official_raw_response_available"] is True
    path = tmp_path / archive["official_raw_response_path"]
    assert path.exists()
    assert '"vedastro_official"' in path.read_text(encoding="utf-8")


def test_gateway_lists_official_raw_response_archives(monkeypatch, tmp_path):
    from scripts import vedastro_gateway

    monkeypatch.setenv("VEDASTRO_GATEWAY_QUEUE_DIR", str(tmp_path))
    empty = vedastro_gateway.list_official_raw_response_archives()
    assert empty["archive_count"] == 0

    job = vedastro_gateway.enqueue_gateway_job({"year": 1955}, question="x")
    vedastro_gateway.complete_gateway_job(
        job["job_id"],
        {"status": "ok", "official_raw_response": {"source": "vedastro_official"}},
    )
    manifest = vedastro_gateway.list_official_raw_response_archives()

    assert manifest["scope"] == "vedastro_official_raw_response_archive_manifest"
    assert manifest["archive_count"] == 1
    assert manifest["archives"][0]["job_id"] == job["job_id"]
    assert manifest["archives"][0]["official_raw_response_available"] is True


def test_gateway_run_job_executes_queued_request(monkeypatch, tmp_path):
    from scripts import vedastro_gateway

    monkeypatch.setenv("VEDASTRO_GATEWAY_QUEUE_DIR", str(tmp_path))
    job = vedastro_gateway.enqueue_gateway_job(
        {"year": 1955, "month": 2, "day": 24, "hour": 19, "minute": 15, "lat": 37.7749, "lon": -122.4194, "tz": 8},
        question="事业机会什么时候出现",
        themes=["career"],
        reference_date="2026-07-02",
    )
    seen = {}

    def fake_run(case, question="", themes=None, reference_date=""):
        seen.update({"case": case, "question": question, "themes": themes, "reference_date": reference_date})
        return {"scope": "vedastro_gateway_run", "status": "local_fallback"}

    monkeypatch.setattr(vedastro_gateway, "run_gateway_packet", fake_run)
    result = vedastro_gateway.run_gateway_job(job["job_id"])

    assert result["status"] == "completed"
    assert result["result"]["status"] == "local_fallback"
    assert seen["case"]["year"] == 1955
    assert seen["question"] == "事业机会什么时候出现"
    assert seen["themes"] == ["career"]
    assert seen["reference_date"] == "2026-07-02"


def test_gateway_run_job_records_worker_failure(monkeypatch, tmp_path):
    from scripts import vedastro_gateway

    monkeypatch.setenv("VEDASTRO_GATEWAY_QUEUE_DIR", str(tmp_path))
    job = vedastro_gateway.enqueue_gateway_job({"year": 1955}, question="x")

    def broken_run(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(vedastro_gateway, "run_gateway_packet", broken_run)
    result = vedastro_gateway.run_gateway_job(job["job_id"])

    assert result["status"] == "failed"
    assert result["error"] == {"type": "RuntimeError", "message": "boom"}
