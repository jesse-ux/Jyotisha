"""Shared VedAstro-first source priority helpers.

This module keeps the user-facing data order identical across the CLI engine,
API server, and MCP strict workflow:

1. VedAstro official full snapshot when it contains an official chart.
2. Local modules as supplemental evidence and cross-checks.
3. Local chart as fallback only when the official snapshot is blocked.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


SOURCE_PRIORITY = [
    "vedastro_official_snapshot",
    "local_supplemental_modules",
    "local_engine_fallback_when_official_blocked",
]


def official_chart_available(official_snapshot: dict[str, Any] | None) -> bool:
    if not isinstance(official_snapshot, dict):
        return False
    official_chart = official_snapshot.get("official_chart")
    if not isinstance(official_chart, dict):
        return False
    return (
        isinstance(official_chart.get("planets"), dict)
        and bool(official_chart.get("planets"))
        and isinstance(official_chart.get("ascendant"), dict)
        and bool(official_chart.get("ascendant"))
    )


def _local_chart_from(report: dict[str, Any], modules: dict[str, Any]) -> dict[str, Any]:
    chart = report.get("chart")
    if isinstance(chart, dict) and chart:
        return chart
    chart = modules.get("chart")
    return chart if isinstance(chart, dict) else {}


def _blocked_reason(official_snapshot: dict[str, Any] | None) -> str:
    status = "missing"
    if isinstance(official_snapshot, dict):
        status = str(official_snapshot.get("status") or "blocked")
    return f"VedAstro official snapshot blocked: {status}"


def build_source_priority_metadata(
    official_snapshot: dict[str, Any] | None,
    *,
    official_primary: bool,
) -> dict[str, Any]:
    status = official_snapshot.get("status") if isinstance(official_snapshot, dict) else "missing"
    return {
        "mode": "vedastro_official_primary" if official_primary else "local_fallback_official_blocked",
        "priority": list(SOURCE_PRIORITY),
        "official_snapshot_first": True,
        "official_snapshot_status": status or "blocked",
        "local_engine_role": (
            "supplemental_crosscheck_or_fallback"
            if official_primary
            else "fallback_only_because_official_blocked"
        ),
        "user_visible_policy": (
            "show_vedastro_verified_when_official_chart_available"
            if official_primary
            else "show_local_fallback_with_official_blocked_boundary"
        ),
    }


def apply_vedastro_source_priority(
    report: dict[str, Any],
    *,
    official_snapshot: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(report, dict):
        return report
    modules = report.setdefault("modules", {})
    if not isinstance(modules, dict):
        modules = {}
        report["modules"] = modules

    if isinstance(official_snapshot, dict):
        modules["vedastro_official_full_snapshot"] = official_snapshot

    local_chart = _local_chart_from(report, modules)

    if official_chart_available(official_snapshot):
        official_chart = official_snapshot.get("official_chart")  # type: ignore[union-attr]
        modules["local_engine_chart_fallback"] = deepcopy(local_chart)
        public_chart = {
            **deepcopy(local_chart),
            "source": "vedastro_official_primary",
            "primary_source": "vedastro_official",
            "fallback_source": "local_engine",
            "local_engine_role": "supplemental_crosscheck_or_fallback",
            "local_crosscheck_status": "pending",
            "source_priority": list(SOURCE_PRIORITY),
            "planets": official_chart.get("planets", {}),
            "ascendant": official_chart.get("ascendant", {}),
            "houses": official_chart.get("houses", {}),
            "birth_info": local_chart.get("birth_info", report.get("birth_info", report.get("birth", {}))),
            "official_coverage": official_chart.get("coverage", {}),
        }
        report["chart"] = public_chart
        modules["chart"] = public_chart
        for key in ("source", "primary_source", "fallback_source", "planets", "ascendant", "houses"):
            if key in public_chart:
                report[key] = public_chart[key]
        modules["source_priority"] = build_source_priority_metadata(
            official_snapshot,
            official_primary=True,
        )
        return report

    if local_chart:
        fallback_chart = {
            **deepcopy(local_chart),
            "source": "local_engine_fallback",
            "primary_source": "local_engine",
            "fallback_reason": _blocked_reason(official_snapshot),
            "local_engine_role": "fallback_only_because_official_blocked",
            "source_priority": list(SOURCE_PRIORITY),
        }
        report["chart"] = fallback_chart
        modules["chart"] = fallback_chart
        for key in ("source", "primary_source", "planets", "ascendant", "houses"):
            if key in fallback_chart:
                report[key] = fallback_chart[key]

    modules["source_priority"] = build_source_priority_metadata(
        official_snapshot,
        official_primary=False,
    )
    return report


def official_snapshot_evidence(modules: dict[str, Any]) -> dict[str, Any]:
    snapshot = modules.get("vedastro_official_full_snapshot") if isinstance(modules, dict) else {}
    source_priority = modules.get("source_priority") if isinstance(modules, dict) else {}
    if not isinstance(snapshot, dict) or not snapshot:
        return {
            "level": "blocked",
            "source": "vedastro_official",
            "status": "missing",
            "operation": "official_full_snapshot",
            "source_priority": source_priority if isinstance(source_priority, dict) else {},
            "reason": "VedAstro official full snapshot is not attached.",
        }
    level = "primary" if official_chart_available(snapshot) else "blocked"
    return {
        "level": level,
        "source": "vedastro_official",
        "status": snapshot.get("status") or "blocked",
        "available": bool(snapshot.get("available")),
        "operation": snapshot.get("operation") or "official_full_snapshot",
        "source_priority": source_priority if isinstance(source_priority, dict) else {},
        "section_statuses": snapshot.get("section_statuses") or {},
        "chart_available": official_chart_available(snapshot),
        "reason": snapshot.get("reason"),
    }
