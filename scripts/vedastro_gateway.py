#!/usr/bin/env python3
"""China-friendly VedAstro-compatible gateway orchestration."""

from __future__ import annotations

import os
from typing import Any


BACKEND_PRIORITY = ["self_host", "official", "cache", "queue", "local_fallback"]
BOUNDARY_TEXT = "Users never call VedAstro directly; backend gateway owns cache, queue, and fallback."


def _bool_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int = 0) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(float(raw))
    except ValueError:
        return default


def build_gateway_config() -> dict[str, Any]:
    mode = os.environ.get("VEDASTRO_GATEWAY_MODE", "local_first").strip() or "local_first"
    self_host = os.environ.get("VEDASTRO_SELF_HOST_ENDPOINT", "").strip()
    official = os.environ.get("VEDASTRO_API_ENDPOINT", "").strip()
    return {
        "mode": mode,
        "self_host_endpoint_configured": bool(self_host),
        "official_endpoint_configured": bool(official),
        "cache_ttl_seconds": _int_env("VEDASTRO_CACHE_TTL_SECONDS", 0),
        "queue_enabled": _bool_env("VEDASTRO_GATEWAY_QUEUE_ENABLED") or _bool_env("VEDASTRO_QUEUE_ENABLED"),
        "fail_open_local": os.environ.get("VEDASTRO_FAIL_OPEN_LOCAL", "1").strip().lower()
        not in {"0", "false", "no"},
    }


def _active_backend(config: dict[str, Any]) -> str:
    if config["self_host_endpoint_configured"]:
        return "self_host"
    if config["official_endpoint_configured"] and _bool_env("VEDASTRO_ENABLE_NETWORK"):
        return "official"
    if config["cache_ttl_seconds"] > 0:
        return "cache"
    if config["queue_enabled"]:
        return "queue"
    return "local_fallback"


def gateway_status() -> dict[str, Any]:
    config = build_gateway_config()
    return {
        "scope": "vedastro_gateway",
        "mode": config["mode"],
        "backend_priority": BACKEND_PRIORITY,
        "active_backend": _active_backend(config),
        "self_host_configured": config["self_host_endpoint_configured"],
        "official_configured": config["official_endpoint_configured"],
        "cache_ttl_seconds": config["cache_ttl_seconds"],
        "queue_enabled": config["queue_enabled"],
        "fail_open_local": config["fail_open_local"],
        "direct_browser_access_allowed": False,
        "frontend_secret_safe": True,
        "boundary": BOUNDARY_TEXT,
    }
