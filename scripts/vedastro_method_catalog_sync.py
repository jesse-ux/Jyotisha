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
from pathlib import Path
from typing import Any
from urllib import request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "scratch" / "local" / "vedastro_adapter" / "method_catalog_snapshot.json"
OFFICIAL_TAG_CATALOG_URL = "https://api.vedastro.org/api/Calculate/GetAllEventDataGroupedByTag"
STUB_ENV = "VEDASTRO_METHOD_CATALOG_STUB"


def schema() -> dict[str, Any]:
    return {
        "sync": "vedastro_method_catalog_sync",
        "scope": "official_vedastro_method_catalog",
        "operations": ["sync_tags", "write_snapshot"],
        "sources": {
            "official_tag_catalog": OFFICIAL_TAG_CATALOG_URL,
        },
        "output_contract": ["source", "summary", "tag_groups"],
    }


def _load_stubbed_catalog() -> dict[str, Any] | None:
    raw = os.environ.get(STUB_ENV, "").strip()
    if not raw:
        return None
    return json.loads(raw)


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
    catalog["summary"] = {
        "tag_count": len(tag_groups),
        "method_count": method_count,
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
