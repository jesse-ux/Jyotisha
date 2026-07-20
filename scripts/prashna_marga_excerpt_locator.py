#!/usr/bin/env python3
"""Locate short Prasna Marga Sphuta source windows by IA text URLs."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "references/oracle/prashna_marga_raw_capture_packet_2026_07_20.json"
OUT = ROOT / "references/oracle/prashna_marga_excerpt_locator_2026_07_20.json"
TERMS = ["Trisphuta", "Chatusphuta", "Catusphuta", "Panchasphuta", "Gulika"]

def sha(s: str) -> str: return hashlib.sha256(s.encode('utf-8','ignore')).hexdigest()
def fetch(url: str) -> str:
    req=Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urlopen(req,timeout=25) as r: return r.read().decode('utf-8','ignore')

def locate(text: str, source_id: str, file_name: str, url: str):
    lines=text.splitlines()
    for i,line in enumerate(lines):
        if any(t.lower() in line.lower() for t in TERMS):
            start=max(0,i-2); end=min(len(lines),i+3)
            window='\n'.join(lines[start:end])
            compact=' '.join(window.split())[:240]
            return {'source_id':source_id,'file_name':file_name,'download_url':url,'matched_line':i+1,'line_start':start+1,'line_end':end,'matched_terms':[t for t in TERMS if t.lower() in window.lower()],'window_hash':sha(window),'short_context':compact}
    return None

def build(date: str):
    src=json.load(open(SRC)); wins=[]; blocked=[]
    for item in src['internet_archive_items']:
        for f in item['files']:
            if f['format']!='DjVuTXT': continue
            try:
                hit=locate(fetch(f['download_url']), item['identifier'], f['name'], f['download_url'])
                if hit: wins.append(hit)
                else: blocked.append({'source_id':item['identifier'],'file_name':f['name'],'status':'locator_terms_not_found'})
            except Exception as e:
                blocked.append({'source_id':item['identifier'],'file_name':f['name'],'status':'fetch_failed','error':type(e).__name__})
    return {'scope':'prashna_marga_excerpt_locator','created_at':date,'status':'excerpt_locator_ready','claim_status':'source_intake_only','production_tuning_allowed':False,'truth_matrix_allowed':False,'summary':{'located_window_count':len(wins),'blocked_file_count':len(blocked),'oracle_ready_count':0},'located_windows':wins,'blocked_files':blocked,'missing_for_oracle':['complete_prashna_input','raw excerpt capture','line-level transcription review','legal external replay'],'upgrade_status':'candidate_not_oracle','next_steps':['raw excerpt capture with page/line coordinates and independent transcription review','compare VedAstro vs B.V. Raman wording before formula tuning'],'boundary':'Short context and hashes only; no long copyrighted text is reproduced and no truth upgrade is allowed.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--date',default='2026-07-20'); args=ap.parse_args(); data=build(args.date); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True))
if __name__=='__main__': main()
