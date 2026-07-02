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
