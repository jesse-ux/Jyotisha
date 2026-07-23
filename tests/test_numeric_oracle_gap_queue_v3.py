import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'references/oracle/numeric_oracle_gap_queue_v3_2026_07_23.json'
def test_numeric_oracle_gap_queue_v3_blocks_truth_upgrade():
 data=json.loads(subprocess.check_output(['python3','scripts/numeric_oracle_gap_queue_v3.py'],cwd=ROOT,text=True))
 assert data['claim_status']=='candidate_queue'
 assert data['truth_matrix_allowed'] is False
 assert data['summary']['numeric_packet_ready_count']==0
 assert {'KP exact cusp','Sphuta/Gulika','Prashna/Sphuta','Tajika/Saham'} <= set(data['summary']['blocked_domains'])
def test_numeric_oracle_gap_queue_v3_records_partial_gulika_candidate_only():
 data=json.loads(PACKET.read_text())
 partial=[r for r in data['rows'] if r['status']=='partial_numeric_candidate']
 assert len(partial)==1
 assert partial[0]['domain']=='Sphuta/Gulika'
 assert 'local replay raw/hash' in partial[0]['missing_for_packet']
 assert data['boundary'].startswith('This queue records public candidates only')
