#!/usr/bin/env python3
"""Compare Xalen shared-input and independent VSOP87 ephemeris modes."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def compare(shared_path:Path,independent_path:Path)->dict:
 s=json.loads(shared_path.read_text(encoding='utf-8'))['raw'];i=json.loads(independent_path.read_text(encoding='utf-8'))['raw'];positions={}
 for name,a in s['effective_positions'].items():
  b=i['effective_positions'][name];delta=(b['longitude']-a['longitude']+180)%360-180;positions[name]={'shared_longitude':a['longitude'],'independent_longitude':b['longitude'],'longitude_delta_deg':delta,'speed_delta_deg_per_day':b['speed']-a['speed']}
 varga_diffs=sum(s['varga'][d][p]!=i['varga'][d][p] for d in s['varga'] for p in s['varga'][d]);av_diffs=sum(s['ashtakavarga']['bav'][p]!=i['ashtakavarga']['bav'][p] for p in s['ashtakavarga']['bav'])+(s['ashtakavarga']['sav']!=i['ashtakavarga']['sav']);shad={p:i['shadbala'][p]['total']-s['shadbala'][p]['total'] for p in s['shadbala']}
 return {'scope':'xalen_ephemeris_mode_comparison','shared_mode':s['ephemeris_mode'],'independent_mode':i['ephemeris_mode'],'independent_engine':'Xalen Almanac.default_vedic VSOP87 analytical + Xalen Lahiri','positions':positions,'maximum_absolute_longitude_delta_deg':max(abs(v['longitude_delta_deg']) for v in positions.values()),'varga_difference_count':varga_diffs,'ashtakavarga_difference_count':av_diffs,'shadbala_total_delta_virupas':shad,'boundary':'Independent mode recomputes seven planetary longitudes/speeds; house numbers remain shared input.'}

def main()->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--shared',type=Path,default=Path('references/oracle/artifacts/xalen_steve_jobs_high_rigor_raw.json'));p.add_argument('--independent',type=Path,default=Path('references/oracle/artifacts/xalen_steve_jobs_independent_ephemeris_raw.json'));p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=compare(a.shared,a.independent);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps({'max_delta':r['maximum_absolute_longitude_delta_deg'],'varga_diffs':r['varga_difference_count']},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
