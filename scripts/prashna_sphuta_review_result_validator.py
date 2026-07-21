#!/usr/bin/env python3
"""Validate Prashna Sphuta human review result templates."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "references/oracle/prashna_sphuta_review_result_template_2026_07_20.json"
OUT = ROOT / "references/oracle/prashna_sphuta_review_result_validation_2026_07_20.json"

def build(date):
    src=json.load(open(TEMPLATE)); rows=[]
    for t in src['templates']:
        missing=[]
        if t.get('review_result') is None: missing.append('review_result')
        for f in t['required_human_fields']:
            if not t.get(f): missing.append(f)
        valid=not missing and t.get('review_result') in t['allowed_results']
        rows.append({'task_id':t['task_id'],'validation_status':'valid_completed_review' if valid else 'blocked_missing_human_review','missing_fields':missing,'review_result':t.get('review_result'),'replay_gate_ready':False,'claim_boundary':'Validation only; replay gate also requires complete Prashna input.'})
    return {'scope':'prashna_sphuta_review_result_validation','created_at':date,'status':'validation_ready','claim_status':'blocked_until_human_labels','production_tuning_allowed':False,'truth_matrix_allowed':False,'allowed_results':src['templates'][0]['allowed_results'],'replay_gate_policy':'requires_valid_completed_review_and_complete_prashna_input','summary':{'template_count':len(rows),'valid_completed_review_count':sum(r['validation_status']=='valid_completed_review' for r in rows),'replay_gate_ready_count':0},'validation_rows':rows,'boundary':'Blank templates remain blocked; completed review alone still cannot upgrade truth without replay.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--date',default='2026-07-20'); args=ap.parse_args(); data=build(args.date); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True))
if __name__=='__main__': main()
