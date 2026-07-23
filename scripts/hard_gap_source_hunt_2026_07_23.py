#!/usr/bin/env python3
"""Record source-hunt status for remaining hard oracle gaps."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'references/oracle/hard_gap_source_hunt_2026_07_23.json'
ROWS=[
 {'domain':'KP 12 cusp exact longitude','source_id':'roxyapi_kp_catalog','url':'https://roxyapi.com/docs/guides/kp','useful_fields':['getKpCusps returns 12 Placidus cusps','star/sub/sub-sub hierarchy','KP ayanamsa lookup','ruling planets interval'], 'status':'api_surface_candidate', 'missing_for_oracle':['API key/terms','pinned response raw/hash','public worked-example expected table']},
 {'domain':'KP 12 cusp exact longitude','source_id':'ajmerastro_kp_tools','url':'https://www.ajmerastro.com/en/kp-astrology','useful_fields':['12 cusps','A-D significators','ruling planets','249 sub-lord table'], 'status':'tool_surface_candidate', 'missing_for_oracle':['machine-readable raw','version identity','public fixed input/output packet']},
 {'domain':'KP 12 cusp exact longitude','source_id':'scribd_kp_planets_and_cusps','url':'https://fr.scribd.com/doc/193725310/KP-Planets-and-Cusps','useful_fields':['planet/cusp table candidate','sub/sub-sub text surface'], 'status':'copyright_limited_table_candidate', 'missing_for_oracle':['complete legally usable table extraction','birth input/timezone/ayanamsa','local replay raw/hash']},
 {'domain':'KP timing/outcome oracle','source_id':'internet_archive_kp_cuspal_system','url':'https://archive.org/stream/Book1969LiewellynAToZHoroscopeMakerAndDelineatorKPRedIt/Jyotish_Key%20to%20Learn_K.P.%20cuspal%20system_S.P.%20Khullar_djvu.txt','useful_fields':['KP event reasoning text','sub/sub-sub timing examples'], 'status':'text_reference_candidate', 'missing_for_oracle':['structured 12-cusp expected rows','blind outcome labels','negative windows']},
 {'domain':'Gulika/Sphuta','source_id':'coursehero_gulika_2014_fragment','url':'https://www.coursehero.com/file/69722801/387858709-Gulika-and-Mandi-pdftxt/','useful_fields':['2014-05-11 date','sunrise 06:20','Gulika rise 16:02','Gulika longitude candidate 15F24'], 'status':'partial_numeric_candidate_still_blocked', 'missing_for_oracle':['place','timezone','coordinates','copyright-safe provenance','local replay raw/hash']},
 {'domain':'Prashna/Sphuta','source_id':'vedastro_prasna_marga_ch5','url':'https://vedastro.org/blog/Prasna-Marga-Chapter-5-Mathematical-Foundations.html','useful_fields':['Prashna mathematical foundations','partial ascendant example','sphuta context'], 'status':'partial_formula_candidate', 'missing_for_oracle':['question time/place','complete expected Sphuta outputs','local replay raw/hash']},
 {'domain':'Tajika/Saham','source_id':'naksham_varshaphal_calculator','url':'https://nakshamastro.com/astrohub/vedic/varshaphal','useful_fields':['Varshaphal calculator surface','Muntha','year lord','Tajika yogas','Sahams'], 'status':'calculator_surface_candidate', 'missing_for_oracle':['pinned raw export','source version','expected Saham longitude','license/API terms']},
]
def build():
 return {'scope':'hard_gap_source_hunt','created_at':'2026-07-23','claim_status':'source_hunt_only','truth_matrix_allowed':False,'production_tuning_allowed':False,'rows':ROWS,'summary':{'source_count':len(ROWS),'ready_numeric_oracle_count':0,'partial_numeric_candidate_count':1,'timing_holdout_status':'blocked_until_independent_human_labels'},'next_actions':['If RoxyAPI key/terms are available, capture pinned KP /cusps raw for a public fixed chart and compare against VedicAstro observation only.','For Gulika fragment, locate place/timezone or keep candidate blocked.','For Tajika/Saham, require solar return input plus expected Saham longitude before replay.','For timing/rectification, freeze independent human labels before blind ranking.'],'boundary':'No source found in this pass satisfies complete input + expected numeric values + replay raw/hash. All hard gaps remain blocked or candidate-only.'}
def main():
 data=build(); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(data,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
