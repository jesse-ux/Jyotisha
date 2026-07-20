#!/usr/bin/env python3
"""Pin Internet Archive Prasna Marga source metadata for later raw excerpt capture."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "references/oracle/prashna_marga_raw_capture_packet_2026_07_20.json"

ITEMS = [
    {
        'identifier':'PrasnaMargaBVR','title':'Prasna Marga - Dr. BV Raman','metadata_url':'https://archive.org/metadata/PrasnaMargaBVR',
        'files':[{'name':'Prasna Marga 1_djvu.txt','format':'DjVuTXT','sha1':'bed3491a79ca5039409dac7fd62e386f7de55a47','download_url':'https://archive.org/download/PrasnaMargaBVR/Prasna%20Marga%201_djvu.txt'}, {'name':'Prasna Marga 1.pdf','format':'Text PDF','sha1':'86839fc2d13509309ec3a14a160c861bb223d844','download_url':'https://archive.org/download/PrasnaMargaBVR/Prasna%20Marga%201.pdf'}]
    },
    {
        'identifier':'prasna-marga-part-2-by-bv-raman','title':'Prasna Marga Part 2 By BV Raman','metadata_url':'https://archive.org/metadata/prasna-marga-part-2-by-bv-raman',
        'files':[{'name':'Prasna Marga Part 2 by BV Raman_djvu.txt','format':'DjVuTXT','sha1':'17c432465520ef75bde7a2c4fa167ff119664666','download_url':'https://archive.org/download/prasna-marga-part-2-by-bv-raman/Prasna%20Marga%20Part%202%20by%20BV%20Raman_djvu.txt'}]
    },
]

def digest(obj): return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def build(date):
    items=[]
    for it in ITEMS:
        row={**it,'source_metadata_hash':'','upgrade_status':'candidate_not_oracle','claim_boundary':'Metadata/file hash pin only; no book text is vendored and no numeric truth is upgraded.'}
        row['source_metadata_hash']=digest(row)
        items.append(row)
    return {'scope':'prashna_marga_raw_capture_packet','created_at':date,'status':'raw_capture_metadata_ready','claim_status':'source_intake_only','production_tuning_allowed':False,'truth_matrix_allowed':False,'summary':{'ia_item_count':len(items),'pinned_file_count':sum(len(i['files']) for i in items),'oracle_ready_count':0},'field_locator_terms':['Trisphuta','Chatusphuta','Catusphuta','Panchasphuta','Gulika'],'internet_archive_items':items,'next_steps':['raw excerpt capture around locator terms with page/line coordinates','compare B.V. Raman scan vs VedAstro transcription','only then classify formula_variant vs source_transcription'],'boundary':'Capture metadata only; long copyrighted text is not reproduced.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--date',default='2026-07-20'); args=ap.parse_args(); data=build(args.date); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True))
if __name__=='__main__': main()
