import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'references/oracle/kp_api_pinned_raw_capture_readiness_2026_07_23.json'
def test_kp_api_capture_readiness_requires_key_terms_version():
 data=json.loads(subprocess.check_output(['python3','scripts/kp_api_pinned_raw_capture_readiness.py'],cwd=ROOT,text=True))
 assert data['claim_status']=='blocked_until_key_terms_version'
 assert data['truth_matrix_allowed'] is False
 assert 'request_json_sha256' in data['capture_contract']
 assert 'terms snapshot URL/date' in data['capture_contract']
def test_kp_api_capture_readiness_names_all_target_providers():
 data=json.loads(PACKET.read_text())
 providers={p['provider']:p for p in data['providers']}
 assert {'RoxyAPI','AstrologyAPI','AjmerAstro'} <= set(providers)
 assert '12 cusps longitude' in providers['RoxyAPI']['target_fields']
 assert data['boundary'].startswith('Do not call or archive')
