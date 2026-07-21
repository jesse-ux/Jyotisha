#!/usr/bin/env python3
"""Create blank human review result templates for Prashna Sphuta line tasks."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "references/oracle/prashna_sphuta_line_review_queue_2026_07_20.json"
OUT = ROOT / "references/oracle/prashna_sphuta_review_result_template_2026_07_20.json"
ALLOWED = ["formula_variant", "source_transcription", "naming_variant", "insufficient_evidence"]
REQ = ["reviewer_id", "reviewed_at", "source_line_coordinates", "second_source_or_scan_evidence", "review_notes"]

def build(date):
    q=json.load(open(QUEUE)); templates=[]
    for t in q['review_tasks']:
        templates.append({**t,'review_result':None,'allowed_results':ALLOWED,'required_human_fields':REQ,'completed':False,'upgrade_after_completion':'requires_replay_packet_and_gate_review'})
    return {'scope':'prashna_sphuta_review_result_template','created_at':date,'status':'blank_review_template_ready','claim_status':'blocked_until_human_labels','production_tuning_allowed':False,'truth_matrix_allowed':False,'summary':{'template_count':len(templates),'completed_review_count':0,'truth_upgrade_count':0},'upgrade_policy':'no_upgrade_until_completed_review_and_replay','templates':templates,'boundary':'Blank template only; human review fields must be filled before any classification or formula change.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--date',default='2026-07-20'); args=ap.parse_args(); data=build(args.date); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True))
if __name__=='__main__': main()
