#!/usr/bin/env python3
"""Sync a lightweight VedAstro method catalog snapshot.

This script intentionally starts small. It can pull the official event-tag
catalog from VedAstro's public API or write a stubbed snapshot in tests. The
result is a local JSON snapshot suitable for later MCP/Python/REST routing.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib import request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "scratch" / "local" / "vedastro_adapter" / "method_catalog_snapshot.json"
OFFICIAL_TAG_CATALOG_URL = "https://api.vedastro.org/api/Calculate/GetAllEventDataGroupedByTag"
STUB_ENV = "VEDASTRO_METHOD_CATALOG_STUB"
PYTHON_BRIDGE = ROOT / "scripts" / "vedastro_python_bridge.py"


def schema() -> dict[str, Any]:
    return {
        "sync": "vedastro_method_catalog_sync",
        "scope": "official_vedastro_method_catalog",
        "operations": ["sync_tags", "sync_python_capabilities", "write_snapshot"],
        "sources": {
            "official_tag_catalog": OFFICIAL_TAG_CATALOG_URL,
            "official_python_package": "vedastro.Calculate",
        },
        "output_contract": ["source", "summary", "tag_groups", "python_capabilities", "python_signature_buckets"],
    }


def _load_stubbed_catalog() -> dict[str, Any] | None:
    raw = os.environ.get(STUB_ENV, "").strip()
    if not raw:
        return None
    return json.loads(raw)


def _build_python_signature_buckets(rows: list[dict[str, Any]]) -> dict[str, Any]:
    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        bucket = str(row.get("bucket") or "unknown")
        entry = buckets.setdefault(bucket, {"count": 0, "examples": []})
        entry["count"] += 1
        if len(entry["examples"]) < 10:
            entry["examples"].append(row["method"])
    return buckets


def _scan_python_capabilities() -> list[dict[str, Any]]:
    if not PYTHON_BRIDGE.exists():
        return []
    completed = subprocess.run(
        [sys.executable, str(PYTHON_BRIDGE), "--list-capabilities"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=240,
        check=False,
        env=os.environ.copy(),
    )
    if completed.returncode != 0:
        return []
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return []
    capabilities = payload.get("capabilities")
    return capabilities if isinstance(capabilities, list) else []


def _fetch_official_tag_catalog() -> dict[str, Any]:
    with request.urlopen(OFFICIAL_TAG_CATALOG_URL, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    groups = ((payload.get("Payload") or {}).get("GetAllEventDataGroupedByTag") or {})
    return {
        "source": "official_tag_catalog",
        "tag_groups": groups,
    }


def build_catalog() -> dict[str, Any]:
    catalog = _load_stubbed_catalog() or _fetch_official_tag_catalog()
    tag_groups = catalog.get("tag_groups") or {}
    method_count = 0
    for events in tag_groups.values():
        if isinstance(events, list):
            method_count += len(events)
    python_capabilities = catalog.get("python_capabilities")
    if not isinstance(python_capabilities, list):
        try:
            python_capabilities = _scan_python_capabilities()
        except Exception:
            python_capabilities = []
    python_signature_buckets = _build_python_signature_buckets(python_capabilities)
    python_callable_count = sum(1 for row in python_capabilities if row.get("callable"))
    catalog["python_capabilities"] = python_capabilities
    catalog["python_signature_buckets"] = python_signature_buckets
    catalog["summary"] = {
        "tag_count": len(tag_groups),
        "method_count": method_count,
        "python_capability_count": len(python_capabilities),
        "python_callable_count": python_callable_count,
        "python_signature_bucket_count": len(python_signature_buckets),
    }
    return catalog


def write_snapshot(output_path: Path) -> dict[str, Any]:
    catalog = build_catalog()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "status": "ok",
        "source": catalog.get("source"),
        "summary": catalog.get("summary"),
        "output_path": str(output_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="VedAstro method catalog sync")
    parser.add_argument("--print-schema", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    if args.print_schema:
        result = schema()
    elif args.write:
        result = write_snapshot(Path(args.output))
    else:
        result = build_catalog()

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
