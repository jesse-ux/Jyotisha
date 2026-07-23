#!/usr/bin/env python3
"""Build numeric oracle gap queue for KP, Prashna, Tajika, Saham, Gulika and Sphuta."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'references/oracle/numeric_oracle_gap_queue_v3_2026_07_23.json'
ROWS=[
 {'domain':'KP exact cusp','source_id':'scribd_kp_planets_and_cusps','url':'https://www.scribd.com/doc/193725310/KP-Planets-and-Cusps','found_fields':['planet/cusp longitude table','rasi','star','sign lord','star lord','sub lord','sub-sub lord'],'missing_for_packet':['source page/full rows legally accessible','birth input','timezone','ayanamsa/node mode','local replay raw/hash'],'status':'candidate_numeric_table_not_packet'},
 {'domain':'KP significator workflow','source_id':'astrosage_kp_fundamental_principles','url':'https://kpastrology.astrosage.com/kp-learning-home/tutorial/chapter-2-fundamental-principles','found_fields':['sign/star/sub positions','significator removal example','sub-lord weighting note'],'missing_for_packet':['complete 12 cusp exact longitudes','event outcome oracle','negative timing windows'],'status':'workflow_reference_not_numeric_oracle'},
 {'domain':'Sphuta/Gulika','source_id':'coursehero_gulika_mandi_text','url':'https://www.coursehero.com/file/69722801/387858709-Gulika-and-Mandi-pdftxt/','found_fields':['date 2014-05-11','sunrise 06:20','Gulika rise 16:02','Gulika longitude 15F24 candidate'],'missing_for_packet':['place coordinates','timezone','house table source','copyright-safe excerpt boundary','local replay raw/hash'],'status':'partial_numeric_candidate'},
 {'domain':'Sphuta','source_id':'eastrovedica_lesson49','url':'https://www.eastrovedica.com/html/vedic_astrologylesson49.asp','found_fields':['Prana Sphuta formula','Deha Sphuta formula','Mrityu Sphuta formula'],'missing_for_packet':['complete input longitudes','expected numeric outputs','replay raw/hash'],'status':'formula_reference_not_numeric_packet'},
 {'domain':'Prashna/Sphuta','source_id':'vedastro_prasna_marga_ch5','url':'https://vedastro.org/blog/Prasna-Marga-Chapter-5-Mathematical-Foundations.html','found_fields':['Prashna Moon longitude context','example Lagna Aquarius 12°25′','Sphuta calculation context'],'missing_for_packet':['full question time/place','complete expected Sphuta outputs','local replay raw/hash'],'status':'partial_formula_candidate'},
 {'domain':'Tajika/Saham','source_id':'astrogle_sahams_varshaphala','url':'https://www.astrogle.com/astrology/important-role-of-sahams-in-varshaphala-annual-chart.html','found_fields':['Saham definition','annual chart context','Punya/Vivaha focus'],'missing_for_packet':['solar return input','planetary longitudes','expected Saham longitude','day/night convention','replay raw/hash'],'status':'formula_context_reference'},
 {'domain':'Tajika/Saham','source_id':'naksham_varshaphal_calculator','url':'https://nakshamastro.com/astrohub/vedic/varshaphal','found_fields':['calculator surface','year lord','Muntha','Tajika yogas','Sahams','Mudda Dasha'],'missing_for_packet':['pinned software identity','raw export','worked example expected values','license/API terms'],'status':'calculator_candidate_not_oracle'},
]
def build():
 return {'scope':'numeric_oracle_gap_queue_v3','created_at':'2026-07-23','claim_status':'candidate_queue','truth_matrix_allowed':False,'production_tuning_allowed':False,'rows':ROWS,'summary':{'candidate_count':len(ROWS),'numeric_packet_ready_count':0,'partial_numeric_candidate_count':sum(r['status']=='partial_numeric_candidate' for r in ROWS),'blocked_domains':sorted(set(r['domain'] for r in ROWS))},'promotion_requirements':['complete input','expected numeric values','source URL/page/line or screenshot hash','license/copyright-safe boundary','local replay raw/hash','claim gate remains non-truth until cross-source consistency'],'boundary':'This queue records public candidates only. It does not upgrade KP, Prashna, Tajika, Saham, Gulika or Sphuta truth status.'}
def main():
 data=build(); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(data,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
