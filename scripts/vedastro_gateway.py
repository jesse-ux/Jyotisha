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


def _official_raw_response(result: dict[str, Any]) -> Any:
    raw = result.get("official_raw_response")
    if raw:
        return raw
    raw = result.get("raw_response")
    if isinstance(raw, dict) and raw.get("source") == "vedastro_official":
        return raw
    return None


def _raw_response_archive(job_id: str, result: dict[str, Any]) -> dict[str, Any]:
    raw = _official_raw_response(result)
    if not raw:
        return {
            "status": "stored_gateway_packet_not_official_raw",
            "official_raw_response_available": False,
            "boundary": "Gateway packet was archived; VedAstro official raw response is still separate evidence.",
        }
    archive_rel = f"{job_id}.official_raw_response.json"
    archive_path = _queue_dir() / archive_rel
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "status": "official_raw_response_archived",
        "official_raw_response_available": True,
        "official_raw_response_path": archive_rel,
        "boundary": "VedAstro official raw response archived separately from the gateway summary packet.",
    }


def complete_gateway_job(job_id: str, result: dict[str, Any]) -> dict[str, Any]:
    job = get_gateway_job(job_id)
    if job is None:
        raise FileNotFoundError(job_id)
    job["status"] = "completed"
    job["updated_at"] = _now_iso()
    job["result"] = dict(result or {})
    job["raw_response_archive"] = _raw_response_archive(job_id, job["result"])
    return _write_job(job)


def list_official_raw_response_archives() -> dict[str, Any]:
    archives: list[dict[str, Any]] = []
    queue_dir = _queue_dir()
    if queue_dir.exists():
        for path in sorted(queue_dir.glob("*.json")):
            if path.name.endswith(".official_raw_response.json"):
                continue
            try:
                job = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            archive = job.get("raw_response_archive") if isinstance(job, dict) else {}
            if not isinstance(archive, dict) or not archive.get("official_raw_response_available"):
                continue
            archives.append(
                {
                    "job_id": job.get("job_id"),
                    "status": archive.get("status"),
                    "official_raw_response_available": True,
                    "official_raw_response_path": archive.get("official_raw_response_path"),
                }
            )
    return {
        "scope": "vedastro_official_raw_response_archive_manifest",
        "archive_count": len(archives),
        "archives": archives,
    }


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
    from scripts.diagnose_vedastro_mode import build_report as build_vedastro_mode_report

    readiness = build_vedastro_mode_report()
    config = build_gateway_config()
    return {
        "scope": "vedastro_gateway",
        "mode": config["mode"],
        "backend_priority": BACKEND_PRIORITY,
        "active_backend": _active_backend(config),
        "self_host_configured": config["self_host_endpoint_configured"],
        "official_configured": config["official_endpoint_configured"],
        "credential_configured": bool(os.environ.get("VEDASTRO_API_KEY", "").strip()),
        "cache_ttl_seconds": config["cache_ttl_seconds"],
        "queue_enabled": config["queue_enabled"],
        "fail_open_local": config["fail_open_local"],
        "official_readiness": {
            "official_ready": bool(readiness.get("official_ready")),
            "mode": readiness.get("mode"),
            "readiness_blockers": list(readiness.get("readiness_blockers") or []),
            "free_tier_possible_with_cache_queue": bool(readiness.get("free_tier_possible_with_cache_queue")),
            "official_closure_plan": readiness.get("official_closure_plan") or {},
        },
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


def _official_closure_state_from_report(gateway: dict[str, Any], report: dict[str, Any]) -> str:
    active_backend = gateway.get("active_backend") or "local_fallback"
    if active_backend == "local_fallback":
        return "local_fallback"
    if _official_raw_response_from_report(report):
        return "official_verified"
    return "official_blocked"


def _official_raw_response_from_report(report: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(report, dict):
        return {}
    raw = (
        report.get("official_raw_response")
        or report.get("raw_response")
        or report.get("vedastro_official_raw_response")
    )
    return raw if isinstance(raw, dict) else {}


def _official_closure_reason_from_report(gateway: dict[str, Any], report: dict[str, Any]) -> str:
    active_backend = gateway.get("active_backend") or "local_fallback"
    if active_backend == "local_fallback":
        return "local_fallback_backend"
    if _official_raw_response_from_report(report):
        return "official_raw_response_present"
    return "official_raw_response_missing"


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
    official_raw_response = _official_raw_response_from_report(report)
    return {
        "scope": "vedastro_gateway_run",
        "schema_version": 1,
        "status": _status_from_report(gateway, report),
        "official_closure_state": _official_closure_state_from_report(gateway, report),
        "official_closure_reason": _official_closure_reason_from_report(gateway, report),
        **({"official_raw_response": official_raw_response} if official_raw_response else {}),
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
