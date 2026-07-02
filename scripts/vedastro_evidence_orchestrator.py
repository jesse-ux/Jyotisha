#!/usr/bin/env python3
"""Shared VedAstro evidence orchestration layer.

The orchestrator does not expose hundreds of VedAstro nodes to users. It picks
the smallest useful domain scan set for the current route and delegates the
actual external boundary to ``vedastro_service_adapter``.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

try:
    from scripts.vedastro_service_adapter import (
        VEDASTRO_CALCULATION_COVERAGE,
        run_official_full_snapshot_for_case,
        run_range_scan_for_case,
    )
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from vedastro_service_adapter import (
        VEDASTRO_CALCULATION_COVERAGE,
        run_official_full_snapshot_for_case,
        run_range_scan_for_case,
    )


ROUTE_DOMAIN_MAP = {
    "relationship": ["marriage"],
    "marriage": ["marriage"],
    "career": ["career"],
    "finance": ["wealth"],
    "wealth": ["wealth"],
    "health": ["health"],
    "education": ["education"],
    "property": ["property"],
    "children": ["children"],
    "migration": ["migration"],
    "prashna": ["prashna"],
    "rectification": ["marriage", "career", "wealth"],
    "timing": ["career", "marriage", "wealth"],
    "general": ["career", "marriage", "wealth"],
    "overview": ["career", "marriage", "wealth"],
}


ROUTE_THEME_REQUIREMENTS = {
    "relationship": {
        "route": "relationship",
        "requires_dual_dasha": True,
        "required_local_supplements": ["upapada_lagna", "darakaraka", "narayana_dasha", "functional_benefic_malefic"],
    },
    "marriage": {
        "route": "relationship",
        "requires_dual_dasha": True,
        "required_local_supplements": ["upapada_lagna", "darakaraka", "narayana_dasha", "functional_benefic_malefic"],
    },
    "career": {
        "route": "career",
        "requires_dual_dasha": True,
        "required_local_supplements": ["a10_karma_pada", "narayana_dasha", "functional_benefic_malefic"],
    },
    "finance": {
        "route": "finance",
        "requires_dual_dasha": True,
        "required_local_supplements": ["wealth_structure_explainer", "narayana_dasha", "functional_benefic_malefic"],
    },
    "wealth": {
        "route": "finance",
        "requires_dual_dasha": True,
        "required_local_supplements": ["wealth_structure_explainer", "narayana_dasha", "functional_benefic_malefic"],
    },
    "health": {
        "route": "health",
        "requires_dual_dasha": True,
        "required_local_supplements": ["d30_health_axis", "sixth_eighth_twelfth_houses", "functional_benefic_malefic"],
    },
    "education": {
        "route": "education",
        "requires_dual_dasha": True,
        "required_local_supplements": ["d24_learning_axis", "fifth_ninth_houses", "functional_benefic_malefic"],
    },
    "property": {
        "route": "property",
        "requires_dual_dasha": True,
        "required_local_supplements": ["d4_property_axis", "fourth_house", "functional_benefic_malefic"],
    },
    "children": {
        "route": "children",
        "requires_dual_dasha": True,
        "required_local_supplements": ["d7_children_axis", "fifth_house", "functional_benefic_malefic"],
    },
    "migration": {
        "route": "migration",
        "requires_dual_dasha": True,
        "required_local_supplements": ["d4_d9_foreign_axis", "ninth_twelfth_houses", "functional_benefic_malefic"],
    },
    "prashna": {
        "route": "prashna",
        "requires_dual_dasha": False,
        "required_local_supplements": ["prashna_chart", "question_context_required", "functional_benefic_malefic"],
    },
    "overview": {
        "route": "overview",
        "requires_dual_dasha": True,
        "required_local_supplements": [],
    },
    "general": {
        "route": "general",
        "requires_dual_dasha": True,
        "required_local_supplements": [],
    },
}


def _default_window(reference_date: str | None, days: int = 180) -> tuple[str, str]:
    raw = str(reference_date or datetime.utcnow().strftime("%Y-%m-%d"))[:10]
    try:
        start = datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return raw, raw
    return start.isoformat(), (start + timedelta(days=days)).isoformat()


def _normalize_case(birth_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "year": birth_payload.get("year"),
        "month": birth_payload.get("month"),
        "day": birth_payload.get("day"),
        "hour": birth_payload.get("hour"),
        "minute": birth_payload.get("minute"),
        "second": birth_payload.get("second", 0),
        "lat": birth_payload.get("lat"),
        "lon": birth_payload.get("lon"),
        "tz": birth_payload.get("tz"),
        "ayanamsa_policy": birth_payload.get("ayanamsa_policy")
        or birth_payload.get("ayanamsa")
        or "lahiri",
        "node_policy": birth_payload.get("node_policy")
        or birth_payload.get("node_mode")
        or birth_payload.get("nodeMode")
        or "mean",
    }


def orchestrate_vedastro_evidence(
    birth_payload: dict[str, Any],
    *,
    route: str = "general",
    reference_date: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    case_id: str = "vedastro_orchestrator",
) -> dict[str, Any]:
    domains = ROUTE_DOMAIN_MAP.get(route, ROUTE_DOMAIN_MAP["general"])
    window_start, window_end = (start_date, end_date) if start_date and end_date else _default_window(reference_date)
    case = _normalize_case(birth_payload)
    case["reference_date"] = str(reference_date or window_start)[:10]
    case["themes"] = list(domains)
    domain_reports: dict[str, Any] = {}
    evidence_ledger: list[dict[str, Any]] = []
    top_events_by_domain: dict[str, Any] = {}
    daily_windows_by_domain: dict[str, list[dict[str, Any]]] = {}
    top_daily_window_by_domain: dict[str, dict[str, Any]] = {}
    domain_statuses: dict[str, Any] = {}
    domain_event_counts: dict[str, int] = {}
    available = False
    first_reason = None
    official_full_snapshot = run_official_full_snapshot_for_case(
        case,
        case_id=f"{case_id}_official_full_snapshot",
    )
    official_metadata = official_full_snapshot.get("source_metadata") if isinstance(official_full_snapshot, dict) else {}
    if not isinstance(official_metadata, dict):
        official_metadata = {}
    full_catalog = official_metadata.get("official_full_capability_catalog")
    if not isinstance(full_catalog, dict):
        full_catalog = {}
    full_catalog_domain_routing = full_catalog.get("domain_routing") if isinstance(full_catalog.get("domain_routing"), dict) else {}
    full_catalog_dynamic_selection = full_catalog.get("dynamic_selection") if isinstance(full_catalog.get("dynamic_selection"), dict) else {}
    official_section_statuses = official_full_snapshot.get("section_statuses") if isinstance(official_full_snapshot, dict) else {}
    if not isinstance(official_section_statuses, dict):
        official_section_statuses = {}
    official_report_references = {
        theme: selection.get("report_reference")
        for theme, selection in full_catalog_dynamic_selection.items()
        if isinstance(selection, dict) and isinstance(selection.get("report_reference"), dict)
    }
    theme_requirements = ROUTE_THEME_REQUIREMENTS.get(route, ROUTE_THEME_REQUIREMENTS["general"]).copy()
    theme_requirements["domains"] = list(domains)

    for domain in domains:
        report = run_range_scan_for_case(
            case,
            domain,
            str(window_start),
            str(window_end),
            case_id=f"{case_id}_{domain}",
        )
        domain_reports[domain] = report
        domain_statuses[domain] = report.get("status")
        domain_event_counts[domain] = int(report.get("event_count", 0) or 0)
        available = available or bool(report.get("available"))
        first_reason = first_reason or report.get("reason")
        if isinstance(report.get("top_event"), dict):
            top_events_by_domain[domain] = report["top_event"]
        daily_windows = report.get("daily_windows")
        if isinstance(daily_windows, list):
            daily_windows_by_domain[domain] = daily_windows
        top_daily_window = report.get("top_daily_window")
        if isinstance(top_daily_window, dict):
            top_daily_window_by_domain[domain] = top_daily_window
        for event in report.get("evidence_ledger") or []:
            if isinstance(event, dict):
                evidence_ledger.append(event)

    status = "ok" if any(item == "ok" for item in domain_statuses.values()) else next(iter(domain_statuses.values()), "blocked")
    return {
        "backend": "vedastro_service_adapter_candidate",
        "available": available,
        "status": status,
        "operation": "range_scan",
        "domain": domains[0] if len(domains) == 1 else "overview",
        "route": route,
        "event_count": len(evidence_ledger),
        "top_event": next(iter(top_events_by_domain.values()), None),
        "top_events_by_domain": top_events_by_domain,
        "daily_windows_by_domain": daily_windows_by_domain,
        "top_daily_window_by_domain": top_daily_window_by_domain,
        "evidence_ledger": evidence_ledger,
        "reason": None if status == "ok" else first_reason,
        "official_full_snapshot": official_full_snapshot,
        "domain_reports": domain_reports,
        "source_metadata": {
            "auto_ingested_by": "VedAstroEvidenceOrchestrator",
            "strategy": "official_full_snapshot_first_then_route_scoped_range_scan",
            "official_python_path": (
                (official_full_snapshot.get("source_metadata") or {}).get("official_python_path")
                if isinstance(official_full_snapshot, dict)
                else None
            ),
            "official_python_bundle_status": (
                (official_metadata.get("official_python_bundle") or {}).get("status")
            ),
            "official_full_capability_catalog_status": full_catalog.get("status"),
            "official_full_capability_catalog_summary": full_catalog.get("summary") or {},
            "official_full_capability_domain_routing": full_catalog_domain_routing,
            "official_full_capability_dynamic_selection": full_catalog_dynamic_selection,
            "official_report_references": official_report_references,
            "official_section_statuses": official_section_statuses,
            "theme_requirements": theme_requirements,
            "node_coverage": {
                "official_full_snapshot_first": True,
                "official_full_capability_catalog_default": bool(full_catalog),
                "official_full_capability_theme_routing": bool(full_catalog_domain_routing),
                "official_full_capability_dynamic_selection": bool(full_catalog_dynamic_selection),
                "strategy": "domain_scoped_range_scan",
                "official_calculation_coverage": VEDASTRO_CALCULATION_COVERAGE,
                "selected_domains": domains,
                "not_user_exposed": True,
            },
            "route": route,
            "scan_window": {"start_date": str(window_start), "end_date": str(window_end)},
            "domain_statuses": domain_statuses,
            "domain_event_counts": domain_event_counts,
        },
    }
