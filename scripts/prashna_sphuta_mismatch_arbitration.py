#!/usr/bin/env python3
"""Arbitrate Prashna Sphuta expected-value mismatches without truth upgrade."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPLAY = ROOT / "references/oracle/prashna_sphuta_candidate_replay_readiness_2026_07_20.json"
OUT = ROOT / "references/oracle/prashna_sphuta_mismatch_arbitration_2026_07_20.json"

def status(row, key, tol=0.02):
    exp=row['expected_degrees'][key]; got=row['computed_from_expected_degrees'][key]
    return 'matches' if abs(((got-exp+180)%360)-180) <= tol else 'mismatch'

def build(date: str):
    replay=json.load(open(REPLAY))
    rows=[]
    for row in replay['rows']:
        rows.append({
            'source_id': row['source_id'], 'url': row['url'],
            'trisphuta_status': status(row,'trisphuta'),
            'chatusphuta_status': status(row,'chatusphuta'),
            'panchasphuta_status': status(row,'panchasphuta'),
            'candidate_causes': ['formula_variant','source_transcription','chatusphuta_catusphuta_naming','incomplete_input_settings'],
            'next_evidence_owner': 'worked_example_collection',
            'next_evidence': ['raw scan/page capture','complete example input','independent translation/transcription check','legal external replay'],
            'upgrade_status': 'not_oracle_ready',
            'claim_boundary': 'Mismatch queue only; do not tune formulas or upgrade Prashna truth from this packet.',
        })
    sources=[
        {'source_id':'vedastro_prasna_marga_ch5_sphuta_example','url':'https://vedastro.org/book/PrasnaMarga/Chapter5','source_role':'numeric_candidate','upgrade_status':'candidate_not_oracle'},
        {'source_id':'internet_archive_prasna_marga_bv_raman_sphuta_fragment','url':'https://archive.org/details/PrasnaMarga/','source_role':'public_formula_numeric_fragment_candidate','upgrade_status':'candidate_not_oracle'},
    ]
    return {'scope':'prashna_sphuta_mismatch_arbitration','created_at':date,'status':'arbitration_queue_ready','claim_status':'open_queue','production_tuning_allowed':False,'truth_matrix_allowed':False,'summary':{'mismatch_count':sum(r['chatusphuta_status']=='mismatch' or r['panchasphuta_status']=='mismatch' for r in rows),'source_candidate_count':len(sources),'oracle_ready_count':0},'rows':rows,'source_candidates':sources,'boundary':'Queue records candidate causes; closure requires raw source and replay evidence.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--date',default='2026-07-20'); args=ap.parse_args()
    data=build(args.date); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True))
if __name__=='__main__': main()
