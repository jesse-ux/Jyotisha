#!/usr/bin/env python3
"""Run installed PyJHora Sphuta OSS case as isolated observation."""
from __future__ import annotations
import argparse, contextlib, hashlib, importlib.metadata as md, io, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'references/oracle/prashna_sphuta_oss_case_probe_2026_07_20.json'

def h(o): return hashlib.sha256(json.dumps(o,ensure_ascii=False,sort_keys=True,default=str).encode()).hexdigest()

def build(date):
    rows=[]; meta={}
    try:
        captured_stdout = io.StringIO()
        captured_stderr = io.StringIO()
        with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(captured_stderr):
            import jhora
            from jhora.panchanga import drik
            from jhora.horoscope.chart import sphuta
        try: dist=md.metadata('jhora')
        except md.PackageNotFoundError: dist=md.metadata('PyJHora')
        meta={'package':dist.get('Name'),'version':dist.get('Version'),'license':dist.get('License') or 'AGPL detected from package metadata text','module_file':jhora.__file__,'captured_import_stdout_hash':h(captured_stdout.getvalue()),'captured_import_stderr_hash':h(captured_stderr.getvalue())}
        dob=drik.Date(1996,12,7); tob=(10,34,0); place=drik.Place('Chennai',13.0878,80.2785,5.5)
        for field,fn,expected in [('tri_sphuta',sphuta.tri_sphuta,'Pisces 20° 47’ 20"'),('chatur_sphuta',sphuta.chatur_sphuta,'Scorpio 12° 21’ 15"'),('pancha_sphuta',sphuta.pancha_sphuta,'Aries 22° 54’ 29"')]:
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    got=fn(dob,tob,place,divisional_chart_factor=1)
                rows.append({'field':field,'status':'observed','raw_result':got,'expected_from_oss_case':expected})
            except Exception as e:
                rows.append({'field':field,'status':'runtime_error','error':type(e).__name__,'expected_from_oss_case':expected})
    except Exception as e:
        meta={'package':'jhora','import_error':type(e).__name__}
        for field in ['tri_sphuta','chatur_sphuta','pancha_sphuta']: rows.append({'field':field,'status':'runtime_error','error':'jhora_import_failed'})
    data={'scope':'prashna_sphuta_oss_case_probe','created_at':date,'status':'oss_probe_ready','claim_status':'tooling_observation_only','production_tuning_allowed':False,'truth_matrix_allowed':False,'oracle_ready':False,'license_boundary':'agpl_observation_only_do_not_vendor','case':{'source':'jhora.tests.pvr_tests.sphuta_tests','dob':'1996-12-07','tob':'10:34:00','place':'Chennai 13.0878,80.2785 +05:30'},'package_metadata':meta,'rows':rows,'boundary':'Runs installed OSS package only; no AGPL implementation is copied and no oracle truth is upgraded.'}
    data['raw_hash']=h({'meta':meta,'rows':rows})
    return data

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--date',default='2026-07-20'); args=ap.parse_args(); data=build(args.date); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True))
if __name__=='__main__': main()
