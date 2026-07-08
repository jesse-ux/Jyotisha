# Functional Benefic/Malefic Bridge Audit - 2026-06-28

## Scope

This pass promotes the previously untracked `scripts/oracle_functional_benefics.py`
fragment into a reusable strict-workflow layer.

## What Changed

- Added `<repo>/scripts/functional_benefics.py` as the single source for functional benefic/malefic classification by Lagna.
- Converted `<repo>/scripts/oracle_functional_benefics.py` into a CLI wrapper around that module.
- Routed MCP strict workflows through the shared module.
- Routed full-reading prompt-pack and API prompt-pack snapshots through the same shared module.

## Contract

The bridge requires only a valid ascendant sign.

It returns:

- `status`
- `ascendant`
- `functional_benefics`
- `functional_malefics`
- `functional_neutrals`
- `yogakarakas`
- `owned_houses`
- `effect_on_confidence`
- `source`

## Boundary

- This layer classifies functional house-lord roles.
- It does not replace natural benefic/malefic assessment.
- It does not directly force event labels.
- It must appear in strict workflow evidence and Technique Audit Table outputs for high-rigor readings.

## Regression Coverage

- `<repo>/tests/test_mcp_strict_workflow_functional_layer.py`
- `<repo>/tests/test_cli_smoke.py`
- `<repo>/tests/test_api_server_security.py::test_chart_ai_prompt_pack_exposes_functional_benefic_malefic_layer`
