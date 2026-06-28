#!/usr/bin/env python3
"""Minimal VedAstro service-boundary adapter skeleton.

This module does not replace the local SwissEph path. It only defines the
request/response schema and a controlled "not configured" status so the
workspace can evolve from research notes to an executable adapter contract.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
from pathlib import Path
from typing import Any
from urllib import request, error


ROOT = Path(__file__).resolve().parents[1]


PARITY_CASES = {
    "beijing_first_use_demo": {
        "year": 1990,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "lat": 39.9042,
        "lon": 116.4074,
        "tz": 8.0,
        "ayanamsa_policy": "lahiri",
        "node_policy": "mean",
    },
    "delhi_lagna_boundary": {
        "year": 1984,
        "month": 10,
        "day": 31,
        "hour": 6,
        "minute": 30,
        "lat": 28.6139,
        "lon": 77.2090,
        "tz": 5.5,
        "ayanamsa_policy": "lahiri",
        "node_policy": "mean",
    },
    "new_york_moon_boundary": {
        "year": 2001,
        "month": 9,
        "day": 11,
        "hour": 8,
        "minute": 46,
        "lat": 40.7128,
        "lon": -74.0060,
        "tz": -4.0,
        "ayanamsa_policy": "lahiri",
        "node_policy": "mean",
    },
}

SUPPORTED_RANGE_SCAN_DOMAINS = {"marriage", "wealth", "career"}
RANGE_SCAN_EVENT_ALLOWLIST = {
    "marriage": {
        "event_ids": {
            "GocharJupiterIn7th",
            "GocharJupiterAspect7th",
            "GocharSaturnAspect7th",
            "JupiterSupportsMarriageAxis",
        },
        "tags": {"marriage", "relationship", "spouse", "transit"},
    },
    "wealth": {
        "event_ids": {
            "GocharJupiterIn2nd",
            "GocharJupiterIn11th",
            "GocharJupiterAspect2nd",
            "GocharJupiterAspect11th",
            "WealthExpansionWindow",
        },
        "tags": {"wealth", "finance", "income", "gains", "transit"},
    },
    "career": {
        "event_ids": {
            "GocharJupiterIn10th",
            "GocharSaturnIn10th",
            "GocharJupiterAspect10th",
            "CareerExpansionWindow",
        },
        "tags": {"career", "profession", "work", "transit"},
    },
}
RANGE_SCAN_SIGNAL_METADATA = {
    "marriage": {
        "GocharJupiterIn7th": {
            "signal_key": "gochar_jupiter_7th_marriage",
            "signal_label": "Jupiter in 7th marriage window",
            "signal_family": "marriage_trigger",
        },
        "GocharJupiterAspect7th": {
            "signal_key": "gochar_jupiter_aspect_7th_marriage",
            "signal_label": "Jupiter aspecting 7th marriage window",
            "signal_family": "marriage_trigger",
        },
        "GocharSaturnAspect7th": {
            "signal_key": "gochar_saturn_aspect_7th_relationship_pressure",
            "signal_label": "Saturn aspecting 7th relationship window",
            "signal_family": "relationship_pressure",
        },
        "JupiterSupportsMarriageAxis": {
            "signal_key": "jupiter_supports_marriage_axis",
            "signal_label": "Jupiter supports marriage axis",
            "signal_family": "marriage_trigger",
        },
    },
    "wealth": {
        "GocharJupiterIn2nd": {
            "signal_key": "gochar_jupiter_2nd_wealth",
            "signal_label": "Jupiter in 2nd wealth window",
            "signal_family": "wealth_trigger",
        },
        "GocharJupiterIn11th": {
            "signal_key": "gochar_jupiter_11th_gains",
            "signal_label": "Jupiter in 11th gains window",
            "signal_family": "gains_trigger",
        },
        "GocharJupiterAspect2nd": {
            "signal_key": "gochar_jupiter_aspect_2nd_wealth",
            "signal_label": "Jupiter aspecting 2nd wealth window",
            "signal_family": "wealth_trigger",
        },
        "GocharJupiterAspect11th": {
            "signal_key": "gochar_jupiter_aspect_11th_gains",
            "signal_label": "Jupiter aspecting 11th gains window",
            "signal_family": "gains_trigger",
        },
        "WealthExpansionWindow": {
            "signal_key": "wealth_expansion_window",
            "signal_label": "Wealth expansion window",
            "signal_family": "wealth_trigger",
        },
    },
    "career": {
        "GocharJupiterIn10th": {
            "signal_key": "gochar_jupiter_10th_career",
            "signal_label": "Jupiter in 10th career window",
            "signal_family": "career_trigger",
        },
        "GocharSaturnIn10th": {
            "signal_key": "gochar_saturn_10th_career",
            "signal_label": "Saturn in 10th career window",
            "signal_family": "career_pressure",
        },
        "GocharJupiterAspect10th": {
            "signal_key": "gochar_jupiter_aspect_10th_career",
            "signal_label": "Jupiter aspecting 10th career window",
            "signal_family": "career_trigger",
        },
        "CareerExpansionWindow": {
            "signal_key": "career_expansion_window",
            "signal_label": "Career expansion window",
            "signal_family": "career_trigger",
        },
    },
}
DEFAULT_TIMEOUT_SECONDS = 8
TIMEOUT_ENV = "VEDASTRO_TIMEOUT_SECONDS"
RETRY_POLICY = {
    "max_attempts": 2,
    "backoff_seconds": 1,
    "retry_on": ["timeout", "429", "502", "503", "504"],
}
ALLOW_NETWORK_ENV = "VEDASTRO_ENABLE_NETWORK"


def _timeout_seconds() -> float:
    raw = os.environ.get(TIMEOUT_ENV, "").strip()
    if not raw:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        return float(raw)
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS


def schema() -> dict[str, Any]:
    request_example = {
        **PARITY_CASES["beijing_first_use_demo"],
        "body_list": ["Sun", "Moon", "Ascendant", "Rahu", "Ketu"],
    }
    range_scan_allowlist = {
        domain: {
            "event_ids": sorted(values["event_ids"]),
            "tags": sorted(values["tags"]),
        }
        for domain, values in sorted(RANGE_SCAN_EVENT_ALLOWLIST.items())
    }
    return {
        "adapter": "vedastro_service_adapter",
        "backend": "vedastro_service_adapter_candidate",
        "transport": "http_json_service_boundary",
        "default_timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
        "retry_policy": RETRY_POLICY,
        "required_env": {
            "endpoint": "VEDASTRO_API_ENDPOINT",
            "api_key_optional": "VEDASTRO_API_KEY",
        },
        "request_contract": [
            "year",
            "month",
            "day",
            "hour",
            "minute",
            "lat",
            "lon",
            "tz",
            "ayanamsa_policy",
            "node_policy",
            "body_list",
        ],
        "response_contract": [
            "backend",
            "available",
            "status",
            "ayanamsa_value",
            "node_policy",
            "body_list",
            "bodies",
            "source_metadata",
        ],
        "range_scan_request_contract": [
            "operation",
            "domain",
            "start_date",
            "end_date",
            "year",
            "month",
            "day",
            "hour",
            "minute",
            "lat",
            "lon",
            "tz",
            "ayanamsa_policy",
            "node_policy",
            "event_model",
        ],
        "range_scan_response_contract": [
            "backend",
            "available",
            "status",
            "operation",
            "domain",
            "evidence_ledger",
            "source_metadata",
        ],
        "range_scan_event_allowlist": range_scan_allowlist,
        "request_example": request_example,
        "provenance_contract": {
            "external_service": True,
            "required_fields": [
                "endpoint",
                "transport",
                "provenance_mode",
                "retry_policy",
                "timeout_seconds",
            ],
        },
    }


def _unconfigured(reason: str) -> dict[str, Any]:
    return {
        "backend": "vedastro_service_adapter_candidate",
        "available": False,
        "status": "service_endpoint_not_configured",
        "reason": reason,
        "source_metadata": {
            "transport": "http_json_service_boundary",
            "endpoint_env": "VEDASTRO_API_ENDPOINT",
            "api_key_env": "VEDASTRO_API_KEY",
            "provenance_mode": "external_service_candidate",
            "timeout_seconds": _timeout_seconds(),
            "retry_policy": RETRY_POLICY,
        },
    }


def _request_preview(case: dict[str, Any]) -> dict[str, Any]:
    return {
        **case,
        "body_list": ["Sun", "Moon", "Ascendant", "Rahu", "Ketu"],
    }


def _range_scan_preview(case: dict[str, Any], domain: str, start_date: str, end_date: str) -> dict[str, Any]:
    return {
        "operation": "range_scan",
        "domain": domain,
        "start_date": start_date,
        "end_date": end_date,
        "event_model": "vedastro_events_at_range_candidate",
        **case,
    }


def _normalize_success(payload: dict[str, Any], endpoint: str) -> dict[str, Any]:
    return {
        "backend": "vedastro_service_adapter_candidate",
        "available": True,
        "status": "ok",
        "ayanamsa_value": payload.get("ayanamsa_value"),
        "node_policy": payload.get("node_policy"),
        "body_list": payload.get("body_list"),
        "bodies": payload.get("bodies"),
        "source_metadata": {
            "transport": "http_json_service_boundary",
            "endpoint": endpoint,
            "provenance_mode": "external_service_candidate",
            "timeout_seconds": _timeout_seconds(),
            "retry_policy": RETRY_POLICY,
            **(payload.get("source_metadata") or {}),
        },
    }


def _normalize_range_scan_success(
    payload: dict[str, Any],
    endpoint: str,
    request_preview: dict[str, Any],
) -> dict[str, Any]:
    events = payload.get("events")
    if not isinstance(events, list):
        events = []

    domain = request_preview["domain"]
    allowlist = RANGE_SCAN_EVENT_ALLOWLIST.get(domain, {})
    allowed_ids = allowlist.get("event_ids", set())
    allowed_tags = allowlist.get("tags", set())

    evidence_ledger = []
    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            continue
        event_id = event.get("id") or event.get("name") or f"event_{index}"
        tags = event.get("tags") or []
        if not isinstance(tags, list):
            tags = []
        tag_set = {str(tag) for tag in tags}
        if event_id not in allowed_ids and tag_set.isdisjoint(allowed_tags):
            continue
        signal_metadata = RANGE_SCAN_SIGNAL_METADATA.get(domain, {}).get(event_id, {})
        evidence_ledger.append(
            {
                "source": "vedastro_service_adapter_candidate",
                "operation": "range_scan",
                "domain": domain,
                "event_id": event_id,
                "signal_key": signal_metadata.get("signal_key"),
                "signal_label": signal_metadata.get("signal_label") or event.get("name") or event_id,
                "signal_family": signal_metadata.get("signal_family"),
                "start": event.get("start") or event.get("start_time") or event.get("start_date"),
                "end": event.get("end") or event.get("end_time") or event.get("end_date"),
                "score": event.get("score") if event.get("score") is not None else event.get("strength"),
                "tags": tags,
                "raw": event,
            }
        )

    top_event = None
    if evidence_ledger:
        top = max(
            evidence_ledger,
            key=lambda item: item.get("score") if isinstance(item.get("score"), (int, float)) else float("-inf"),
        )
        top_event = {
            "event_id": top.get("event_id"),
            "signal_key": top.get("signal_key"),
            "signal_label": top.get("signal_label"),
            "signal_family": top.get("signal_family"),
            "score": top.get("score"),
            "start": top.get("start"),
            "end": top.get("end"),
            "tags": top.get("tags") or [],
        }

    return {
        "backend": "vedastro_service_adapter_candidate",
        "available": True,
        "status": "ok",
        "operation": "range_scan",
        "domain": domain,
        "request_preview": request_preview,
        "event_count": len(evidence_ledger),
        "top_event": top_event,
        "evidence_ledger": evidence_ledger,
        "source_metadata": {
            "transport": "http_json_service_boundary",
            "endpoint": endpoint,
            "provenance_mode": "external_service_candidate",
            "timeout_seconds": _timeout_seconds(),
            "retry_policy": RETRY_POLICY,
            **(payload.get("source_metadata") or {}),
        },
    }


def _source_metadata(endpoint: str) -> dict[str, Any]:
    return {
        "transport": "http_json_service_boundary",
        "endpoint": endpoint,
        "provenance_mode": "external_service_candidate",
        "timeout_seconds": _timeout_seconds(),
        "retry_policy": RETRY_POLICY,
        "network_execution_env": ALLOW_NETWORK_ENV,
    }


def _post_json(endpoint: str, request_preview: dict[str, Any]) -> dict[str, Any] | str:
    req = request.Request(
        endpoint,
        data=json.dumps(request_preview).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=_timeout_seconds()) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


def run_case(case_id: str) -> dict[str, Any]:
    if case_id not in PARITY_CASES:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "unknown_case_id",
            "reason": f"Unknown parity case: {case_id}",
        }

    endpoint = os.environ.get("VEDASTRO_API_ENDPOINT", "").strip()
    if not endpoint:
        return _unconfigured("VEDASTRO_API_ENDPOINT is not configured; adapter skeleton stops before network access.")

    case = PARITY_CASES[case_id]
    request_preview = _request_preview(case)
    if os.environ.get(ALLOW_NETWORK_ENV, "").strip().lower() not in {"1", "true", "yes"}:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "network_execution_disabled",
            "reason": f"{ALLOW_NETWORK_ENV} is not enabled; adapter stops after building request/provenance metadata.",
            "request_preview": request_preview,
            "source_metadata": _source_metadata(endpoint),
        }
    try:
        payload = _post_json(endpoint, request_preview)
    except error.HTTPError as exc:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "http_error",
            "reason": f"VedAstro adapter HTTP error: {exc.code}",
            "request_preview": request_preview,
            "source_metadata": _source_metadata(endpoint),
        }
    except error.URLError as exc:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "network_error",
            "reason": f"VedAstro adapter network error: {exc.reason}",
            "request_preview": request_preview,
            "source_metadata": _source_metadata(endpoint),
        }
    except (TimeoutError, socket.timeout):
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "timeout",
            "reason": "VedAstro adapter timed out",
            "request_preview": request_preview,
            "source_metadata": _source_metadata(endpoint),
        }
    except json.JSONDecodeError:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "invalid_json",
            "reason": "VedAstro adapter received non-JSON response",
            "request_preview": request_preview,
            "source_metadata": _source_metadata(endpoint),
        }

    return _normalize_success(payload, endpoint)


def run_range_scan(case_id: str, domain: str, start_date: str, end_date: str) -> dict[str, Any]:
    if case_id not in PARITY_CASES:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "unknown_case_id",
            "reason": f"Unknown parity case: {case_id}",
        }
    if domain not in SUPPORTED_RANGE_SCAN_DOMAINS:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "unsupported_range_scan_domain",
            "reason": f"Unsupported range scan domain: {domain}",
        }

    endpoint = os.environ.get("VEDASTRO_API_ENDPOINT", "").strip()
    if not endpoint:
        return _unconfigured("VEDASTRO_API_ENDPOINT is not configured; range scan stops before network access.")

    request_preview = _range_scan_preview(PARITY_CASES[case_id], domain, start_date, end_date)
    if os.environ.get(ALLOW_NETWORK_ENV, "").strip().lower() not in {"1", "true", "yes"}:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "network_execution_disabled",
            "reason": f"{ALLOW_NETWORK_ENV} is not enabled; range scan stops after building request/provenance metadata.",
            "request_preview": request_preview,
            "source_metadata": _source_metadata(endpoint),
        }

    try:
        payload = _post_json(endpoint, request_preview)
    except error.HTTPError as exc:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "http_error",
            "reason": f"VedAstro range scan HTTP error: {exc.code}",
            "request_preview": request_preview,
            "source_metadata": _source_metadata(endpoint),
        }
    except error.URLError as exc:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "network_error",
            "reason": f"VedAstro range scan network error: {exc.reason}",
            "request_preview": request_preview,
            "source_metadata": _source_metadata(endpoint),
        }
    except (TimeoutError, socket.timeout):
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "timeout",
            "reason": "VedAstro range scan timed out",
            "request_preview": request_preview,
            "source_metadata": _source_metadata(endpoint),
        }
    except json.JSONDecodeError:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "invalid_json",
            "reason": "VedAstro range scan received non-JSON response",
            "request_preview": request_preview,
            "source_metadata": _source_metadata(endpoint),
        }

    return _normalize_range_scan_success(payload, endpoint, request_preview)


def main() -> int:
    parser = argparse.ArgumentParser(description="VedAstro service adapter skeleton")
    parser.add_argument("--print-schema", action="store_true")
    parser.add_argument("--case", default="beijing_first_use_demo")
    parser.add_argument("--range-scan", action="store_true")
    parser.add_argument("--domain", choices=sorted(SUPPORTED_RANGE_SCAN_DOMAINS), default="marriage")
    parser.add_argument("--start-date", default="2026-01-01")
    parser.add_argument("--end-date", default="2031-01-01")
    args = parser.parse_args()

    if args.print_schema:
        result = schema()
    elif args.range_scan:
        result = run_range_scan(args.case, args.domain, args.start_date, args.end_date)
    else:
        result = run_case(args.case)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
