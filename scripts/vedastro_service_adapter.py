#!/usr/bin/env python3
"""Minimal VedAstro service-boundary adapter skeleton.

This module does not replace the local SwissEph path. It only defines the
request/response schema and a controlled "not configured" status so the
workspace can evolve from research notes to an executable adapter contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import time
from pathlib import Path
from typing import Any
from urllib import request, error
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]


PARITY_CASES = {
    "user_REDACTED_YEAR_test": {
        "year": REDACTED_YEAR,
        "month": 4,
        "day": 17,
        "hour": 14,
        "minute": 49,
        "lat": 36.42,
        "lon": 114.2,
        "tz": 8.0,
        "ayanamsa_policy": "lahiri",
        "node_policy": "mean",
    },
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
SUPPORTED_EXTERNAL_TECHNIQUE_DOMAINS = {"marriage", "wealth", "career", "general"}
VEDASTRO_CALCULATION_COVERAGE = {
    "official_python_library_calculations": "596+",
    "official_api_builder_calculators": "600+",
    "official_events_builder_events": "400+",
    "official_events_builder_methods": ["SearchEvents", "GetEventTiming", "ListEventTypes"],
    "range_scan_role": "high_frequency_life_event_radar",
    "intended_use": "external_timing_evidence_for_strict_workflow",
}
EXTERNAL_TECHNIQUE_ROLE = "external_technique_evidence"
EXTERNAL_TECHNIQUE_OPERATION = "calculation_method"
EXTERNAL_TECHNIQUE_ADJUDICATOR_POLICY = {
    "role": EXTERNAL_TECHNIQUE_ROLE,
    "can_change_score": False,
    "can_set_dominant_label": False,
    "can_set_payout_label": False,
    "allowed_destinations": ["secondary_context", "technique_audit"],
}
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
DEFAULT_TIMEOUT_SECONDS = 120
TIMEOUT_ENV = "VEDASTRO_TIMEOUT_SECONDS"
BACKOFF_ENV = "VEDASTRO_RETRY_BACKOFF_SECONDS"
RETRY_POLICY = {
    "max_attempts": 2,
    "backoff_seconds": 1,
    "retry_on": ["timeout", "429", "502", "503", "504"],
}
ALLOW_NETWORK_ENV = "VEDASTRO_ENABLE_NETWORK"
ARTIFACT_DIR = ROOT / "scratch" / "local" / "vedastro_adapter"


def _timeout_seconds() -> float:
    raw = os.environ.get(TIMEOUT_ENV, "").strip()
    if not raw:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        return float(raw)
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS


def _backoff_seconds() -> float:
    raw = os.environ.get(BACKOFF_ENV, "").strip()
    if not raw:
        return float(RETRY_POLICY["backoff_seconds"])
    try:
        return max(0.0, float(raw))
    except ValueError:
        return float(RETRY_POLICY["backoff_seconds"])


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _hash_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_json_bytes(payload)).hexdigest()


def _utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _endpoint_host(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    return parsed.netloc or endpoint


def _artifact_path(operation: str, request_hash: str, response_hash: str) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{operation}-{request_hash[:12]}-{response_hash[:12]}.json"
    return ARTIFACT_DIR / filename


def _repo_relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _write_artifact(result: dict[str, Any]) -> str:
    metadata = result.get("source_metadata") or {}
    artifact = _artifact_path(
        str(metadata.get("operation") or result.get("operation") or "calculation"),
        str(metadata.get("request_hash") or "no-request-hash"),
        str(metadata.get("response_hash") or "no-response-hash"),
    )
    artifact.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return _repo_relative(artifact)


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
            "vedastro_event_method",
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
        "vedastro_calculation_coverage": VEDASTRO_CALCULATION_COVERAGE,
        "external_technique_request_contract": [
            "operation",
            "role",
            "domain",
            "method",
            "api_endpoint",
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
        ],
        "external_technique_response_contract": [
            "backend",
            "available",
            "status",
            "operation",
            "role",
            "domain",
            "evidence_ledger",
            "adjudicator_policy",
            "source_metadata",
        ],
        "external_technique_adjudicator_policy": EXTERNAL_TECHNIQUE_ADJUDICATOR_POLICY,
        "range_scan_event_allowlist": range_scan_allowlist,
        "request_example": request_example,
        "provenance_contract": {
            "external_service": True,
            "required_fields": [
                "endpoint",
                "endpoint_host",
                "transport",
                "provenance_mode",
                "retry_policy",
                "timeout_seconds",
                "request_hash",
                "response_hash",
                "called_at",
                "artifact_path",
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
        "vedastro_event_method": "SearchEvents",
        "domain": domain,
        "start_date": start_date,
        "end_date": end_date,
        "event_model": "vedastro_events_at_range_candidate",
        **case,
    }


def _external_technique_preview(
    case: dict[str, Any],
    domain: str,
    method: str,
    api_endpoint: str,
) -> dict[str, Any]:
    return {
        "operation": EXTERNAL_TECHNIQUE_OPERATION,
        "role": EXTERNAL_TECHNIQUE_ROLE,
        "domain": domain,
        "method": method,
        "api_endpoint": api_endpoint,
        **case,
    }


def _base_live_metadata(
    endpoint: str,
    request_preview: dict[str, Any],
    payload: dict[str, Any],
    operation: str,
    attempt_count: int = 1,
    retry_error_codes: list[int] | None = None,
) -> dict[str, Any]:
    return {
        "transport": "http_json_service_boundary",
        "endpoint": endpoint,
        "endpoint_host": _endpoint_host(endpoint),
        "method": "POST",
        "operation": operation,
        "provenance_mode": "external_service_candidate",
        "timeout_seconds": _timeout_seconds(),
        "retry_policy": {**RETRY_POLICY, "backoff_seconds": _backoff_seconds()},
        "network_execution_env": ALLOW_NETWORK_ENV,
        "called_at": _utc_timestamp(),
        "request_hash": _hash_payload(request_preview),
        "response_hash": _hash_payload(payload),
        "attempt_count": attempt_count,
        "retry_error_codes": retry_error_codes or [],
    }


def _normalize_success(
    payload: dict[str, Any],
    endpoint: str,
    request_preview: dict[str, Any],
    attempt_count: int = 1,
    retry_error_codes: list[int] | None = None,
) -> dict[str, Any]:
    metadata = {
        **_base_live_metadata(endpoint, request_preview, payload, "calculation", attempt_count, retry_error_codes),
        **(payload.get("source_metadata") or {}),
    }
    result = {
        "backend": "vedastro_service_adapter_candidate",
        "available": True,
        "status": "ok",
        "ayanamsa_value": payload.get("ayanamsa_value"),
        "node_policy": payload.get("node_policy"),
        "body_list": payload.get("body_list"),
        "bodies": payload.get("bodies"),
        "source_metadata": metadata,
    }
    result["source_metadata"]["artifact_path"] = _write_artifact(result)
    return result


def _normalize_external_technique_success(
    payload: dict[str, Any],
    endpoint: str,
    request_preview: dict[str, Any],
) -> dict[str, Any]:
    evidence = {
        "source": "vedastro_service_adapter_candidate",
        "operation": EXTERNAL_TECHNIQUE_OPERATION,
        "role": EXTERNAL_TECHNIQUE_ROLE,
        "domain": request_preview["domain"],
        "method": request_preview["method"],
        "api_endpoint": request_preview["api_endpoint"],
        "status": payload.get("status") or "ok",
        "summary": payload.get("summary"),
        "nature": payload.get("nature"),
        "tags": payload.get("tags") if isinstance(payload.get("tags"), list) else [],
        "raw": payload,
    }
    return {
        "backend": "vedastro_service_adapter_candidate",
        "available": True,
        "status": "ok",
        "operation": EXTERNAL_TECHNIQUE_OPERATION,
        "role": EXTERNAL_TECHNIQUE_ROLE,
        "domain": request_preview["domain"],
        "request_preview": request_preview,
        "evidence_ledger": [evidence],
        "adjudicator_policy": EXTERNAL_TECHNIQUE_ADJUDICATOR_POLICY,
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
    attempt_count: int = 1,
    retry_error_codes: list[int] | None = None,
) -> dict[str, Any]:
    # Handle actual VedAstro response format: {"Status": "Pass", "Payload": [...]}
    if payload.get("Status") == "Pass":
        events = payload.get("Payload", [])
    else:
        # Fallback to local stub format if not VedAstro format
        events = payload.get("events", [])
        
    if not isinstance(events, list):
        events = []

    domain = request_preview.get("domain", "")
    allowlist = RANGE_SCAN_EVENT_ALLOWLIST.get(domain, {})
    allowed_ids = allowlist.get("event_ids", set())
    allowed_tags = allowlist.get("tags", set())

    original_event_count = len(events)
    evidence_ledger = []
    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            continue
        # VedAstro uses "Name" for event id, and "EventTags" for tags
        event_id = event.get("Name") or event.get("id") or event.get("name") or f"event_{index}"
        tags = event.get("EventTags") or event.get("tags") or []
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
                "start": event.get("StartTime") or event.get("start") or event.get("start_time") or event.get("start_date"),
                "end": event.get("EndTime") or event.get("end") or event.get("end_time") or event.get("end_date"),
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

    metadata = {
        **_base_live_metadata(endpoint, request_preview, payload, "range_scan", attempt_count, retry_error_codes),
        "vedastro_event_method": request_preview.get("vedastro_event_method"),
        "allowlist_domain": domain,
        "allowlist_event_count": len(evidence_ledger),
        "filtered_event_count": len(evidence_ledger),
        "raw_event_count": original_event_count,
        **(payload.get("source_metadata") or {}),
    }
    result = {
        "backend": "vedastro_service_adapter_candidate",
        "available": True,
        "status": "ok",
        "operation": "range_scan",
        "domain": domain,
        "request_preview": request_preview,
        "event_count": len(evidence_ledger),
        "top_event": top_event,
        "evidence_ledger": evidence_ledger,
        "source_metadata": metadata,
    }
    result["source_metadata"]["artifact_path"] = _write_artifact(result)
    return result


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
    vedastro_payload = request_preview
    req = request.Request(
        endpoint,
        data=json.dumps(vedastro_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=_timeout_seconds()) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


def _retry_status_codes() -> set[int]:
    codes = set()
    for value in RETRY_POLICY.get("retry_on", []):
        try:
            codes.add(int(str(value)))
        except ValueError:
            continue
    return codes


def _post_json_with_retry(endpoint: str, request_preview: dict[str, Any]) -> tuple[dict[str, Any], int, list[int]]:
    retry_codes = _retry_status_codes()
    retry_error_codes: list[int] = []
    max_attempts = int(RETRY_POLICY["max_attempts"])
    for attempt in range(1, max_attempts + 1):
        try:
            payload = _post_json(endpoint, request_preview)
            if not isinstance(payload, dict):
                return {}, attempt, retry_error_codes
            return payload, attempt, retry_error_codes
        except error.HTTPError as exc:
            if attempt >= max_attempts or exc.code not in retry_codes:
                raise
            retry_error_codes.append(exc.code)
            if _backoff_seconds():
                time.sleep(_backoff_seconds())
    return {}, max_attempts, retry_error_codes


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
        payload, attempt_count, retry_error_codes = _post_json_with_retry(endpoint, request_preview)
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

    return _normalize_success(payload, endpoint, request_preview)


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

    request_preview = _range_scan_preview(PARITY_CASES[case_id], domain, start_date, end_date)
    endpoint = os.environ.get("VEDASTRO_API_ENDPOINT", "").strip()
    if not endpoint:
        result = _unconfigured("VEDASTRO_API_ENDPOINT is not configured; range scan stops before network access.")
        result["operation"] = "range_scan"
        result["domain"] = domain
        result["request_preview"] = request_preview
        return result

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
        payload, attempt_count, retry_error_codes = _post_json_with_retry(endpoint, request_preview)
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

    return _normalize_range_scan_success(payload, endpoint, request_preview, attempt_count, retry_error_codes)


def run_external_technique(case_id: str, domain: str, method: str, api_endpoint: str) -> dict[str, Any]:
    if case_id not in PARITY_CASES:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "unknown_case_id",
            "reason": f"Unknown parity case: {case_id}",
        }
    if domain not in SUPPORTED_EXTERNAL_TECHNIQUE_DOMAINS:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "unsupported_external_technique_domain",
            "reason": f"Unsupported external technique domain: {domain}",
            "adjudicator_policy": EXTERNAL_TECHNIQUE_ADJUDICATOR_POLICY,
        }
    if not method.strip() or not api_endpoint.strip():
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "missing_external_technique_method",
            "reason": "Both method and api_endpoint are required for external technique evidence.",
            "adjudicator_policy": EXTERNAL_TECHNIQUE_ADJUDICATOR_POLICY,
        }

    endpoint = os.environ.get("VEDASTRO_API_ENDPOINT", "").strip()
    if not endpoint:
        result = _unconfigured(
            "VEDASTRO_API_ENDPOINT is not configured; external technique evidence stops before network access."
        )
        result["operation"] = EXTERNAL_TECHNIQUE_OPERATION
        result["role"] = EXTERNAL_TECHNIQUE_ROLE
        result["domain"] = domain
        result["adjudicator_policy"] = EXTERNAL_TECHNIQUE_ADJUDICATOR_POLICY
        return result

    request_preview = _external_technique_preview(PARITY_CASES[case_id], domain, method, api_endpoint)
    if os.environ.get(ALLOW_NETWORK_ENV, "").strip().lower() not in {"1", "true", "yes"}:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "network_execution_disabled",
            "reason": (
                f"{ALLOW_NETWORK_ENV} is not enabled; external technique evidence stops "
                "after building request/provenance metadata."
            ),
            "request_preview": request_preview,
            "adjudicator_policy": EXTERNAL_TECHNIQUE_ADJUDICATOR_POLICY,
            "source_metadata": _source_metadata(endpoint),
        }

    try:
        payload = _post_json(endpoint, request_preview)
    except error.HTTPError as exc:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "http_error",
            "reason": f"VedAstro external technique HTTP error: {exc.code}",
            "request_preview": request_preview,
            "adjudicator_policy": EXTERNAL_TECHNIQUE_ADJUDICATOR_POLICY,
            "source_metadata": _source_metadata(endpoint),
        }
    except error.URLError as exc:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "network_error",
            "reason": f"VedAstro external technique network error: {exc.reason}",
            "request_preview": request_preview,
            "adjudicator_policy": EXTERNAL_TECHNIQUE_ADJUDICATOR_POLICY,
            "source_metadata": _source_metadata(endpoint),
        }
    except (TimeoutError, socket.timeout):
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "timeout",
            "reason": "VedAstro external technique timed out",
            "request_preview": request_preview,
            "adjudicator_policy": EXTERNAL_TECHNIQUE_ADJUDICATOR_POLICY,
            "source_metadata": _source_metadata(endpoint),
        }
    except json.JSONDecodeError:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "invalid_json",
            "reason": "VedAstro external technique received non-JSON response",
            "request_preview": request_preview,
            "adjudicator_policy": EXTERNAL_TECHNIQUE_ADJUDICATOR_POLICY,
            "source_metadata": _source_metadata(endpoint),
        }

    return _normalize_external_technique_success(payload, endpoint, request_preview)


def main() -> int:
    parser = argparse.ArgumentParser(description="VedAstro service adapter skeleton")
    parser.add_argument("--print-schema", action="store_true")
    parser.add_argument("--case", default="beijing_first_use_demo")
    parser.add_argument("--range-scan", action="store_true")
    parser.add_argument("--domain", choices=sorted(SUPPORTED_EXTERNAL_TECHNIQUE_DOMAINS), default="marriage")
    parser.add_argument("--start-date", default="2026-01-01")
    parser.add_argument("--end-date", default="2031-01-01")
    parser.add_argument("--external-technique", action="store_true")
    parser.add_argument("--method", default="")
    parser.add_argument("--api-endpoint", default="")
    args = parser.parse_args()

    if args.print_schema:
        result = schema()
    elif args.external_technique:
        result = run_external_technique(args.case, args.domain, args.method, args.api_endpoint)
    elif args.range_scan:
        result = run_range_scan(args.case, args.domain, args.start_date, args.end_date)
    else:
        result = run_case(args.case)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
