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
        run_range_scan_for_case,
    )
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from vedastro_service_adapter import VEDASTRO_CALCULATION_COVERAGE, run_range_scan_for_case


ROUTE_DOMAIN_MAP = {
    "relationship": ["marriage"],
    "marriage": ["marriage"],
    "career": ["career"],
    "finance": ["wealth"],
    "wealth": ["wealth"],
    "rectification": ["marriage", "career", "wealth"],
    "timing": ["career", "marriage", "wealth"],
    "general": ["career", "marriage", "wealth"],
    "overview": ["career", "marriage", "wealth"],
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
    domain_reports: dict[str, Any] = {}
    evidence_ledger: list[dict[str, Any]] = []
    top_events_by_domain: dict[str, Any] = {}
    domain_statuses: dict[str, Any] = {}
    domain_event_counts: dict[str, int] = {}
    available = False
    first_reason = None

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
        "evidence_ledger": evidence_ledger,
        "reason": None if status == "ok" else first_reason,
        "domain_reports": domain_reports,
        "source_metadata": {
            "auto_ingested_by": "VedAstroEvidenceOrchestrator",
            "strategy": "minimal_route_scoped_orchestration",
            "node_coverage": {
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
