#!/usr/bin/env python3
"""Thin bridge to the official public VedAstro MCP endpoint.

This bridge is intentionally narrow. It proves that the official public MCP
surface is reachable and callable from the local workspace without letting
external responses silently override local adjudication.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from typing import Any


DEFAULT_ENDPOINT = "https://mcp.vedastro.org/api/mcp/public"
DEFAULT_PROTOCOL_VERSION = "2025-06-18"
DEFAULT_TIMEOUT_SECONDS = 60


def _post_json(endpoint: str, payload: dict[str, Any], timeout: float = DEFAULT_TIMEOUT_SECONDS) -> tuple[dict[str, Any], dict[str, str]]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        headers = {key.lower(): value for key, value in resp.headers.items()}
    return json.loads(raw), headers


def _initialize(endpoint: str) -> dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": DEFAULT_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {
                "name": "jyotish-local-bridge",
                "version": "1.0.0",
            },
        },
    }
    result, headers = _post_json(endpoint, payload)
    session_id = headers.get("mcp-session-id") or headers.get("x-mcp-session-id")
    return {
        "endpoint": endpoint,
        "available": True,
        "status": "ok",
        "operation": "initialize",
        "session_id": session_id,
        "result": result.get("result") or result,
        "source": "official_public_mcp",
    }


def _tools_list(endpoint: str) -> dict[str, Any]:
    init = _initialize(endpoint)
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if init.get("session_id"):
        headers["Mcp-Session-Id"] = str(init["session_id"])
    req = urllib.request.Request(endpoint, data=body, method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
        raw = resp.read().decode("utf-8")
        response_headers = {key.lower(): value for key, value in resp.headers.items()}
    result = json.loads(raw)
    tools = (result.get("result") or {}).get("tools") or []
    return {
        "endpoint": endpoint,
        "available": True,
        "status": "ok",
        "operation": "tools_list",
        "session_id": init.get("session_id") or response_headers.get("mcp-session-id"),
        "tool_count": len(tools),
        "tool_names": [tool.get("name") for tool in tools if isinstance(tool, dict) and tool.get("name")],
        "result": result.get("result") or result,
        "source": "official_public_mcp",
    }


def schema() -> dict[str, Any]:
    return {
        "bridge": "vedastro_official_mcp_bridge",
        "role": "official_public_mcp_thin_bridge",
        "endpoint": DEFAULT_ENDPOINT,
        "operations": ["initialize", "tools_list"],
        "response_contract": [
            "endpoint",
            "available",
            "status",
            "operation",
            "result",
            "source",
        ],
        "boundaries": [
            "Use for official MCP reachability and tool discovery.",
            "Do not let raw MCP results directly override local score/dominant_label/payout_label.",
            "Promote only through explicit local contracts and tests.",
        ],
    }


def _error_result(endpoint: str, operation: str, exc: Exception) -> dict[str, Any]:
    reason = str(exc)
    if isinstance(exc, urllib.error.HTTPError):
        reason = f"http_{exc.code}: {reason}"
    return {
        "endpoint": endpoint,
        "available": False,
        "status": "mcp_request_failed",
        "operation": operation,
        "reason": reason,
        "source": "official_public_mcp",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Official public VedAstro MCP bridge")
    parser.add_argument("--print-schema", action="store_true")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--operation", choices=["initialize", "tools_list"], default="tools_list")
    args = parser.parse_args()

    if args.print_schema:
        result = schema()
    else:
        try:
            if args.operation == "initialize":
                result = _initialize(args.endpoint)
            else:
                result = _tools_list(args.endpoint)
        except Exception as exc:  # noqa: BLE001
            result = _error_result(args.endpoint, args.operation, exc)

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
