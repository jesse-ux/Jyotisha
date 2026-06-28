# Isolated Asset Bridge Audit - 2026-06-28

## Scope

This audit records the first small bridge pass after the VedAstro parity matrix identified high-value local assets that were present but not fully exploited by strict adjudicators.

## Bridges

### Synastry / Ashtakoot -> relationship strict evidence

- New evidence key: `synastry_relationship_support`
- Source: `synastry_relationship_bridge_v1`
- Inputs accepted:
  - `modules.synastry.total_score`
  - `modules.synastry.is_approved` or `is_match_approved`
  - selected clean additional Kuta signals: `Vedha`, `Rajju`, `BadConstellations`
- Output levels:
  - `none`
  - `moderate`
  - `supportive`

Boundary:

- Adds at most `+5` to relationship score.
- Adds `synastry_support` to `secondary_context`.
- Does not lift `dominant_label`.
- Does not bypass D9, UL, Vimshottari, Narayana, Vivah Saham, or marriage convergence gates.

### Kakshya -> career strict evidence

- New evidence key: `kakshya_career_support`
- Source: `kakshya_career_bridge_v1`
- Inputs accepted:
  - `modules.kakshya.summary.average_strength`
- Output levels:
  - `none`
  - `supportive`
  - `obstructive`

Boundary:

- Adds `+2` for supportive career Kakshya.
- Subtracts `-2` for obstructive career Kakshya.
- Adds a secondary context flag.
- Does not lift `dominant_label` without the existing career hard gates.

### VedAstro range scan adapter summary

- Adds `event_count`.
- Adds `top_event`.
- Keeps the complete `evidence_ledger` as the source of truth.

Boundary:

- The adapter summary is convenience metadata only.
- External range scan evidence remains `oracle_only` until promoted by adjudicator tests.

## Regression Coverage

- `tests/test_mcp_strict_workflow_relationship.py`
- `tests/test_mcp_strict_workflow_career.py`
- `tests/test_vedastro_service_adapter_executor.py`

## Next Follow-Up

Build a full relationship bridge around Synastry/Ashtakoot only after real couple benchmark cases are added. This pass intentionally keeps matching evidence secondary.
