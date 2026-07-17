#!/usr/bin/env python3
"""User-level VedAstro + strict-workflow entrypoint for Codex sessions."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from scripts.diagnose_vedastro_mode import build_report as build_runtime_mode_report
    from scripts.local_env import load_local_env
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from diagnose_vedastro_mode import build_report as build_runtime_mode_report
    from local_env import load_local_env


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "vedastro_official_capability_runner.py"


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


def _themes(raw: str) -> list[str]:
    aliases = {
        "relationship": "marriage",
        "relationships": "marriage",
        "finance": "wealth",
        "money": "wealth",
        "事业": "career",
        "婚恋": "marriage",
        "婚姻": "marriage",
        "财富": "wealth",
        "健康": "health",
        "教育": "education",
        "房产": "property",
        "子女": "children",
        "迁移": "migration",
        "问卜": "prashna",
        "校时": "rectification",
        "应期": "timing",
    }
    values: list[str] = []
    for item in raw.replace("，", ",").split(","):
        key = aliases.get(item.strip().lower(), item.strip().lower())
        if key and key not in values:
            values.append(key)
    return values or ["career", "marriage", "wealth"]


def _primary_route(question: str, themes: list[str]) -> str:
    text = f"{question} {' '.join(themes)}".lower()
    route_aliases = [
        ("career", ("career", "job", "work", "profession", "事业", "工作", "职业", "项目")),
        ("relationship", ("marriage", "relationship", "spouse", "partner", "婚恋", "婚姻", "伴侣")),
        ("finance", ("wealth", "finance", "money", "income", "财富", "金钱", "收入")),
    ]
    for route, tokens in route_aliases:
        if any(token in text for token in tokens):
            return route
    return "general"


def _case_from_args(args: argparse.Namespace, themes: list[str]) -> dict[str, Any]:
    return {
        "year": args.year,
        "month": args.month,
        "day": args.day,
        "hour": args.hour,
        "minute": args.minute,
        "second": args.second,
        "lat": args.lat,
        "lon": args.lon,
        "tz": args.tz,
        "reference_date": args.reference_date,
        "themes": themes,
        "ayanamsa_policy": args.ayanamsa,
        "node_policy": args.node_mode,
    }


def _run_capability_catalog(case: dict[str, Any]) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--bundle",
                "official_full_capability_catalog",
                "--birth-json",
                json.dumps(case, ensure_ascii=False),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=max(5.0, float(os.environ.get("VEDASTRO_TIMEOUT_SECONDS", "20") or 20)),
            check=False,
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "status": "official_full_capability_catalog_timeout",
            "summary": {},
            "domain_routing": {},
            "sample_outputs": {},
        }
    if completed.returncode != 0:
        return {
            "available": False,
            "status": "official_full_capability_catalog_runtime_error",
            "summary": {},
            "domain_routing": {},
            "dynamic_selection": {},
            "stderr": (completed.stderr or "").strip(),
        }
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {
            "available": False,
            "status": "official_full_capability_catalog_invalid_json",
            "summary": {},
            "domain_routing": {},
            "dynamic_selection": {},
            "stdout_excerpt": (completed.stdout or "").strip()[:500],
        }


def _official_raw_requested(args: argparse.Namespace) -> bool:
    return (
        bool(getattr(args, "require_official_raw_response", False))
        or _bool_env("VEDASTRO_REQUIRE_OFFICIAL_RAW_RESPONSE")
        or _bool_env("VEDASTRO_GATEWAY_REQUIRE_OFFICIAL_RAW_RESPONSE")
    )


def _run_official_full_snapshot(case: dict[str, Any]) -> dict[str, Any]:
    stub = os.environ.get("VEDASTRO_OFFICIAL_FULL_SNAPSHOT_STUB", "").strip()
    if stub:
        try:
            parsed = json.loads(stub)
        except json.JSONDecodeError as exc:
            return {
                "available": False,
                "status": "official_full_snapshot_stub_invalid_json",
                "error": {"type": type(exc).__name__, "message": str(exc)},
            }
        return parsed if isinstance(parsed, dict) else {"available": False, "status": "official_full_snapshot_stub_not_object"}

    try:
        from scripts.vedastro_service_adapter import run_official_full_snapshot_for_case
    except ModuleNotFoundError:  # pragma: no cover - direct script execution
        from vedastro_service_adapter import run_official_full_snapshot_for_case

    try:
        result = run_official_full_snapshot_for_case(case, case_id="user_chart")
    except Exception as exc:  # pragma: no cover - runtime boundary
        return {
            "available": False,
            "status": "official_full_snapshot_runtime_error",
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }
    return result if isinstance(result, dict) else {"available": False, "status": "official_full_snapshot_invalid_result"}


def _extract_official_raw_response(snapshot: dict[str, Any]) -> dict[str, Any]:
    raw = (
        snapshot.get("official_raw_response")
        or snapshot.get("raw_response")
        or snapshot.get("vedastro_official_raw_response")
    )
    return raw if isinstance(raw, dict) else {}


def _snapshot_summary(snapshot: dict[str, Any], raw_response: dict[str, Any]) -> dict[str, Any]:
    metadata = snapshot.get("source_metadata") if isinstance(snapshot.get("source_metadata"), dict) else {}
    return {
        "status": snapshot.get("status") or "not_requested",
        "available": bool(snapshot.get("available")) or bool(raw_response),
        "operation": snapshot.get("operation") or "official_full_snapshot",
        "raw_response_available": bool(raw_response),
        "artifact_path": metadata.get("artifact_path"),
        "reason": snapshot.get("reason"),
        "error": snapshot.get("error") if isinstance(snapshot.get("error"), dict) else {},
        "boundary": "official_raw_response must be present before claiming VedAstro official cloud closure.",
    }


def _strict_workflow_summary(route: str, catalog: dict[str, Any]) -> dict[str, Any]:
    dynamic_selection = catalog.get("dynamic_selection") if isinstance(catalog.get("dynamic_selection"), dict) else {}
    theme_for_route = {"relationship": "marriage", "finance": "wealth"}.get(route, route)
    return {
        "triggered": route in {"career", "relationship", "finance"},
        "primary_route": route,
        "routes_available": ["career", "relationship", "finance"],
        "source": "strict_workflow_contract_summary",
        "official_capability_selection": dynamic_selection.get(theme_for_route) or {},
        "boundary": (
            "This entrypoint triggers the strict workflow contract lane and passes VedAstro official catalog "
            "selection metadata; it does not claim every official method was executed."
        ),
    }


def _cache_and_queue_report() -> dict[str, Any]:
    queue_enabled = (
        _bool_env("VEDASTRO_FREE_TIER_QUEUE")
        or _bool_env("VEDASTRO_FREE_TIER_QUEUE_ENABLED")
        or _bool_env("VEDASTRO_ENABLE_FREE_TIER_QUEUE")
    )
    using_free_tier = not bool(os.environ.get("VEDASTRO_API_KEY", "").strip())
    return {
        "official_full_snapshot_cache_scope": "official_full_snapshot_semantic_cache",
        "official_full_snapshot_cache_ttl_seconds": _int_env("VEDASTRO_OFFICIAL_FULL_SNAPSHOT_CACHE_TTL_SECONDS", 0),
        "range_scan_cache_scope": "vedastro_range_scan_request_cache",
        "range_scan_cache_ttl_seconds": _int_env("VEDASTRO_CACHE_TTL_SECONDS", 0),
        "free_tier_queue_enabled": queue_enabled,
        "free_tier_strategy": {
            "using_free_tier": using_free_tier,
            "queue_enabled": queue_enabled,
            "guard_status": "within_free_tier_strategy" if using_free_tier else "premium_key_present",
        },
        "sample_limit": _int_env("VEDASTRO_FULL_CATALOG_SAMPLE_LIMIT", 0),
        "artifact_root": "scratch/local/vedastro_adapter",
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    load_local_env(ROOT)
    themes = _themes(args.themes)
    case = _case_from_args(args, themes)
    runtime = build_runtime_mode_report()
    catalog = _run_capability_catalog(case)
    snapshot = _run_official_full_snapshot(case) if _official_raw_requested(args) else {"status": "not_requested"}
    raw_response = _extract_official_raw_response(snapshot)
    route = _primary_route(args.question, themes)
    report = {
        "scope": "vedastro_user_entrypoint",
        "schema_version": 1,
        "input": {
            "question": args.question,
            "themes": themes,
            "birth": {key: case[key] for key in ("year", "month", "day", "hour", "minute", "second", "lat", "lon", "tz")},
            "reference_date": args.reference_date,
        },
        "runtime_mode": runtime,
        "vedastro_official_full_snapshot": _snapshot_summary(snapshot, raw_response),
        "official_capability_catalog": {
            "status": catalog.get("status") or "blocked",
            "available": bool(catalog.get("available")),
            "summary": catalog.get("summary") or {},
            "coverage": catalog.get("coverage") or {},
            "domain_routing": catalog.get("domain_routing") or {},
            "dynamic_selection": catalog.get("dynamic_selection") or {},
        },
        "cache_and_queue": _cache_and_queue_report(),
        "strict_workflow": _strict_workflow_summary(route, catalog),
        "honesty_boundary": {
            "all_641_methods_executed": False,
            "official_catalog_classified": bool(catalog.get("summary")),
            "official_extended_ready": bool(runtime.get("official_ready")),
            "rule": (
                "Use official catalog domain routing and dynamic selection as evidence metadata. "
                "Methods requiring user context/text/rectification remain blocked or secondary until inputs exist."
            ),
        },
        "user_commands": {
            "json": (
                "python3 scripts/vedastro_user_entrypoint.py --year YYYY --month MM --day DD "
                "--hour HH --minute MM --lat LAT --lon LON --tz TZ --question '...' "
                "--themes career,marriage,wealth --reference-date YYYY-MM-DD "
                "--require-official-raw-response --format json "
                "# includes official_full_capability_catalog and official_raw_response when verified"
            ),
            "markdown": (
                "python3 scripts/vedastro_user_entrypoint.py --year YYYY --month MM --day DD "
                "--hour HH --minute MM --lat LAT --lon LON --tz TZ --question '...' --format markdown"
            ),
        },
    }
    if raw_response:
        report["official_raw_response"] = raw_response
    return report


def render_markdown(report: dict[str, Any]) -> str:
    runtime = report["runtime_mode"]
    snapshot = report.get("vedastro_official_full_snapshot") or {}
    catalog = report["official_capability_catalog"]
    cache = report["cache_and_queue"]
    strict = report["strict_workflow"]
    summary = catalog.get("summary") or {}
    lines = [
        "# VedAstro 用户级入口",
        "",
        f"- runtime_mode: `{runtime.get('mode')}`",
        f"- official_full_snapshot: `{snapshot.get('status')}`",
        f"- official_raw_response_available: `{str(bool(snapshot.get('raw_response_available'))).lower()}`",
        f"- official_ready: `{str(runtime.get('official_ready')).lower()}`",
        f"- catalog_status: `{catalog.get('status')}`",
        f"- catalog_method_count: `{summary.get('catalog_method_count', 0)}`",
        f"- unknown_method_count: `{summary.get('unknown_method_count', 0)}`",
        f"- misrouted_general_method_count: `{summary.get('misrouted_general_method_count', 0)}`",
        f"- strict workflow triggered: `{str(strict.get('triggered')).lower()}`",
        f"- primary_route: `{strict.get('primary_route')}`",
        "",
        "## Cache / Free-Tier Queue",
        "",
        f"- official_full_snapshot_cache_ttl_seconds: `{cache['official_full_snapshot_cache_ttl_seconds']}`",
        f"- range_scan_cache_ttl_seconds: `{cache['range_scan_cache_ttl_seconds']}`",
        f"- free_tier_queue_enabled: `{str(cache['free_tier_queue_enabled']).lower()}`",
        "",
        "## Boundary",
        "",
        "- 这个入口会启动 VedAstro official capability catalog 分类、动态主题选择和 strict workflow 合同摘要。",
        "- 它不会把 641 项全部当作已执行；需要用户上下文、文本问题或校时画像的方法会保持 blocked/secondary。",
        "- 如果 runtime 是 `fast_local_fallback`，解盘必须诚实降级，不得声称 official extended 已闭环。",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)
    parser.add_argument("--day", type=int, required=True)
    parser.add_argument("--hour", type=int, required=True)
    parser.add_argument("--minute", type=int, required=True)
    parser.add_argument("--second", type=int, default=0)
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--tz", type=float, required=True)
    parser.add_argument("--question", default="")
    parser.add_argument("--themes", default="career,marriage,wealth")
    parser.add_argument("--reference-date", required=True)
    parser.add_argument("--ayanamsa", default="lahiri")
    parser.add_argument("--node-mode", default="mean")
    parser.add_argument("--require-official-raw-response", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    report = build_report(args)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
