#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def _load(rel: str) -> dict:
    p = ROOT / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"status": "missing"}
def run() -> dict:
    e2e = _load("references/cross_project_contract/commercial_astrology_e2e_runtime_capture_report_2026_07_19.json")
    return {"scope": "long_term_validation_dashboard", "status": "ready", "items": {
        "commercial_e2e": e2e.get("status"),
        "vedastro_hosted_identity": "blocked_until_build_version",
        "day_month_holdout": "awaiting_independent_labels",
        "shadbala_av": "partial_worked_example_arbitration",
        "kp_precision": "probe_only",
        "muhurta": "gap_registry_probe_only"
    }}
if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2, sort_keys=True))
