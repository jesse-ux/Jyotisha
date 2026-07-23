import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'references/oracle/reference_only_line_audit_v2_2026_07_23.json'
def test_reference_only_line_audit_v2_blocks_runtime_copy():
 data=json.loads(subprocess.check_output(['python3','scripts/reference_only_line_audit_v2.py'],cwd=ROOT,text=True))
 assert data['claim_status']=='fragment_audit_only'
 assert data['summary']['runtime_migration_count']==0
 assert data['summary']['numeric_oracle_ready_count']==0
 assert data['truth_matrix_allowed'] is False
def test_reference_only_line_audit_v2_keeps_gulika_and_tajika_as_registry_context():
 data=json.loads(PACKET.read_text())
 rows={r['relative_path']:r for r in data['rows']}
 assert 'Ghatika end table wording' in rows['scripts/gulika.py']['useful_for']
 assert 'Saham operand resolver' in rows['scripts/tajika.py']['useful_for']
 assert rows['docs/benchmark/tajika_sahams_annual_benchmark_dashboard.json']['convert_to']==['dashboard schema reference','not numeric oracle']
