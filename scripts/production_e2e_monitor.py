#!/usr/bin/env python3
from __future__ import annotations
import json, os, urllib.request
from pathlib import Path
import commercial_astrology_e2e_acceptance_runner as runner

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTEXT = ROOT / "artifacts" / "commercial_astrology_e2e_contexts_2026_07_19_run6"

def _get(url: str, cookie: str = "") -> dict:
    req = urllib.request.Request(url, headers={"cookie": cookie} if cookie else {})
    with urllib.request.urlopen(req, timeout=20) as r:
        return {"status": r.status, "body": r.read(2000).decode("utf-8", "replace")}

def run(base_url: str | None = None, context_dir: Path = DEFAULT_CONTEXT) -> dict:
    base_url = base_url or os.getenv("JYOTISHA_PRODUCTION_BASE_URL")
    cookie = os.getenv("JYOTISHA_PRODUCTION_COOKIE", "")
    health = _get(base_url.rstrip("/") + "/api/health", cookie) if base_url else {"status": "skipped_no_base_url"}
    acceptance = runner.evaluate(context_dir=context_dir)
    status = "pass" if acceptance["status"] == "pass" and (not base_url or health["status"] == 200) else "fail"
    return {"scope": "production_e2e_monitor", "status": status, "health": health, "acceptance": acceptance}

if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2, sort_keys=True))
