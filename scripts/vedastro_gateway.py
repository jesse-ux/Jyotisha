#!/usr/bin/env python3
"""China-friendly VedAstro-compatible gateway orchestration."""

from __future__ import annotations

import os
from types import SimpleNamespace
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


def _entrypoint_args(
    case: dict[str, Any],
    question: str,
    themes: list[str] | tuple[str, ...] | None,
    reference_date: str,
) -> SimpleNamespace:
    return SimpleNamespace(
        year=int(case.get("year", 0)),
        month=int(case.get("month", 0)),
        day=int(case.get("day", 0)),
        hour=int(case.get("hour", 0)),
        minute=int(case.get("minute", 0)),
        second=int(case.get("second", 0)),
        lat=float(case.get("lat", 0.0)),
        lon=float(case.get("lon", 0.0)),
        tz=float(case.get("tz", 0.0)),
        question=question or "",
        themes=",".join(str(item) for item in (themes or []) if str(item).strip()) or "career,marriage,wealth",
        reference_date=reference_date,
        ayanamsa=str(case.get("ayanamsa_policy") or case.get("ayanamsa") or "lahiri"),
        node_mode=str(case.get("node_policy") or case.get("node_mode") or "mean"),
    )


def _status_from_report(gateway: dict[str, Any], report: dict[str, Any]) -> str:
    catalog = report.get("official_capability_catalog") if isinstance(report, dict) else {}
    catalog_status = str((catalog or {}).get("status") or "").lower()
    active_backend = gateway.get("active_backend") or "local_fallback"
    if active_backend == "queue":
        return "queued"
    if active_backend == "cache":
        return "cached"
    if active_backend == "local_fallback":
        return "local_fallback"
    if (catalog or {}).get("available"):
        return "ok"
    if "budget" in catalog_status or "queue" in catalog_status:
        return "queued"
    if catalog_status:
        return "partial"
    return "blocked"


def run_gateway_packet(
    case: dict[str, Any],
    question: str = "",
    themes: list[str] | tuple[str, ...] | None = None,
    reference_date: str = "",
) -> dict[str, Any]:
    from scripts.vedastro_user_entrypoint import build_report

    gateway = gateway_status()
    args = _entrypoint_args(case, question, themes, reference_date)
    report = build_report(args)
    catalog = report.get("official_capability_catalog") or {}
    return {
        "scope": "vedastro_gateway_run",
        "schema_version": 1,
        "status": _status_from_report(gateway, report),
        "gateway_status": gateway,
        "input": report.get("input") or {},
        "runtime_mode": report.get("runtime_mode") or {},
        "official_capability_catalog": {
            "status": catalog.get("status") or "blocked",
            "available": bool(catalog.get("available")),
            "summary": catalog.get("summary") or {"catalog_method_count": 0},
            "coverage": catalog.get("coverage") or {},
            "domain_routing": catalog.get("domain_routing") or {},
            "dynamic_selection": catalog.get("dynamic_selection") or {},
        },
        "cache_and_queue": report.get("cache_and_queue") or {},
        "strict_workflow": report.get("strict_workflow") or {},
        "honesty_boundary": {
            **(report.get("honesty_boundary") or {}),
            "all_641_methods_executed": False,
            "gateway_rule": (
                "Gateway may use self-hosted VedAstro, official VedAstro, cache, queue, or local fallback; "
                "it never implies all official methods ran for this question."
            ),
        },
        "user_visibility": {
            "mainland_cn_safe": True,
            "direct_browser_access_allowed": False,
            "frontend_secret_safe": True,
            "boundary": BOUNDARY_TEXT,
        },
    }
