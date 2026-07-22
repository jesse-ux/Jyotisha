#!/usr/bin/env python3
"""Expected-value-only replay readiness for Prashna Sphuta candidates."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from scripts.prashna_sphuta import calculate_sphuta_evidence

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "references/oracle/prashna_numeric_oracle_packet_queue_2026_07_20.json"
OUT = ROOT / "references/oracle/prashna_sphuta_candidate_replay_readiness_2026_07_20.json"

PAT = re.compile(r"(?P<sign>\d+)s\s*(?P<deg>\d+)°(?:\s*(?P<min>\d+)')?(?:\s*(?P<sec>\d+)\")?")

def parse_dms(value: str) -> float:
    m = PAT.search(value)
    if not m: raise ValueError(value)
    sign=int(m.group('sign')); deg=int(m.group('deg')); minute=int(m.group('min') or 0); sec=int(m.group('sec') or 0)
    return (sign*30 + deg + minute/60 + sec/3600) % 360

def close(a,b,tol=0.02): return abs(((a-b+180)%360)-180) <= tol

def build(date: str):
    q=json.load(open(QUEUE))
    rows=[]
    for cand in q['rows']:
        ev={k:parse_dms(v) for k,v in cand['expected_values'].items()}
        calc=calculate_sphuta_evidence(ascendant_longitude=ev['lagna'], planet_longitudes={'Sun':ev['sun'],'Moon':ev['moon'],'Rahu':ev['rahu']}, gulika_longitude=ev['gulika'])
        pts=calc['points']
        computed={'trisphuta': pts['trisphuta'], 'chatusphuta': pts['catusphuta'], 'panchasphuta': pts['pancasphuta']}
        pass_formula=all(close(computed[k], ev[k]) for k in ['trisphuta','chatusphuta','panchasphuta'])
        rows.append({
            'source_id': cand['source_id'],
            'url': cand['url'],
            'expected_degrees': ev,
            'computed_from_expected_degrees': computed,
            'local_formula_consistency': 'pass' if pass_formula else 'mismatch',
            'replay_status': 'blocked_missing_complete_input',
            'missing_for_true_replay': ['question_datetime_local','location','timezone','ayanamsa','node_mode','raw_capture_hash','legal_external_replay'],
            'upgrade_status': 'not_oracle_ready',
            'claim_boundary': 'Checks arithmetic consistency of published expected values only; not a true local ephemeris replay.',
        })
    data={
        'scope':'prashna_sphuta_candidate_replay_readiness','created_at':date,'status':'replay_readiness_ready','claim_status':'tooling_observation_only',
        'production_tuning_allowed':False,'truth_matrix_allowed':False,
        'summary':{'candidate_count':len(rows),'local_formula_check_pass_count':sum(r['local_formula_consistency']=='pass' for r in rows),'oracle_ready_count':0},
        'rows':rows,'boundary':'Expected-value arithmetic only; complete Prashna inputs are still required for oracle replay.'
    }
    return data

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--date',default='2026-07-20'); args=ap.parse_args()
    data=build(args.date); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True))
if __name__=='__main__': main()
