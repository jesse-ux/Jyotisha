#!/usr/bin/env python3
"""Replay pinned Xalen shared-input formulas across public AA birth cases."""

from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from scripts.xalen_oracle_adapter import run_probe

ROOT=Path(__file__).resolve().parents[1]; SIGNS=['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']; PLANETS=['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']

def chart_input(subject:dict)->dict:
 cmd=[sys.executable,'scripts/jyotish_engine.py','chart']
 for key in ('year','month','day','hour','minute','lat','lon','tz'):cmd += [f'--{key}',str(subject[key])]
 cmd += ['--ayanamsa','lahiri','--node-mode','mean']
 done=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=60,check=False)
 if done.returncode:raise RuntimeError(done.stderr)
 chart=json.loads(done.stdout);birth=chart['birth_info'];planets=[]
 for name in PLANETS:
  p=chart['planets'][name];planets.append({'name':name,'longitude':p['lon'],'speed':p['speed'],'house':p['house']})
 return {'jd':birth['julian_day'],'day_fraction':(subject['hour']+subject['minute']/60)/24,'asc_sign_idx':SIGNS.index(chart['ascendant']['sign']),'planets':planets}

def run_batch(manifests:list[Path],limit:int=5,mode:str='shared_input')->dict:
 cases=[]
 for path in manifests:
  for case in json.loads(path.read_text(encoding='utf-8')).get('cases') or []:
   subject=case['subject'];source=subject.get('birth_source') or {}
   if source.get('time_accuracy_rating')!='AA' or any(c['case_id']==case['case_id'] for c in cases):continue
   payload=chart_input(subject);payload['mode']=mode;probe=run_probe(payload);raw=probe['raw'];digest=hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(',',':')).encode()).hexdigest()
   cases.append({'case_id':case['case_id'],'name':subject['name'],'birth_source':source,'input_mode':mode,'input':payload,'xalen_raw':raw,'raw_sha256':digest})
   if len(cases)>=limit:break
  if len(cases)>=limit:break
 return {'scope':'xalen_multi_public_case_replay','mode':mode,'case_count':len(cases),'source_commit':'cc6edbec1f748ebdc4950ae6198f575c5ada73fa','license':'Apache-2.0','cases':cases,'boundary':'Shared mode isolates formulas; independent mode recomputes seven-planet ephemeris while retaining shared houses.'}

def main()->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--limit',type=int,default=5);p.add_argument('--mode',choices=['shared_input','independent_ephemeris'],default='shared_input');p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=run_batch([ROOT/'references/real_case_calibration/replay_manifest.json',ROOT/'references/real_case_calibration/replay_manifest_probe3_v2.json'],a.limit,a.mode);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps({'case_count':r['case_count'],'mode':r['mode']},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
