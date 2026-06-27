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
from pathlib import Path
from typing import Any


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

DEFAULT_TIMEOUT_SECONDS = 8
RETRY_POLICY = {
    "max_attempts": 2,
    "backoff_seconds": 1,
    "retry_on": ["timeout", "429", "502", "503", "504"],
}
ALLOW_NETWORK_ENV = "VEDASTRO_ENABLE_NETWORK"


def schema() -> dict[str, Any]:
    request_example = {
        **PARITY_CASES["beijing_first_use_demo"],
        "body_list": ["Sun", "Moon", "Ascendant", "Rahu", "Ketu"],
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
            "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
            "retry_policy": RETRY_POLICY,
        },
    }


def _request_preview(case: dict[str, Any]) -> dict[str, Any]:
    return {
        **case,
        "body_list": ["Sun", "Moon", "Ascendant", "Rahu", "Ketu"],
    }


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
            "source_metadata": {
                "transport": "http_json_service_boundary",
                "endpoint": endpoint,
                "provenance_mode": "external_service_candidate",
                "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
                "retry_policy": RETRY_POLICY,
                "network_execution_env": ALLOW_NETWORK_ENV,
            },
        }
    return {
        "backend": "vedastro_service_adapter_candidate",
        "available": False,
        "status": "service_execution_not_implemented",
        "reason": "Endpoint is configured, but the real HTTP execution/normalization layer is intentionally not implemented yet.",
        "request_preview": request_preview,
        "source_metadata": {
            "transport": "http_json_service_boundary",
            "endpoint": endpoint,
            "provenance_mode": "external_service_candidate",
            "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
            "retry_policy": RETRY_POLICY,
            "network_execution_env": ALLOW_NETWORK_ENV,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="VedAstro service adapter skeleton")
    parser.add_argument("--print-schema", action="store_true")
    parser.add_argument("--case", default="beijing_first_use_demo")
    args = parser.parse_args()

    result = schema() if args.print_schema else run_case(args.case)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
