# Real Case Batch1 Runtime Retrieval Audit 2026-07-03

## Scope

Promote already-classified `real_case_studies_batch1` from queue-only visibility into a callable local retrieval layer without treating it as primary truth.

## Runtime Wiring

`mcp_server._existing_interpretation_source_pack()` now exposes:

- `real_case_calibration_layer.status = queued`
- `real_case_calibration_layer.index_status = available`
- `real_case_calibration_layer.batch_id = real_case_studies_batch1`
- domain buckets: `career`, `finance`, `relationship`, `health`, `rectification`, `timing`
- source refs from `references/real_case_studies` and `docs/benchmark`

`real_case_calibration.status` remains `blocked` because matching-case attachment and external MEVG calibration are still required before confidence can be lifted.

## Cleanup Boundary

Duplicate / obsolete / quarantine files were not physically deleted in this patch. They remain hard-excluded from runtime truth by the inventory gate and source-pack tests. This avoids deleting local research history while preventing contamination of the interpretation chain.

## Verification

Passed:

```bash
python3 -m pytest -q \
  tests/test_interpretation_source_inventory_gate.py \
  tests/test_interpretation_source_advanced_pipeline_contract.py \
  tests/test_interpretation_source_next_phase_contract.py \
  tests/test_mcp_strict_workflow_career.py \
  tests/test_mcp_strict_workflow_finance.py \
  tests/test_mcp_strict_workflow_relationship.py
```
