# Marriage Adjudicator Jaimini Bridge v1 Audit (2026-06-28)

## Scope

This pass adds the smallest Jaimini bridge to the relationship strict workflow.

It fixes only `label-lift failure` for legal-marriage cases.

## Implemented Behavior

The relationship event judgement now preserves legacy fields:

- `score`
- `verdict`
- `primary_drivers`

and adds:

- `dominant_label`
- `secondary_context`

## Boundary

v1 may lift only:

- `legal_marriage`

v1 does not lift:

- `relationship_formation`
- `public_formalization`

## Jaimini Bridge

`present_evidence.jaimini_marriage_support` has:

- `level`: `none`, `weak`, or `moderate`
- `signals`
- `source`: `jaimini_bridge_v1`

`strong` is intentionally not available in v1.

## Hard Gates

`dominant_label = legal_marriage` requires:

- D9 present
- UL present
- Vimshottari present
- Narayana present
- Vivah Saham or marriage convergence present
- moderate Jaimini support

If a hard gate is missing, Jaimini evidence remains context-only.

## Verification

Commands:

```bash
python3 -m pytest tests/test_mcp_strict_workflow_relationship.py -q
python3 -m pytest tests/test_mcp_strict_workflow_finance.py -q
```

Observed:

- relationship: `2 passed`
- finance: `16 passed`
