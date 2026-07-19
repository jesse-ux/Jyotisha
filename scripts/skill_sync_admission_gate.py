#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / "references/oracle/effective_skill_capability_view_2026_07_19.json"
def run() -> dict:
    data = json.loads(VIEW.read_text(encoding="utf-8"))
    blocked = []
    for item in data.get("items", []):
        status = item.get("effective_status") or item.get("claim_status")
        if status in {"blocked", "research_only", "reference_only"} and item.get("commercial_claim_allowed") is True:
            blocked.append(item.get("technique_id") or item.get("id"))
    return {"scope": "skill_sync_admission_gate", "status": "pass" if not blocked else "fail", "blocked_promotions": blocked}
if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2, sort_keys=True))
