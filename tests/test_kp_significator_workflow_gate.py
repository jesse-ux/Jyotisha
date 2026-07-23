import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'references/oracle/kp_significator_workflow_gate_2026_07_23.json'
def test_kp_significator_workflow_gate_stays_blocked():
 data=json.loads(subprocess.check_output(['python3','scripts/kp_significator_workflow_gate.py'],cwd=ROOT,text=True))
 assert data['claim_status']=='calculable_displayable_public_oracle_blocked'
 assert data['truth_matrix_allowed'] is False
 assert data['summary']['ready_for_verified_prediction_count']==0
 assert {s['step'] for s in data['workflow_steps']}=={'exact_cusp_raw','planetary_star_sub_raw','significator_table','ruling_planets','timing_outcome_oracle'}
def test_kp_gate_names_required_significator_and_holdout_layers():
 data=json.loads(PACKET.read_text())
 sig=[s for s in data['workflow_steps'] if s['step']=='significator_table'][0]
 assert 'A planets in stars of occupants' in sig['requires']
 rp=[s for s in data['workflow_steps'] if s['step']=='ruling_planets'][0]
 assert 'query time and place' in rp['requires']
 assert data['display_policy'].startswith('Show KP')
