#!/usr/bin/env python3
"""China-friendly VedAstro-compatible gateway orchestration."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any


BACKEND_PRIORITY = ["self_host", "official", "cache", "queue", "local_fallback"]
BOUNDARY_TEXT = "Users never call VedAstro directly; backend gateway owns cache, queue, and fallback."
ROOT = Path(__file__).resolve().parents[1]


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


def _queue_dir() -> Path:
    raw = os.environ.get("VEDASTRO_GATEWAY_QUEUE_DIR", "").strip()
    return Path(raw).expanduser() if raw else ROOT / "scratch" / "local" / "vedastro_gateway_jobs"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_path(job_id: str) -> Path:
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    if not job_id or any(ch not in allowed for ch in job_id):
        raise ValueError("invalid VedAstro gateway job id")
    return _queue_dir() / f"{job_id}.json"


def _write_job(job: dict[str, Any]) -> dict[str, Any]:
    path = _job_path(str(job["job_id"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(job, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return job


def enqueue_gateway_job(
    case: dict[str, Any],
    question: str = "",
    themes: list[str] | tuple[str, ...] | None = None,
    reference_date: str = "",
) -> dict[str, Any]:
    created_at = _now_iso()
    request = {
        "case": dict(case or {}),
        "question": question or "",
        "themes": list(themes or []),
        "reference_date": reference_date or "",
    }
    digest = hashlib.sha256(
        json.dumps({"created_at": created_at, "request": request}, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:20]
    job_id = f"vgw_{digest}"
    return _write_job(
        {
            "scope": "vedastro_gateway_job",
            "schema_version": 1,
            "job_id": job_id,
            "status": "queued",
            "created_at": created_at,
            "updated_at": created_at,
            "poll_path": f"/api/vedastro_gateway/jobs/{job_id}",
            "request": request,
            "result": None,
            "raw_response_archive": {
                "status": "pending",
                "official_raw_response_available": False,
                "boundary": "Queued jobs do not prove VedAstro official raw response availability.",
            },
        }
    )


def get_gateway_job(job_id: str) -> dict[str, Any] | None:
    try:
        path = _job_path(job_id)
    except ValueError:
        return None
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def complete_gateway_job(job_id: str, result: dict[str, Any]) -> dict[str, Any]:
    job = get_gateway_job(job_id)
    if job is None:
        raise FileNotFoundError(job_id)
    job["status"] = "completed"
    job["updated_at"] = _now_iso()
    job["result"] = dict(result or {})
    job["raw_response_archive"] = {
        "status": "stored_gateway_packet_not_official_raw",
        "official_raw_response_available": False,
        "boundary": "Gateway packet was archived; VedAstro official raw response is still separate evidence.",
    }
    return _write_job(job)


def run_gateway_job(job_id: str) -> dict[str, Any] | None:
    job = get_gateway_job(job_id)
    if job is None:
        return None
    if job.get("status") == "completed":
        return job
    job["status"] = "running"
    job["updated_at"] = _now_iso()
    _write_job(job)
    request = job.get("request") if isinstance(job.get("request"), dict) else {}
    try:
        result = run_gateway_packet(
            request.get("case") if isinstance(request.get("case"), dict) else {},
            question=str(request.get("question") or ""),
            themes=request.get("themes") if isinstance(request.get("themes"), list) else [],
            reference_date=str(request.get("reference_date") or ""),
        )
    except Exception as exc:
        job["status"] = "failed"
        job["updated_at"] = _now_iso()
        job["error"] = {"type": exc.__class__.__name__, "message": str(exc)}
        return _write_job(job)
    return complete_gateway_job(job_id, result)


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
