#!/usr/bin/env python3
"""Validate independently labeled day-level timing holdout annotations."""

from __future__ import annotations

import argparse, json
from pathlib import Path

REQUIRED={"case_id","domain","label","start","end","source_url","adjudicator","time_uncertainty_days"}

def validate(path: Path) -> dict:
    data=json.loads(path.read_text(encoding="utf-8")); rows=data.get("annotations") or []; errors=[]
    for i,row in enumerate(rows):
        for key in sorted(REQUIRED-set(row)): errors.append({"row":i,"field":key,"error":"missing"})
        if row.get("label") not in {"target_event","no_target_event"}: errors.append({"row":i,"field":"label","error":"invalid"})
        if not str(row.get("source_url") or "").startswith(("https://","http://")): errors.append({"row":i,"field":"source_url","error":"not_public_url"})
    positives=sum(r.get("label")=="target_event" for r in rows); negatives=sum(r.get("label")=="no_target_event" for r in rows)
    gate=data.get("frozen_gate") or {}; ready=not errors and positives>=gate.get("minimum_independent_cases",20) and negatives>=gate.get("minimum_independent_negative_intervals",80)
    return {"scope":"day_level_holdout_validation","annotation_count":len(rows),"positive_count":positives,"negative_count":negatives,"errors":errors,"status":"ready_for_blind_replay" if ready else "awaiting_independent_labels","production_tuning_allowed":False}

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("manifest",type=Path);a=p.parse_args();r=validate(a.manifest);print(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
