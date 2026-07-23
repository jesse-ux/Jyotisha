import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'references/oracle/hard_gap_source_hunt_2026_07_23.json'
def test_hard_gap_source_hunt_does_not_upgrade_oracles():
 data=json.loads(subprocess.check_output(['python3','scripts/hard_gap_source_hunt_2026_07_23.py'],cwd=ROOT,text=True))
 assert data['claim_status']=='source_hunt_only'
 assert data['truth_matrix_allowed'] is False
 assert data['summary']['ready_numeric_oracle_count']==0
 assert data['summary']['timing_holdout_status']=='blocked_until_independent_human_labels'
def test_hard_gap_source_hunt_names_kp_gulika_and_tajika_blockers():
 data=json.loads(PACKET.read_text())
 domains={r['domain'] for r in data['rows']}
 assert {'KP 12 cusp exact longitude','Gulika/Sphuta','Prashna/Sphuta','Tajika/Saham','KP timing/outcome oracle'} <= domains
 gulika=[r for r in data['rows'] if r['domain']=='Gulika/Sphuta'][0]
 assert {'place','timezone','coordinates'} <= set(gulika['missing_for_oracle'])
 assert data['boundary'].startswith('No source found')
