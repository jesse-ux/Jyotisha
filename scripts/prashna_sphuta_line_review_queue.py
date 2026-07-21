#!/usr/bin/env python3
"""Create line-level review tasks from Prasna Marga excerpt locator windows."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOC = ROOT / "references/oracle/prashna_marga_excerpt_locator_2026_07_20.json"
OUT = ROOT / "references/oracle/prashna_sphuta_line_review_queue_2026_07_20.json"

def build(date):
    loc=json.load(open(LOC)); tasks=[]
    for i,w in enumerate(loc['located_windows'],1):
        tasks.append({'task_id':f'PSLRQ-{i:03d}','source_id':w['source_id'],'file_name':w['file_name'],'download_url':w['download_url'],'line_start':w['line_start'],'line_end':w['line_end'],'window_hash':w['window_hash'],'short_context':w['short_context'],'fields_to_check':['trisphuta','chatusphuta','catusphuta','panchasphuta','gulika'],'review_status':'needs_human_or_second_source_review','candidate_causes':['formula_variant','source_transcription','naming_variant'],'claim_boundary':'Review task only; no formula change or truth upgrade.'})
    return {'scope':'prashna_sphuta_line_review_queue','created_at':date,'status':'review_queue_ready','claim_status':'open_queue','production_tuning_allowed':False,'truth_matrix_allowed':False,'summary':{'review_task_count':len(tasks),'truth_upgrade_count':0},'acceptance_criteria':['do_not_copy_long_text','record_line_coordinates','classify_formula_variant_or_transcription','preserve_window_hash','require_second_source_or_scan_review'],'review_tasks':tasks,'boundary':'Human/second-source transcription queue only.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--date',default='2026-07-20'); args=ap.parse_args(); data=build(args.date); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True))
if __name__=='__main__': main()
