#!/usr/bin/env python3
"""Build field-level comparison matrix for Prashna Sphuta sources."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPLAY = ROOT / "references/oracle/prashna_sphuta_candidate_replay_readiness_2026_07_20.json"
LOCATOR = ROOT / "references/oracle/prashna_marga_excerpt_locator_2026_07_20.json"
OUT = ROOT / "references/oracle/prashna_sphuta_source_comparison_matrix_2026_07_20.json"

FIELDS=['sun','moon','lagna','gulika','rahu','trisphuta','chatusphuta','panchasphuta']

def status(row, field):
    if field in ['sun','moon','lagna','gulika','rahu']: return 'input_value_only'
    got=row['computed_from_expected_degrees'][field]; exp=row['expected_degrees'][field]
    return 'match' if abs(((got-exp+180)%360)-180) <= .02 else 'mismatch'

def build(date):
    replay=json.load(open(REPLAY)); locator=json.load(open(LOCATOR)); base=replay['rows'][0]
    has_ia=locator['summary']['located_window_count']>0
    rows=[]
    for f in FIELDS:
        rows.append({'field':f,'vedastro_expected_degree':base['expected_degrees'][f],'local_formula_degree':base['computed_from_expected_degrees'].get(f),'local_vs_vedastro_status':status(base,f),'ia_excerpt_status':'located_context' if has_ia and f in ['gulika','trisphuta','chatusphuta','panchasphuta'] else 'not_field_specific','claim_boundary':'Field comparison only; no Prashna truth upgrade without complete input/raw/replay.'})
    return {'scope':'prashna_sphuta_source_comparison_matrix','created_at':date,'status':'comparison_matrix_ready','claim_status':'open_queue','production_tuning_allowed':False,'truth_matrix_allowed':False,'summary':{'field_count':len(rows),'match_count':sum(r['local_vs_vedastro_status']=='match' for r in rows),'mismatch_count':sum(r['local_vs_vedastro_status']=='mismatch' for r in rows),'truth_upgrade_count':0},'ia_excerpt_window_count':locator['summary']['located_window_count'],'field_rows':rows,'next_evidence':['line-level transcription review','complete Prashna input','legal external replay'],'boundary':'Matrix connects VedAstro expected values, local arithmetic replay, and IA locator hashes; still open queue.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--date',default='2026-07-20'); args=ap.parse_args(); data=build(args.date); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True))
if __name__=='__main__': main()
