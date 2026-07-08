from __future__ import annotations


def test_gateway_status_defaults_to_local_first_cn_safe(monkeypatch):
    from scripts import vedastro_gateway

    monkeypatch.delenv("VEDASTRO_GATEWAY_MODE", raising=False)
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
    assert packet["gateway_status"]["mode"] == "cn_gateway"
    assert packet["official_capability_catalog"]["summary"]["catalog_method_count"] >= 0
    assert packet["honesty_boundary"]["all_641_methods_executed"] is False
    assert packet["user_visibility"]["mainland_cn_safe"] is True


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
