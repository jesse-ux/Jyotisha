#!/usr/bin/env python3
"""Audit three reference-only files from the guarded Prashna worktree."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'references/oracle/reference_only_line_audit_v2_2026_07_23.json'
BASE='redacted_local_guarded_prashna_worktree'
ROWS=[
 {'relative_path':'scripts/gulika.py','decision':'reference_only_current_repo_newer','useful_for':['Ghatika end table wording','Prasna Marga rule boundary','Swiss-Ephemeris replay shape'],'why_not_copy':'Current repo already has Gulika implementation/tests; old file lacks current oracle/claim gates.','convert_to':['formula registry note only','no runtime migration']},
 {'relative_path':'scripts/tajika.py','decision':'reference_only_current_repo_newer','useful_for':['Saham operand resolver','day/night formula switch','Muntha annual sign convention'],'why_not_copy':'Current repo already has Tajika/Saham code and closure packets; old file is broad implementation without current evidence gates.','convert_to':['Saham day/night registry cross-check','no runtime migration']},
 {'relative_path':'docs/benchmark/tajika_sahams_annual_benchmark_dashboard.json','decision':'reference_only_benchmark_context','useful_for':['annual benchmark dashboard schema','Tajika/Saham closure status language'],'why_not_copy':'Benchmark values are not an independent public numeric oracle and need provenance/hash review before tests.','convert_to':['dashboard schema reference','not numeric oracle']},
]
def build():
 return {'scope':'reference_only_line_audit_v2','created_at':'2026-07-23','claim_status':'fragment_audit_only','truth_matrix_allowed':False,'production_tuning_allowed':False,'source_root':BASE,'rows':ROWS,'summary':{'audited_file_count':len(ROWS),'runtime_migration_count':0,'registry_or_test_candidate_count':2,'numeric_oracle_ready_count':0},'boundary':'The three guarded-worktree reference-only files contain useful formula/schema context but no directly reusable runtime code or numeric oracle packet.'}
def main():
 data=build(); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(data,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
