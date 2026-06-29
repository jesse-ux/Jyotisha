#!/usr/bin/env python3
"""Minimal VedAstro service-boundary adapter skeleton.

This module does not replace the local SwissEph path. It only defines the
request/response schema and a controlled "not configured" status so the
workspace can evolve from research notes to an executable adapter contract.
"""

from __future__ import annotations

import argparse
import http.client
import hashlib
import json
import os
import socket
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import request, error
from urllib.parse import urlparse

try:
    from scripts.local_env import load_local_env
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from local_env import load_local_env


ROOT = Path(__file__).resolve().parents[1]
load_local_env(ROOT)


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
OFFICIAL_SEARCH_EVENTS_ENDPOINT_PATH = "/Calculate/SearchEvents"
OFFICIAL_SEARCH_EVENTS_METHOD = "POST"
OFFICIAL_SEARCH_EVENTS_PROFILE_VERSION = "official_builder_search_events_v1"
OFFICIAL_FULL_SNAPSHOT_PROFILE_VERSION = "official_full_snapshot_v1"
OFFICIAL_METHOD_CATALOG_URL = "https://vedastro.org/Complete-List-VedAstro-API-Methods-Calculators.html"
OFFICIAL_FULL_SNAPSHOT_METHODS = [
    {
        "section": "chart_core",
        "endpoint_path": "/Calculate/AllPlanetData",
        "calculator_name": "AllPlanetData",
        "role": "core_chart_raw_evidence",
        "description": "Core planet, ascendant, house, nakshatra, ayanamsa and node-mode evidence when supported by the official service.",
        "fanout": "planetName",
    },
    {
        "section": "house_core",
        "endpoint_path": "/Calculate/AllHouseData",
        "calculator_name": "AllHouseData",
        "role": "core_house_raw_evidence",
        "description": "Official house data snapshot when supported by the official service.",
        "fanout": "houseName",
    },
    {
        "section": "dasha_all",
        "endpoint_path": "/Calculate/DasaAtRange",
        "calculator_name": "DasaAtRange",
        "role": "all_dasha_raw_evidence",
        "description": "Official dasha timeline snapshot where available.",
    },
    {
        "section": "events_overview",
        "endpoint_path": OFFICIAL_SEARCH_EVENTS_ENDPOINT_PATH,
        "calculator_name": "SearchEvents",
        "role": "life_event_raw_evidence",
        "description": "Official event radar using SearchEvents for career, marriage and wealth tags.",
    },
]
OFFICIAL_FULL_SNAPSHOT_BACKLOG_SECTIONS = [
    {
        "section": "varga_all",
        "role": "all_varga_raw_evidence",
        "status": "catalog_pending",
        "description": "Awaiting official method mapping for all divisional charts; local varga remains fallback until mapped.",
    },
    {
        "section": "shadbala",
        "role": "strength_raw_evidence",
        "status": "catalog_pending",
        "description": "Awaiting official method mapping for Shadbala; local Shadbala remains fallback until mapped.",
    },
    {
        "section": "ashtakavarga",
        "role": "ashtakavarga_raw_evidence",
        "status": "catalog_pending",
        "description": "Awaiting official method mapping for Ashtakavarga; local Ashtakavarga remains fallback until mapped.",
    },
]
OFFICIAL_SNAPSHOT_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu", "Ascendant"]
OFFICIAL_SNAPSHOT_HOUSES = [f"House{i}" for i in range(1, 13)]
OFFICIAL_RANGE_SCAN_EVENT_TAGS = {
    "marriage": ["Marriage", "Personal", "General"],
    "wealth": ["LendingMoney", "BorrowingMoney", "BuyingSelling", "General"],
    "career": ["Personal", "General", "Building", "Travel"],
}
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
RANGE_SCAN_OFFICIAL_TAG_MATCHES = {
    "marriage": {"Marriage"},
    "wealth": {"LendingMoney", "BorrowingMoney", "BuyingSelling"},
    "career": {"Building", "Travel"},
}
RANGE_SCAN_ALIAS_TERMS = {
    "marriage": {
        "marriage",
        "spouse",
        "wedding",
        "relationship",
        "partner",
        "partnership",
    },
    "wealth": {
        "wealth",
        "money",
        "finance",
        "financial",
        "income",
        "gain",
        "gains",
        "lending",
        "borrowing",
        "business",
        "cash",
    },
    "career": {
        "career",
        "profession",
        "work",
        "job",
        "business",
        "travel",
        "building",
        "public",
        "status",
    },
}
MATCH_METADATA_BY_TYPE = {
    "exact_id": {"signal_lift": 3, "confidence": "high"},
    "official_tag": {"signal_lift": 2, "confidence": "medium_high"},
    "alias": {"signal_lift": 1, "confidence": "low"},
    "rejected": {"signal_lift": 0, "confidence": "rejected"},
}
ALIAS_NEGATIVE_GUARD_TERMS = {"noise", "without", "generic", "irrelevant", "insignificance", "not"}
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
        "official_search_events_profile_contract": {
            "profile_version": OFFICIAL_SEARCH_EVENTS_PROFILE_VERSION,
            "base_url_requirement": "VEDASTRO_API_ENDPOINT must end with /api",
            "route_template": OFFICIAL_SEARCH_EVENTS_ENDPOINT_PATH,
            "method": OFFICIAL_SEARCH_EVENTS_METHOD,
            "content_type": "application/json",
            "optional_auth_header": "x-api-key",
            "body_fields": [
                "BirthTime",
                "Ayanamsa",
                "EventTagList",
            ],
            "range_mode_fields": [
                "AtTime | StartTime + EndTime + PrecisionHours",
            ],
        },
        "official_full_snapshot_request_contract": {
            "profile_version": OFFICIAL_FULL_SNAPSHOT_PROFILE_VERSION,
            "primary_source": "vedastro_official",
            "method_catalog_url": OFFICIAL_METHOD_CATALOG_URL,
            "strategy": "fetch_official_raw_sections_first_then_local_crosscheck",
            "common_body_fields": [
                "BirthTime",
                "Ayanamsa",
                "NodeMode",
                "CalculationPreferences",
            ],
            "request_sections": [
                {
                    "section": item["section"],
                    "endpoint_path": item["endpoint_path"],
                    "calculator_name": item.get("calculator_name"),
                    "role": item["role"],
                }
                for item in OFFICIAL_FULL_SNAPSHOT_METHODS
            ],
            "backlog_sections": OFFICIAL_FULL_SNAPSHOT_BACKLOG_SECTIONS,
            "user_visibility": "backend_raw_evidence_not_direct_user_report",
        },
        "vedastro_calculation_coverage": VEDASTRO_CALCULATION_COVERAGE,
        "official_full_snapshot_response_contract": [
            "backend",
            "available",
            "status",
            "operation",
            "primary_source",
            "snapshot_sections",
            "request_manifest",
            "source_metadata",
        ],
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
    preview = {
        "operation": "range_scan",
        "vedastro_event_method": "SearchEvents",
        "domain": domain,
        "start_date": start_date,
        "end_date": end_date,
        "event_model": "vedastro_events_at_range_candidate",
        "search_mode": "single_point",
        **case,
    }
    preview["official_request_profile"] = _build_official_search_events_profile(preview)
    preview["live_sampling_request_profile"] = _build_live_sampling_search_events_profile(preview)
    return preview


def _format_std_time(date_text: str, hour: Any, minute: Any, tz: Any) -> str:
    year, month, day = str(date_text).split("-")
    hour_int = int(float(hour))
    minute_int = int(float(minute))
    return f"{hour_int:02d}:{minute_int:02d} {day}/{month}/{year} {tz}"


def _time_json_from_case(
    case: dict[str, Any],
    date_text: str,
    *,
    hour: Any | None = None,
    minute: Any | None = None,
) -> dict[str, Any]:
    return {
        "StdTime": _format_std_time(
            date_text,
            case.get("hour", 0) if hour is None else hour,
            case.get("minute", 0) if minute is None else minute,
            case.get("tz", "+00:00"),
        ),
        "Location": {
            "Name": case.get("case_id") or "UserLocation",
            "Latitude": case.get("lat"),
            "Longitude": case.get("lon"),
        },
    }


def _normalize_tz(case: dict[str, Any]) -> str:
    tz = case.get("tz")
    if isinstance(tz, str):
        return tz
    if tz is None:
        return "+00:00"
    sign = "+" if float(tz) >= 0 else "-"
    value = abs(float(tz))
    hours = int(value)
    minutes = int(round((value - hours) * 60))
    return f"{sign}{hours:02d}:{minutes:02d}"


def _build_official_search_events_profile(request_preview: dict[str, Any]) -> dict[str, Any]:
    case = dict(request_preview)
    case["tz"] = _normalize_tz(case)
    body = {
        "BirthTime": _time_json_from_case(case, f"{case['year']:04d}-{case['month']:02d}-{case['day']:02d}"),
        "Ayanamsa": str(case.get("ayanamsa_policy") or "lahiri"),
        "EventTagList": OFFICIAL_RANGE_SCAN_EVENT_TAGS.get(str(request_preview.get("domain") or ""), ["General"]),
    }
    start_time = _time_json_from_case(case, str(request_preview["start_date"]))
    end_time = _time_json_from_case(case, str(request_preview["end_date"]))
    if str(request_preview["start_date"]) == str(request_preview["end_date"]):
        body["AtTime"] = start_time
    else:
        body["StartTime"] = start_time
        body["EndTime"] = end_time
        body["PrecisionHours"] = 100
    headers: dict[str, str] = {"Content-Type": "application/json"}
    api_key = os.environ.get("VEDASTRO_API_KEY", "").strip()
    if api_key:
        headers["x-api-key"] = api_key
    return {
        "profile_version": OFFICIAL_SEARCH_EVENTS_PROFILE_VERSION,
        "endpoint_path": OFFICIAL_SEARCH_EVENTS_ENDPOINT_PATH,
        "method": OFFICIAL_SEARCH_EVENTS_METHOD,
        "headers": headers,
        "body": body,
    }


def _build_live_sampling_search_events_profile(request_preview: dict[str, Any]) -> dict[str, Any]:
    case = dict(request_preview)
    case["tz"] = _normalize_tz(case)
    body = {
        "BirthTime": _time_json_from_case(case, f"{case['year']:04d}-{case['month']:02d}-{case['day']:02d}"),
        "Ayanamsa": str(case.get("ayanamsa_policy") or "lahiri"),
        "EventTagList": OFFICIAL_RANGE_SCAN_EVENT_TAGS.get(str(request_preview.get("domain") or ""), ["General"]),
        "AtTime": _time_json_from_case(case, str(request_preview["start_date"])),
    }
    headers: dict[str, str] = {"Content-Type": "application/json"}
    api_key = os.environ.get("VEDASTRO_API_KEY", "").strip()
    if api_key:
        headers["x-api-key"] = api_key
    return {
        "profile_version": f"{OFFICIAL_SEARCH_EVENTS_PROFILE_VERSION}_live_sampling",
        "endpoint_path": OFFICIAL_SEARCH_EVENTS_ENDPOINT_PATH,
        "method": OFFICIAL_SEARCH_EVENTS_METHOD,
        "headers": headers,
        "body": body,
    }


def _official_common_body(case: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(case)
    normalized["tz"] = _normalize_tz(normalized)
    return {
        "time": _time_json_from_case(
            normalized,
            f"{int(normalized['year']):04d}-{int(normalized['month']):02d}-{int(normalized['day']):02d}",
        ),
        "Ayanamsa": str(normalized.get("ayanamsa_policy") or "lahiri"),
        "NodeMode": str(normalized.get("node_policy") or "mean"),
        "CalculationPreferences": {
            "scope": "all_supported_official_calculations",
            "user_visibility": "backend_raw_evidence_not_direct_user_report",
        },
    }


def _official_snapshot_reference_date(case: dict[str, Any]) -> str:
    for key in ("reference_date", "today", "transit_date", "current_date"):
        value = case.get(key)
        if not value:
            continue
        raw = str(value)[:10]
        try:
            datetime.strptime(raw, "%Y-%m-%d")
            return raw
        except ValueError:
            continue
    return datetime.utcnow().strftime("%Y-%m-%d")


def _official_dasha_range_body(case: dict[str, Any], common_body: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(case)
    normalized["tz"] = _normalize_tz(normalized)
    reference = datetime.strptime(_official_snapshot_reference_date(normalized), "%Y-%m-%d").date()
    start_date = reference.replace(month=1, day=1)
    end_date = reference.replace(month=12, day=31)
    return {
        "birthTime": common_body["time"],
        "startTime": _time_json_from_case(normalized, start_date.isoformat(), hour=0, minute=0),
        "endTime": _time_json_from_case(normalized, end_date.isoformat(), hour=23, minute=59),
        "levels": int(normalized.get("dasha_levels") or 3),
        "precisionHours": int(normalized.get("dasha_precision_hours") or 100),
        "Ayanamsa": common_body["Ayanamsa"],
    }


def _official_full_snapshot_manifest(case: dict[str, Any], case_id: str = "user_chart") -> dict[str, Any]:
    common_body = _official_common_body(case)
    reference_date = _official_snapshot_reference_date(case)
    headers: dict[str, str] = {"Content-Type": "application/json"}
    api_key = os.environ.get("VEDASTRO_API_KEY", "").strip()
    if api_key:
        headers["x-api-key"] = api_key
    requests = []
    for item in OFFICIAL_FULL_SNAPSHOT_METHODS:
        body = dict(common_body)
        if item["section"] == "events_overview":
            body = {
                "BirthTime": common_body["time"],
                "Ayanamsa": common_body["Ayanamsa"],
                "EventTagList": sorted({tag for tags in OFFICIAL_RANGE_SCAN_EVENT_TAGS.values() for tag in tags}),
                "AtTime": common_body["time"],
            }
        if item["section"] == "dasha_all":
            body = _official_dasha_range_body(case, common_body)
        fanout_values = []
        if item.get("fanout") == "planetName":
            fanout_values = OFFICIAL_SNAPSHOT_PLANETS
        elif item.get("fanout") == "houseName":
            fanout_values = OFFICIAL_SNAPSHOT_HOUSES
        requests.append(
            {
                "section": item["section"],
                "role": item["role"],
                "calculator_name": item.get("calculator_name"),
                "endpoint_path": item["endpoint_path"],
                "method": "POST",
                "headers": headers,
                "body": body,
                "fanout_parameter": item.get("fanout"),
                "fanout_values": fanout_values,
                "description": item["description"],
            }
        )
    return {
        "operation": "official_full_snapshot",
        "profile_version": OFFICIAL_FULL_SNAPSHOT_PROFILE_VERSION,
        "source_role": "primary_official_raw_evidence",
        "primary_source": "vedastro_official",
        "case_id": case_id,
        "reference_date": reference_date,
        "method_catalog": {
            "url": OFFICIAL_METHOD_CATALOG_URL,
            "declared_coverage": VEDASTRO_CALCULATION_COVERAGE,
            "catalog_role": "all_supported_method_reference_not_user_visible_output",
            "backlog_sections": OFFICIAL_FULL_SNAPSHOT_BACKLOG_SECTIONS,
        },
        "requests": requests,
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
    official_request_profile = request_preview.get("official_request_profile") if isinstance(request_preview, dict) else None
    metadata = {
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
    if isinstance(official_request_profile, dict):
        redacted_headers = dict(official_request_profile.get("headers") or {})
        if "x-api-key" in redacted_headers:
            redacted_headers["x-api-key"] = "[redacted]"
        redacted_profile = {
            **official_request_profile,
            "headers": redacted_headers,
        }
        metadata["official_endpoint_path"] = official_request_profile.get("endpoint_path")
        metadata["official_request_profile"] = redacted_profile
        metadata["official_request_profile_hash"] = _hash_payload(redacted_profile)
    return metadata


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
    # Handle actual VedAstro response formats:
    # {"Status": "Pass", "Payload": {"SearchEvents": [...]}}
    # {"Status": "Pass", "Payload": [...]}
    if payload.get("Status") == "Pass":
        payload_body = payload.get("Payload", [])
        if isinstance(payload_body, dict):
            events = payload_body.get("SearchEvents", [])
        else:
            events = payload_body
    else:
        # Fallback to local stub format if not VedAstro format
        events = payload.get("events", [])
        
    if not isinstance(events, list):
        events = []

    domain = request_preview.get("domain", "")
    allowlist = RANGE_SCAN_EVENT_ALLOWLIST.get(domain, {})
    allowed_ids = allowlist.get("event_ids", set())
    allowed_tags = allowlist.get("tags", set())
    official_tags = RANGE_SCAN_OFFICIAL_TAG_MATCHES.get(domain, set())
    alias_terms = RANGE_SCAN_ALIAS_TERMS.get(domain, set())

    original_event_count = len(events)
    evidence_ledger = []
    mapping_details = []
    matched_tags: set[str] = set()
    recommended_allowlist_candidates: set[str] = set()
    match_counts = {
        "exact_id": 0,
        "official_tag": 0,
        "alias": 0,
        "rejected": 0,
    }
    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            continue
        # VedAstro uses "Name" for event id, and may expose tags as EventTags, tags, or Tag.
        event_id = event.get("Name") or event.get("id") or event.get("name") or f"event_{index}"
        tags = event.get("EventTags") or event.get("tags") or event.get("Tag") or []
        if isinstance(tags, str):
            tags = [part.strip() for part in tags.split(",") if part.strip()]
        elif not isinstance(tags, list):
            tags = []
        tag_set = {str(tag) for tag in tags}
        matched_by = "rejected"
        matched_terms: list[str] = []
        drop_reason = "no_supported_match"
        signal_metadata = RANGE_SCAN_SIGNAL_METADATA.get(domain, {}).get(event_id, {})
        if event_id in allowed_ids:
            matched_by = "exact_id"
            matched_terms = [event_id]
            drop_reason = ""
        else:
            official_tag_hits = sorted(tag_set.intersection(official_tags))
            if official_tag_hits:
                matched_by = "official_tag"
                matched_terms = official_tag_hits
                drop_reason = ""
            else:
                haystack_parts = [
                    str(event_id),
                    str(event.get("Description") or ""),
                    str(event.get("description") or ""),
                    str(event.get("Name") or ""),
                    " ".join(str(tag) for tag in tags),
                ]
                haystack = " ".join(part.lower() for part in haystack_parts if part)
                alias_hits = sorted(term for term in alias_terms if term in haystack)
                guard_hits = sorted(term for term in ALIAS_NEGATIVE_GUARD_TERMS if term in haystack)
                if alias_hits and not guard_hits:
                    matched_by = "alias"
                    matched_terms = alias_hits
                    drop_reason = ""
        match_counts[matched_by] += 1
        if matched_by == "rejected":
            mapping_details.append(
                {
                    "event_id": event_id,
                    "matched_by": matched_by,
                    "matched_terms": matched_terms,
                    "drop_reason": drop_reason,
                    "tags": tags,
                }
            )
            continue
        if matched_by == "official_tag":
            matched_tags.update(matched_terms)
            if event_id not in allowed_ids and not tag_set.intersection(allowed_tags):
                recommended_allowlist_candidates.add(event_id)
        elif matched_by == "alias":
            if event_id not in allowed_ids:
                recommended_allowlist_candidates.add(event_id)
        match_meta = MATCH_METADATA_BY_TYPE[matched_by]
        mapping_details.append(
            {
                "event_id": event_id,
                "matched_by": matched_by,
                "matched_terms": matched_terms,
                "drop_reason": drop_reason,
                "tags": tags,
            }
        )
        evidence_ledger.append(
            {
                "source": "vedastro_service_adapter_candidate",
                "operation": "range_scan",
                "domain": domain,
                "event_id": event_id,
                "matched_by": matched_by,
                "matched_terms": matched_terms,
                "signal_lift": match_meta["signal_lift"],
                "confidence": match_meta["confidence"],
                "drop_reason": None,
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
        "mapping_replay": {
            "raw_event_count": original_event_count,
            "filtered_event_count": len(evidence_ledger),
            "zero_event_domains": [domain] if original_event_count > 0 and not evidence_ledger else [],
            "match_counts": match_counts,
            "matched_tags": sorted(matched_tags),
            "recommended_allowlist_candidates": sorted(recommended_allowlist_candidates),
            "events": mapping_details,
        },
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
    official_request_profile = None
    if isinstance(request_preview, dict):
        official_request_profile = (
            request_preview.get("live_sampling_request_profile")
            or request_preview.get("official_request_profile")
        )
    request_url = endpoint
    headers = {"Content-Type": "application/json"}
    vedastro_payload = request_preview
    if isinstance(official_request_profile, dict):
        request_url = f"{endpoint.rstrip('/')}{official_request_profile.get('endpoint_path', '')}"
        headers = dict(official_request_profile.get("headers") or headers)
        vedastro_payload = dict(official_request_profile.get("body") or {})
    req = request.Request(
        request_url,
        data=json.dumps(vedastro_payload).encode("utf-8"),
        headers=headers,
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


def _iter_sample_dates(start_date: str, end_date: str) -> list[str]:
    from datetime import datetime, timedelta

    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    if end <= start:
        return [start_date]
    span_days = max((end - start).days, 1)
    step_days = max(1, span_days // 11)
    dates: list[str] = []
    current = start
    while current <= end:
        dates.append(current.isoformat())
        current += timedelta(days=step_days)
    if dates[-1] != end.isoformat():
        dates.append(end.isoformat())
    return dates


def _merge_range_scan_reports(
    reports: list[dict[str, Any]],
    endpoint: str,
    base_preview: dict[str, Any],
) -> dict[str, Any]:
    if not reports:
        return _normalize_range_scan_success({"Status": "Pass", "Payload": []}, endpoint, base_preview)

    deduped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for report in reports:
        for item in report.get("evidence_ledger", []):
            key = (
                str(item.get("event_id") or ""),
                str(item.get("start") or ""),
                str(item.get("end") or ""),
            )
            existing = deduped.get(key)
            existing_score = existing.get("signal_lift", 0) if existing else -1
            score = item.get("signal_lift", 0)
            if existing is None or score > existing_score:
                deduped[key] = item

    evidence_ledger = list(deduped.values())
    top_event = None
    if evidence_ledger:
        top = max(
            evidence_ledger,
            key=lambda item: (
                item.get("signal_lift") if isinstance(item.get("signal_lift"), (int, float)) else 0,
                item.get("confidence") == "high",
            ),
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

    metadata = dict(reports[-1].get("source_metadata") or {})
    metadata["sampling_mode"] = "at_time_sweep"
    metadata["sample_dates"] = [report.get("request_preview", {}).get("start_date") for report in reports]
    metadata["sample_count"] = len(reports)
    metadata["raw_event_count"] = sum(int((report.get("source_metadata") or {}).get("raw_event_count", 0)) for report in reports)
    metadata["filtered_event_count"] = len(evidence_ledger)
    metadata["allowlist_event_count"] = len(evidence_ledger)
    metadata["attempt_count"] = sum(int((report.get("source_metadata") or {}).get("attempt_count", 1)) for report in reports)
    retry_codes: list[int] = []
    for report in reports:
        retry_codes.extend(list((report.get("source_metadata") or {}).get("retry_error_codes") or []))
    metadata["retry_error_codes"] = retry_codes

    result = {
        "backend": "vedastro_service_adapter_candidate",
        "available": True,
        "status": "ok",
        "operation": "range_scan",
        "domain": base_preview.get("domain"),
        "request_preview": base_preview,
        "event_count": len(evidence_ledger),
        "top_event": top_event,
        "evidence_ledger": evidence_ledger,
        "source_metadata": metadata,
    }
    result["source_metadata"]["artifact_path"] = _write_artifact(result)
    return result


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


def _official_full_snapshot_metadata(endpoint: str | None, manifest: dict[str, Any]) -> dict[str, Any]:
    metadata = {
        "transport": "http_json_service_boundary",
        "operation": "official_full_snapshot",
        "primary_source": "vedastro_official",
        "provenance_mode": "vedastro_official_primary_candidate",
        "timeout_seconds": _timeout_seconds(),
        "retry_policy": {**RETRY_POLICY, "backoff_seconds": _backoff_seconds()},
        "network_execution_env": ALLOW_NETWORK_ENV,
        "method_catalog_url": OFFICIAL_METHOD_CATALOG_URL,
        "reference_date": manifest.get("reference_date"),
        "request_hash": _hash_payload(manifest),
    }
    if endpoint:
        metadata["endpoint"] = endpoint
        metadata["endpoint_host"] = _endpoint_host(endpoint)
    return metadata


def _payload_status(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return "invalid"
    if str(payload.get("Status") or "").lower() == "fail":
        failure_text = json.dumps(payload.get("Payload"), ensure_ascii=False).lower()
        if "rate limit" in failure_text or "calls/minute" in failure_text or "too many requests" in failure_text:
            return "rate_limited"
    return "ok" if payload.get("Status") == "Pass" else "fail"


def _aggregate_section_status(statuses: list[str]) -> str:
    if statuses and all(status == "ok" for status in statuses):
        return "ok"
    if any(status == "rate_limited" for status in statuses):
        return "rate_limited"
    return "partial"


def _degrees_from_sign_payload(value: Any) -> float | None:
    if not isinstance(value, dict):
        return None
    degrees = value.get("DegreesIn") if isinstance(value.get("DegreesIn"), dict) else {}
    raw = degrees.get("TotalDegrees")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _sign_position(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    sign = value.get("Name")
    degree = _degrees_from_sign_payload(value)
    if not sign:
        return None
    return {
        "sign": sign,
        "degree_in_sign": degree,
    }


def _extract_all_planet_data(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    body = payload.get("Payload") if isinstance(payload.get("Payload"), dict) else {}
    data = body.get("AllPlanetData") if isinstance(body.get("AllPlanetData"), dict) else {}
    return data if isinstance(data, dict) else {}


def _extract_all_house_data(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    body = payload.get("Payload") if isinstance(payload.get("Payload"), dict) else {}
    data = body.get("AllHouseData") if isinstance(body.get("AllHouseData"), dict) else {}
    return data if isinstance(data, dict) else {}


def _official_planet_snapshot(planet_name: str, data: dict[str, Any]) -> dict[str, Any]:
    d1 = _sign_position(data.get("PlanetRasiD1Sign")) or {}
    raw_lon = None
    nirayana = data.get("PlanetNirayanaLongitude")
    if isinstance(nirayana, dict):
        try:
            raw_lon = float(nirayana.get("TotalDegrees"))
        except (TypeError, ValueError):
            raw_lon = None
    house_text = data.get("HousePlanetOccupiesBasedOnSign") or data.get("HousePlanetOccupiesBasedOnLongitudes")
    house = None
    if isinstance(house_text, str) and house_text.lower().startswith("house"):
        try:
            house = int("".join(ch for ch in house_text if ch.isdigit()))
        except ValueError:
            house = None
    return {
        "source": "vedastro_official",
        "name": planet_name,
        "sign": d1.get("sign"),
        "degree_in_sign": d1.get("degree_in_sign"),
        "degree": raw_lon,
        "lon": raw_lon,
        "house": house,
        "vargas": {
            "D1": d1,
            "D2": _sign_position(data.get("PlanetHoraD2Signs")),
            "D3": _sign_position(data.get("PlanetDrekkanaD3Sign")),
            "D4": _sign_position(data.get("PlanetChaturthamshaD4Sign")),
            "D7": _sign_position(data.get("PlanetSaptamshaD7Sign")),
            "D9": _sign_position(data.get("PlanetNavamshaD9Sign")),
            "D10": _sign_position(data.get("PlanetDashamamshaD10Sign")),
            "D12": _sign_position(data.get("PlanetDwadashamshaD12Sign")),
            "D16": _sign_position(data.get("PlanetShodashamshaD16Sign")),
            "D20": _sign_position(data.get("PlanetVimshamshaD20Sign")),
            "D24": _sign_position(data.get("PlanetChaturvimshamshaD24Sign")),
            "D27": _sign_position(data.get("PlanetBhamshaD27Sign")),
            "D30": _sign_position(data.get("PlanetTrimshamshaD30Sign")),
            "D40": _sign_position(data.get("PlanetKhavedamshaD40Sign")),
            "D45": _sign_position(data.get("PlanetAkshavedamshaD45Sign")),
            "D60": _sign_position(data.get("PlanetShashtyamshaD60Sign")),
        },
        "nakshatra": data.get("PlanetConstellation"),
        "raw_source_keys": sorted(data.keys()),
    }


def _official_house_snapshot(house_name: str, data: dict[str, Any]) -> dict[str, Any]:
    d1 = _sign_position(data.get("HouseRasiD1Sign") or data.get("HouseBhavaChalitSign")) or {}
    return {
        "source": "vedastro_official",
        "name": house_name,
        "sign": d1.get("sign"),
        "degree_in_sign": d1.get("degree_in_sign"),
        "vargas": {
            "D1": d1,
            "D2": _sign_position(data.get("HouseHoraD2Sign") or data.get("HouseHoraD2Signs")),
            "D3": _sign_position(data.get("HouseDrekkanaD3Sign")),
            "D4": _sign_position(data.get("HouseChaturthamshaD4Sign")),
            "D7": _sign_position(data.get("HouseSaptamshaD7Sign")),
            "D9": _sign_position(data.get("HouseNavamshaD9Sign") or data.get("HouseNavamsaD9Sign")),
            "D10": _sign_position(data.get("HouseDashamamshaD10Sign")),
            "D12": _sign_position(data.get("HouseDwadashamshaD12Sign")),
            "D16": _sign_position(data.get("HouseShodashamshaD16Sign")),
            "D20": _sign_position(data.get("HouseVimshamshaD20Sign")),
            "D24": _sign_position(data.get("HouseChaturvimshamshaD24Sign")),
            "D27": _sign_position(data.get("HouseBhamshaD27Sign")),
            "D30": _sign_position(data.get("HouseTrimshamshaD30Sign")),
            "D40": _sign_position(data.get("HouseKhavedamshaD40Sign")),
            "D45": _sign_position(data.get("HouseAkshavedamshaD45Sign")),
            "D60": _sign_position(data.get("HouseShashtyamshaD60Sign")),
        },
        "nakshatra": data.get("HouseConstellation"),
        "raw_source_keys": sorted(data.keys()),
    }


def _build_official_chart_from_snapshot(sections: dict[str, Any]) -> dict[str, Any]:
    chart_core = sections.get("chart_core") if isinstance(sections.get("chart_core"), dict) else {}
    house_core = sections.get("house_core") if isinstance(sections.get("house_core"), dict) else {}
    planets: dict[str, Any] = {}
    for planet_name, payload in chart_core.items():
        data = _extract_all_planet_data(payload)
        if data:
            planets[planet_name] = _official_planet_snapshot(planet_name, data)
    houses: dict[str, Any] = {}
    for house_name, payload in house_core.items():
        data = _extract_all_house_data(payload)
        if data:
            houses[house_name] = _official_house_snapshot(house_name, data)
    ascendant = houses.get("House1") or {}
    return {
        "source": "vedastro_official",
        "primary_source": "vedastro_official",
        "planets": planets,
        "houses": houses,
        "ascendant": ascendant,
        "coverage": {
            "planet_count": len(planets),
            "house_count": len(houses),
            "varga_keys": ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60"],
        },
    }


def _post_official_snapshot_section(endpoint: str, request_item: dict[str, Any]) -> tuple[dict[str, Any], int, list[int]]:
    body = dict(request_item["body"])
    fanout_parameter = request_item.get("fanout_parameter")
    fanout_value = request_item.get("fanout_value")
    if fanout_parameter and fanout_value is not None:
        if fanout_parameter == "planetName":
            body[fanout_parameter] = {"Name": str(fanout_value)}
        else:
            body[fanout_parameter] = str(fanout_value)
    section_preview = {
        "operation": "official_full_snapshot",
        "section": request_item["section"],
        "official_request_profile": {
            "profile_version": OFFICIAL_FULL_SNAPSHOT_PROFILE_VERSION,
            "endpoint_path": request_item["endpoint_path"],
            "method": request_item["method"],
            "headers": request_item["headers"],
            "body": body,
        },
    }
    return _post_json_with_retry(endpoint, section_preview)


def _normalize_official_full_snapshot_success(
    endpoint: str,
    manifest: dict[str, Any],
    sections: dict[str, Any],
    section_statuses: dict[str, str],
    attempt_count: int,
    retry_error_codes: list[int],
) -> dict[str, Any]:
    primary_sections = [item["section"] for item in manifest["requests"]]
    ok_count = sum(1 for section in primary_sections if section_statuses.get(section) == "ok")
    status = "ok" if ok_count == len(primary_sections) else "partial"
    rate_limited_sections = [
        section
        for section in primary_sections
        if section_statuses.get(section) == "rate_limited"
    ]
    metadata = {
        **_official_full_snapshot_metadata(endpoint, manifest),
        "called_at": _utc_timestamp(),
        "section_statuses": section_statuses,
        "section_count": len(primary_sections),
        "section_ok_count": ok_count,
        "rate_limited_sections": rate_limited_sections,
        "attempt_count": attempt_count,
        "retry_error_codes": retry_error_codes,
        "response_hash": _hash_payload({"sections": sections, "section_statuses": section_statuses}),
    }
    if rate_limited_sections:
        metadata["production_hint"] = "configure_vedastro_api_key_or_self_host_official_api"
    result = {
        "backend": "vedastro_service_adapter_candidate",
        "available": ok_count > 0,
        "status": status,
        "operation": "official_full_snapshot",
        "primary_source": "vedastro_official",
        "snapshot_sections": sections,
        "official_chart": _build_official_chart_from_snapshot(sections),
        "section_statuses": section_statuses,
        "request_manifest": manifest,
        "user_visibility": "backend_raw_evidence_not_direct_user_report",
        "source_metadata": metadata,
    }
    result["source_metadata"]["artifact_path"] = _write_artifact(result)
    return result


def _run_official_full_snapshot_case(case: dict[str, Any], case_id: str = "user_chart") -> dict[str, Any]:
    user_case = {
        "case_id": case_id,
        "year": case.get("year"),
        "month": case.get("month"),
        "day": case.get("day"),
        "hour": case.get("hour"),
        "minute": case.get("minute"),
        "second": case.get("second", 0),
        "lat": case.get("lat"),
        "lon": case.get("lon"),
        "tz": case.get("tz"),
        "ayanamsa_policy": case.get("ayanamsa_policy") or case.get("ayanamsa") or "lahiri",
        "node_policy": case.get("node_policy") or case.get("node_mode") or "mean",
        "reference_date": case.get("reference_date") or case.get("today") or case.get("transit_date") or case.get("current_date"),
        "dasha_levels": case.get("dasha_levels"),
        "dasha_precision_hours": case.get("dasha_precision_hours"),
    }
    manifest = _official_full_snapshot_manifest(user_case, case_id)
    endpoint = os.environ.get("VEDASTRO_API_ENDPOINT", "").strip()
    if not endpoint:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "service_endpoint_not_configured",
            "operation": "official_full_snapshot",
            "primary_source": "vedastro_official",
            "reason": "VEDASTRO_API_ENDPOINT is not configured; official full snapshot stops before network access.",
            "snapshot_sections": {},
            "request_manifest": manifest,
            "user_visibility": "backend_raw_evidence_not_direct_user_report",
            "source_metadata": _official_full_snapshot_metadata(None, manifest),
        }

    if os.environ.get(ALLOW_NETWORK_ENV, "").strip().lower() not in {"1", "true", "yes"}:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "network_execution_disabled",
            "operation": "official_full_snapshot",
            "primary_source": "vedastro_official",
            "reason": f"{ALLOW_NETWORK_ENV} is not enabled; official full snapshot stops after building request manifest.",
            "snapshot_sections": {},
            "request_manifest": manifest,
            "user_visibility": "backend_raw_evidence_not_direct_user_report",
            "source_metadata": _official_full_snapshot_metadata(endpoint, manifest),
        }

    sections: dict[str, Any] = {}
    section_statuses: dict[str, str] = {}
    attempt_count = 0
    retry_error_codes: list[int] = []
    for request_item in manifest["requests"]:
        section = request_item["section"]
        fanout_values = request_item.get("fanout_values") if isinstance(request_item.get("fanout_values"), list) else []
        if fanout_values:
            section_payloads: dict[str, Any] = {}
            fanout_statuses: dict[str, str] = {}
            for value in fanout_values:
                fanout_request = {**request_item, "fanout_value": value}
                try:
                    payload, attempts, retries = _post_official_snapshot_section(endpoint, fanout_request)
                    section_payloads[str(value)] = payload
                    fanout_statuses[str(value)] = _payload_status(payload)
                    attempt_count += attempts
                    retry_error_codes.extend(retries)
                except error.HTTPError as exc:
                    fanout_statuses[str(value)] = f"http_error:{exc.code}"
                except (error.URLError, http.client.RemoteDisconnected) as exc:
                    fanout_statuses[str(value)] = f"network_error:{getattr(exc, 'reason', str(exc))}"
                except (TimeoutError, socket.timeout):
                    fanout_statuses[str(value)] = "timeout"
                except json.JSONDecodeError:
                    fanout_statuses[str(value)] = "invalid_json"
            sections[section] = section_payloads
            section_statuses[section] = _aggregate_section_status(list(fanout_statuses.values()))
            section_statuses[f"{section}_fanout"] = fanout_statuses
            continue

        try:
            payload, attempts, retries = _post_official_snapshot_section(endpoint, request_item)
            sections[section] = payload
            section_statuses[section] = _payload_status(payload)
            attempt_count += attempts
            retry_error_codes.extend(retries)
        except error.HTTPError as exc:
            section_statuses[section] = f"http_error:{exc.code}"
        except (error.URLError, http.client.RemoteDisconnected) as exc:
            section_statuses[section] = f"network_error:{getattr(exc, 'reason', str(exc))}"
        except (TimeoutError, socket.timeout):
            section_statuses[section] = "timeout"
        except json.JSONDecodeError:
            section_statuses[section] = "invalid_json"

    return _normalize_official_full_snapshot_success(
        endpoint,
        manifest,
        sections,
        section_statuses,
        attempt_count or 1,
        retry_error_codes,
    )


def run_official_full_snapshot(case_id: str, reference_date: str | None = None) -> dict[str, Any]:
    if case_id not in PARITY_CASES:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "unknown_case_id",
            "operation": "official_full_snapshot",
            "primary_source": "vedastro_official",
            "reason": f"Unknown parity case: {case_id}",
        }
    case = dict(PARITY_CASES[case_id])
    if reference_date:
        case["reference_date"] = reference_date
    return _run_official_full_snapshot_case(case, case_id=case_id)


def run_official_full_snapshot_for_case(
    case: dict[str, Any],
    *,
    case_id: str = "user_chart",
) -> dict[str, Any]:
    return _run_official_full_snapshot_case(case, case_id=case_id)


def _run_range_scan_case(case: dict[str, Any], domain: str, start_date: str, end_date: str) -> dict[str, Any]:
    if domain not in SUPPORTED_RANGE_SCAN_DOMAINS:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "unsupported_range_scan_domain",
            "reason": f"Unsupported range scan domain: {domain}",
        }

    request_preview = _range_scan_preview(case, domain, start_date, end_date)
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

    sample_dates = _iter_sample_dates(start_date, end_date)
    reports: list[dict[str, Any]] = []
    for sample_date in sample_dates:
        sample_preview = dict(request_preview)
        sample_preview["start_date"] = sample_date
        sample_preview["end_date"] = sample_date
        sample_preview["official_request_profile"] = _build_official_search_events_profile(sample_preview)
        sample_preview["live_sampling_request_profile"] = _build_live_sampling_search_events_profile(sample_preview)
        try:
            payload, attempt_count, retry_error_codes = _post_json_with_retry(endpoint, sample_preview)
        except error.HTTPError as exc:
            return {
                "backend": "vedastro_service_adapter_candidate",
                "available": False,
                "status": "http_error",
                "reason": f"VedAstro range scan HTTP error: {exc.code}",
                "request_preview": sample_preview,
                "source_metadata": _source_metadata(endpoint),
            }
        except (error.URLError, http.client.RemoteDisconnected) as exc:
            return {
                "backend": "vedastro_service_adapter_candidate",
                "available": False,
                "status": "network_error",
                "reason": f"VedAstro range scan network error: {getattr(exc, 'reason', str(exc))}",
                "request_preview": sample_preview,
                "source_metadata": _source_metadata(endpoint),
            }
        except (TimeoutError, socket.timeout):
            return {
                "backend": "vedastro_service_adapter_candidate",
                "available": False,
                "status": "timeout",
                "reason": "VedAstro range scan timed out",
                "request_preview": sample_preview,
                "source_metadata": _source_metadata(endpoint),
            }
        except json.JSONDecodeError:
            return {
                "backend": "vedastro_service_adapter_candidate",
                "available": False,
                "status": "invalid_json",
                "reason": "VedAstro range scan received non-JSON response",
                "request_preview": sample_preview,
                "source_metadata": _source_metadata(endpoint),
            }
        reports.append(_normalize_range_scan_success(payload, endpoint, sample_preview, attempt_count, retry_error_codes))

    return _merge_range_scan_reports(reports, endpoint, request_preview)


def run_range_scan(case_id: str, domain: str, start_date: str, end_date: str) -> dict[str, Any]:
    if case_id not in PARITY_CASES:
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": False,
            "status": "unknown_case_id",
            "reason": f"Unknown parity case: {case_id}",
        }
    return _run_range_scan_case(PARITY_CASES[case_id], domain, start_date, end_date)


def run_range_scan_for_case(
    case: dict[str, Any],
    domain: str,
    start_date: str,
    end_date: str,
    case_id: str = "user_chart",
) -> dict[str, Any]:
    user_case = {
        "case_id": case_id,
        "year": case.get("year"),
        "month": case.get("month"),
        "day": case.get("day"),
        "hour": case.get("hour"),
        "minute": case.get("minute"),
        "second": case.get("second", 0),
        "lat": case.get("lat"),
        "lon": case.get("lon"),
        "tz": case.get("tz"),
        "ayanamsa_policy": case.get("ayanamsa_policy") or case.get("ayanamsa") or "lahiri",
        "node_policy": case.get("node_policy") or case.get("node_mode") or "mean",
    }
    return _run_range_scan_case(user_case, domain, start_date, end_date)


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
    parser.add_argument("--official-full-snapshot", action="store_true")
    parser.add_argument("--domain", choices=sorted(SUPPORTED_EXTERNAL_TECHNIQUE_DOMAINS), default="marriage")
    parser.add_argument("--start-date", default="2026-01-01")
    parser.add_argument("--end-date", default="2031-01-01")
    parser.add_argument("--reference-date", default=None)
    parser.add_argument("--external-technique", action="store_true")
    parser.add_argument("--method", default="")
    parser.add_argument("--api-endpoint", default="")
    args = parser.parse_args()

    if args.print_schema:
        result = schema()
    elif args.official_full_snapshot:
        result = run_official_full_snapshot(args.case, reference_date=args.reference_date)
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
