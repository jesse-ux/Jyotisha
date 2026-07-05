# Open Source Batches Runtime Reference Audit 2026-07-03

## Scope

Advance the next queued open-source reference batches without turning them into primary truth:

- `rishi_ai_mcp_batch1`
- `vedic_astro_skills_batch1`

Also expose the remaining external gaps requested by the user:

- VedAstro official default closure
- external oracle parity
- install / usage path slimming

## Runtime Wiring

`mcp_server._existing_interpretation_source_pack()` now exposes:

- `rishi_ai_mcp_batch1_layer`
  - status: `available`
  - source refs: 16
  - mapped domains: career, finance, relationship, children, health, full_reading
  - runtime truth status: `not_primary_truth`

- `vedic_astro_skills_batch1_layer`
  - status: `available`
  - source refs: 8
  - mapped domains: core, reader_validation, career, relationship, rectification, calculator
  - runtime truth status: `not_primary_truth`

- `external_closure_gap_layer`
  - `vedastro_official.status = blocked`
  - `oracle_parity.status = blocked`
  - `install_usage_path.status = needs_slimming`

## Queue Update

Completed as visible reference layers:

- `real_case_studies_batch1`
- `rishi_ai_mcp_batch1`
- `vedic_astro_skills_batch1`

Remaining queue:

- `references_batch2`
- `vedastro_official_default_closure`
- `external_oracle_parity_batch`
- `install_usage_path_slimming`

## Classification Boundary

Open-source sources remain classified as `open_source_reference` unless they were already governed runtime refs such as existing QA / reader / yoga resources. This prevents new open-source material from overriding local strict rules or oracle-calibrated calculations.

## Verification

Passed:

```bash
python3 -m pytest -q \
  tests/test_interpretation_source_inventory_gate.py \
  tests/test_interpretation_source_next_phase_contract.py \
  tests/test_interpretation_source_advanced_pipeline_contract.py \
  tests/test_mcp_strict_workflow_career.py \
  tests/test_mcp_strict_workflow_finance.py \
  tests/test_mcp_strict_workflow_relationship.py
```
