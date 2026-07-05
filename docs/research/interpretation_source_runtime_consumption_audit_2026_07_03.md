# Interpretation Source Runtime Consumption Audit 2026-07-03

## Scope

Follow-up to the existing inventory gate and advanced pipeline contract. This audit checks whether already-classified interpretation source layers are consumed by strict workflows without rebuilding the inventory system.

## Result

- `scripts/interpretation_source_inventory_gate.py`: pass.
- Candidate pool: 956.
- Unclassified candidates: 0.
- Source pack status: used.
- Runtime strict workflows now assert consumption of the promoted batch2 topic layers via secondary context markers.

## Consumed Runtime Markers

The career, finance, and relationship strict workflow tests now require:

- `dasha_timing_layer_used`
- `varga_strength_layer_used`
- `annual_special_layer_context`
- `modifier_obstacle_layer_used`

These markers prove that the batch2 topic layer is not merely visible in the source pack; it is carried into adjudication context.

## Tests Updated

- `tests/test_mcp_strict_workflow_career.py`
- `tests/test_mcp_strict_workflow_finance.py`
- `tests/test_mcp_strict_workflow_relationship.py`

The tests no longer require `secondary_context` to equal an old fixed list. They now require the original business signals plus the promoted source-layer markers.

## Verification

Passed:

```bash
python3 -m pytest -q \
  tests/test_mcp_strict_workflow_career.py \
  tests/test_mcp_strict_workflow_finance.py \
  tests/test_mcp_strict_workflow_relationship.py \
  tests/test_interpretation_source_inventory_gate.py \
  tests/test_interpretation_source_advanced_pipeline_contract.py \
  tests/test_interpretation_source_next_phase_contract.py \
  tests/test_interpretation_source_core5_strict_visibility.py
```

Result: 94 passed.

Also passed: `git diff --check`.

## Boundary

No runtime source-pack rebuild was done. No quarantined or draft sources were promoted.

`python3 scripts/run_quality_gate.py --profile quick ...` exceeded the 120s command timeout in this session, so the quick gate was not used as completion evidence.
