# Dignity Guardrail v1 Boundary Audit - 2026-06-28

## What Landed

- `dignity_guardrail` has been added to `relationship` and `finance` strict workflows.
- The guardrail reads only D1 `chart.planets.status`.
- Only route-relevant planets may affect the guardrail result.
- Score impact is bounded to a single `-5 | 0 | +5`.
- The previous whole-chart dignity broadcast has been removed from `_derive_event_judgement`.

## What Did Not Land

- No D9 dignity scoring
- No D10 dignity scoring
- No Vimsopaka dignity scoring
- No `dominant_label` lifting from dignity
- No merge with Functional Benefic/Malefic logic
- No multi-planet cumulative dignity scoring

## Verified Boundary

The current implementation now enforces these behaviors:

1. non-relevant planets are ignored for route scoring
2. mixed relevant `NEECHA_BHANGA` and `GREAT_ENEMY` signals collapse to `conflict`
3. `conflict` does not directly change event labels
4. `relationship` and `finance` retain their pre-existing label logic
5. dignity only modifies:
   - `event_judgement.score`
   - `event_judgement.secondary_context`
   - `confidence_cap` when a conflict is present

## Why This Is Safer Than The Previous State

The previous implementation scanned all natal planets and added or subtracted score directly from chart status strings. That allowed unrelated dignity states to alter relationship or finance verdicts.

The new guardrail restores strict-workflow discipline by making dignity:

- domain-aware
- bounded
- auditable
- non-authoritative

## Known Follow-Ups

1. Repair divisional dignity data-flow separately in `scripts/jyotish_engine.py`
   - current divisional dignity calculations still need an isolated follow-up review
2. Build `functional_role_guardrail`
   - this should consume the already existing Functional Benefic/Malefic layer
3. Decide later whether `GREAT_FRIEND` should receive context-only semantics
4. Consider whether a route-specific audit table row should be emitted for dignity guardrail status

## Verification

Executed:

- `python3 -m pytest tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_finance.py -q`

Result:

- `25 passed`
