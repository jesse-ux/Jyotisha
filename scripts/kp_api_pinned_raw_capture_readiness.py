#!/usr/bin/env python3
"""KP API pinned raw capture readiness for RoxyAPI/AjmerAstro/AstrologyAPI-like services."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'references/oracle/kp_api_pinned_raw_capture_readiness_2026_07_23.json'
ROWS=[
 {'provider':'RoxyAPI','url':'https://roxyapi.com/docs/guides/kp','status':'key_terms_version_required','needed_before_call':['API key','plan/terms permission for raw archival','endpoint version','ayanamsa enum','node mode','house system','canonical request'], 'target_fields':['12 cusps longitude','star lord','sub lord','sub-sub lord','ruling planets']},
 {'provider':'AstrologyAPI','url':'https://www.astrologyapi.com/docs/kp-house-cusps','status':'key_terms_version_required','needed_before_call':['API key','documentation version','request schema','response retention permission','canonical request'], 'target_fields':['house cusps','sign/star/sub hierarchy']},
 {'provider':'AjmerAstro','url':'https://www.ajmerastro.com/en/kp-astrology','status':'tool_surface_no_raw_contract','needed_before_call':['machine-readable raw export','software version','terms allowing archived comparison'], 'target_fields':['12 cusps','significators','ruling planets']},
]
def build():
 return {'scope':'kp_api_pinned_raw_capture_readiness','created_at':'2026-07-23','claim_status':'blocked_until_key_terms_version','truth_matrix_allowed':False,'production_tuning_allowed':False,'providers':ROWS,'canonical_request_required':['birth/question datetime','place coordinates','timezone','ayanamsa','node mode','house system','query domain'], 'capture_contract':['request_json_sha256','raw_response_sha256','provider/version metadata','terms snapshot URL/date','normalized schema fingerprint','comparison only; no truth upgrade'], 'boundary':'Do not call or archive paid/hosted KP API raw until key, terms, version and retention permission are known.'}
def main():
 data=build(); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(data,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
