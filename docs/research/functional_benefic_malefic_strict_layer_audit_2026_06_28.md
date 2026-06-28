# Functional Benefic/Malefic Strict Layer Audit - 2026-06-28

## Scope

This audit records the first strict-workflow integration of the Functional Benefic/Malefic hard constraint from `AGENTS.md`.

## Implementation

Strict workflow evidence now exposes:

```json
{
  "functional_benefic_malefic": {
    "status": "used | blocked",
    "ascendant": "Leo",
    "functional_benefics": ["Sun", "Mars", "Jupiter"],
    "functional_malefics": ["Mercury", "Moon", "Saturn", "Venus"],
    "functional_neutrals": [],
    "yogakarakas": ["Mars"],
    "owned_houses": {"Sun": [1]},
    "source": "strict_functional_benefic_malefic_v1"
  }
}
```

## Boundary

- This is a functional house-lord role layer, not a natural benefic/malefic table.
- It is exposed as evidence and secondary context.
- It does not directly lift dominant labels.
- If chart ascendant or planets are unavailable, the layer remains `blocked` in evidence but does not pollute legacy secondary-context tests.

## Why It Matters

The project hard constraint says high-rigor timing or outcome readings must not judge benefic/malefic effects from natural planetary quality alone. This bridge makes the functional role layer visible to strict workflows so later adjudicators and Technique Audit Tables can use it.

## Verification

- `tests/test_mcp_strict_workflow_functional_layer.py`
- `tests/test_mcp_strict_workflow_relationship.py`
- `tests/test_mcp_strict_workflow_career.py`
- `tests/test_mcp_strict_workflow_finance.py`
