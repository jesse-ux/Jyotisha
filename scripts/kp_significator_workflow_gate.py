#!/usr/bin/env python3
"""Build KP significator workflow gate packet from public references.

No prediction is made here. The packet defines what must exist before exact KP
significator timing can be promoted beyond observation.
"""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'references/oracle/kp_significator_workflow_gate_2026_07_23.json'
PUBLIC_SOURCES=[
 {'source_id':'astrosage_kp_fundamental_principles','url':'https://kpastrology.astrosage.com/kp-learning-home/tutorial/chapter-2-fundamental-principles','useful_for':['star_lord_sequence','sub_lord_sequence'],'license_boundary':'public reference; do not copy implementation'},
 {'source_id':'onlinejyotish_kp_horoscope_tool','url':'https://www.onlinejyotish.com/free-astrology/kp-horoscope.php','useful_for':['cusp_details','significators','ruling_planets'],'license_boundary':'public tool surface only'},
 {'source_id':'kp_significator_table_public_pdf_index','url':'https://www.scribd.com/doc/159331923/Significator-Table','useful_for':['significator_strength_order','housewise_planetwise_table_shape'],'license_boundary':'snippet/reference only; no bulk extraction'},
 {'source_id':'kp_ruling_planets_public_reference','url':'https://paramarsh.app/patrika/kp-astrology/kp-ruling-planets','useful_for':['ruling_planets_workflow','rp_crosscheck'],'license_boundary':'public reference; cite only'},
]
WORKFLOW_STEPS=[
 {'step':'exact_cusp_raw','requires':['12 cusp longitude','sign lord','star lord','sub lord','sub-sub lord','ayanamsa','house system','node mode'],'current_status':'partial_observation','blocker':'only one exact longitude row and eleven label rows are public-transcribed'},
 {'step':'planetary_star_sub_raw','requires':['planet longitude','house occupancy from exact cusps','planet star/sub/sub-sub lords'],'current_status':'runtime_probe_only','blocker':'needs public numeric table replay'},
 {'step':'significator_table','requires':['A planets in stars of occupants','B occupants','C planets in stars of owners','D owners','optional weak aspect/conjunction layer'],'current_status':'workflow_contract_only','blocker':'exact cusp + planet raw oracle missing'},
 {'step':'ruling_planets','requires':['day lord','Moon sign/star/sub lord','Lagna sign/star/sub lord','query time and place'],'current_status':'workflow_contract_only','blocker':'question-time contract and worked example oracle missing'},
 {'step':'timing_outcome_oracle','requires':['event domain houses','positive event date/window','negative windows','blind ranking before seeing labels'],'current_status':'blocked_until_human_holdout','blocker':'independent labeled holdout missing'},
]
def build():
 return {'scope':'kp_significator_workflow_gate','created_at':'2026-07-23','claim_status':'calculable_displayable_public_oracle_blocked','truth_matrix_allowed':False,'production_tuning_allowed':False,'public_sources':PUBLIC_SOURCES,'workflow_steps':WORKFLOW_STEPS,'summary':{'step_count':len(WORKFLOW_STEPS),'ready_for_verified_prediction_count':0,'blocked_step_count':len(WORKFLOW_STEPS)},'display_policy':'Show KP cusp/star/sub/significator/ruling-planet layers as observation-only. Do not present event timing as verified until exact numeric oracle and holdout pass.','boundary':'KP workflow can be displayed and audited, but exact prediction/timing claims remain blocked.'}
def main():
 data=build(); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(data,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
