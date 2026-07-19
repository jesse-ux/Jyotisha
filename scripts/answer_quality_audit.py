#!/usr/bin/env python3
from __future__ import annotations
import json, sys
FORBIDDEN = ["一定发生", "保证结婚", "保证发财", "医疗诊断", "确诊", "签证保证", "exact_day_verified", "full_year_certainty"]
REQUIRED_WHEN_TIMING = ["候选", "窗口", "边界"]
def audit_answer(text: str) -> dict:
    hits = [x for x in FORBIDDEN if x.lower() in text.lower()]
    timing_missing = ("什么时候" in text or "几月" in text or "哪天" in text) and not any(x in text for x in REQUIRED_WHEN_TIMING)
    return {"status": "pass" if not hits and not timing_missing else "fail", "forbidden_hits": hits, "timing_boundary_missing": timing_missing}
def run(path: str | None = None) -> dict:
    rows = json.load(open(path, encoding="utf-8")) if path else []
    results = [audit_answer(str(r.get("answer", r))) for r in rows]
    return {"scope": "answer_quality_audit", "status": "pass" if all(r["status"] == "pass" for r in results) else "fail", "results": results}
if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else None), ensure_ascii=False, indent=2))
