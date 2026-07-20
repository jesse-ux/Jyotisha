#!/usr/bin/env python3
"""Summarize Prashna/Sphuta closure chain and remaining gates."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "references/oracle/prashna_sphuta_closure_dashboard_2026_07_20.json"
CHAIN = [
 'prashna_input_contract_2026_07_20.json','prashna_numeric_oracle_packet_queue_2026_07_20.json','prashna_sphuta_candidate_replay_readiness_2026_07_20.json','prashna_sphuta_mismatch_arbitration_2026_07_20.json','prashna_marga_raw_capture_packet_2026_07_20.json','prashna_marga_excerpt_locator_2026_07_20.json','prashna_sphuta_source_comparison_matrix_2026_07_20.json','prashna_sphuta_line_review_queue_2026_07_20.json','prashna_sphuta_review_result_template_2026_07_20.json','prashna_sphuta_review_result_validation_2026_07_20.json']

def build(date):
    packets=[]
    for f in CHAIN:
        p=ROOT/'references/oracle'/f
        d=json.load(open(p)); packets.append({'path':str(p.relative_to(ROOT)),'scope':d.get('scope'),'claim_status':d.get('claim_status'),'status':d.get('status')})
    gates=[
        {'gate_id':'human_line_review','status':'blocked','evidence':'review_result_validation valid_completed_review_count == 0'},
        {'gate_id':'complete_prashna_input','status':'blocked','evidence':'candidate lacks question datetime/location/timezone/ayanamsa/node'},
        {'gate_id':'legal_external_replay','status':'blocked','evidence':'no PyJHora/other legal replay packet yet'},
        {'gate_id':'formula_or_transcription_arbitration','status':'open_queue','evidence':'Trisphuta matches; Chatusphuta/Panchasphuta mismatch'},
    ]
    return {'scope':'prashna_sphuta_closure_dashboard','created_at':date,'status':'closure_dashboard_ready','claim_status':'blocked_until_human_labels','production_tuning_allowed':False,'truth_matrix_allowed':False,'commercial_sync_status':'research_observation_only','summary':{'packet_chain_count':len(packets),'blocked_gate_count':sum(g['status']=='blocked' for g in gates),'truth_upgrade_count':0},'packet_chain':packets,'gates':gates,'forbidden_uses':['do_not_use_for_deterministic_prashna_verdict','do_not_tune_formula_from_candidate_mismatch','do_not_claim_external_oracle_ready'],'next_actions':['fill review_result_template via human/second-source review','capture complete Prashna input if a worked example is found','run legal external replay only after inputs close'],'boundary':'Dashboard only; summarizes blocked gates and does not upgrade any Prashna/Sphuta claim.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--date',default='2026-07-20'); args=ap.parse_args(); data=build(args.date); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True))
if __name__=='__main__': main()
