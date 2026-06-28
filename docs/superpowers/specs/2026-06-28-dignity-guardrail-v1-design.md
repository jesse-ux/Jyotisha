# Dignity Guardrail v1 Design

**Date:** 2026-06-28
**Scope:** `relationship` / `finance` strict workflow
**Status:** Approved for planning

## Goal

Bridge the newly enriched D1 dignity output into `mcp_server.py` as a narrow, domain-aware guardrail that can slightly adjust score and confidence without overriding the existing adjudicators.

## Why This Exists

The codebase now exposes richer dignity states such as `NEECHA_BHANGA`, `GREAT_FRIEND`, and `GREAT_ENEMY`, but the current `mcp_server.py` changes apply them by scanning all natal planets and adding or subtracting points globally. That breaks the existing strict-workflow boundary in two ways:

1. Unrelated planets can alter `relationship` or `finance` verdicts.
2. Dignity starts acting like a free-scoring system instead of a bounded evidence guardrail.

This design fixes that by introducing a small, explicit `dignity_guardrail` evidence block.

## Non-Goals

- Do not redesign dignity scoring across the whole engine.
- Do not use D9, D10, Vimsopaka, or any other divisional dignity in v1.
- Do not change `dominant_label`, `primary_drivers`, `wealth_promise_strength`, `jaimini_marriage_support`, or `avayogi_risk`.
- Do not merge this with Functional Benefic/Malefic logic in v1.
- Do not allow dignity to stack into large score swings.

## Source Boundary

`dignity_guardrail` may only read from:

- `full-reading.modules.chart.planets[*].status`
- `full-reading.modules.chart.ascendant.sign`

v1 must not read:

- `modules.varga_full.*.dignity`
- D9 expanded dignity
- Vimsopaka dignity layers
- any derived dignity from divisional charts

This keeps the first bridge anchored to one stable source: D1 chart status.

## Output Contract

Add the following object to `present_evidence` for `relationship` and `finance`:

```json
{
  "dignity_guardrail": {
    "route": "relationship | finance",
    "status": "ok | caution | conflict | blocked",
    "score_delta": -5 | 0 | 5,
    "source": "chart.planets.status",
    "relevant_planets": [
      {
        "planet": "Venus",
        "role": "relationship_karaka",
        "status": "落陷取消(Neecha Bhanga)",
        "dignity_code": "NEECHA_BHANGA",
        "effect": "supportive_recovery"
      }
    ],
    "ignored_planets": [
      {
        "planet": "Mars",
        "reason": "not_domain_relevant"
      }
    ],
    "conflict_flags": [],
    "notes": [
      "Only domain-relevant planets are allowed to affect score."
    ]
  }
}
```

## Route-Specific Relevant Planet Selection

### Relationship

Relevant planets:

- `7L`
- `Venus`
- `Jupiter`
- `DK` when present

Not required in v1:

- `UL-linked lord`
- public-formalization-specific planets

### Finance

Relevant planets:

- `2L`
- `11L`
- `Venus`
- `Jupiter`

Conditionally relevant:

- `10L`, but only when `career_convergence` is present

## Dignity Codes That Matter in v1

Only two dignity outcomes may affect score:

- `NEECHA_BHANGA` -> supportive recovery -> `+5`
- `GREAT_ENEMY` -> high friction -> `-5`

All other dignity states may be recorded in `relevant_planets` but must not change score:

- `EXALTED`
- `MOOLATRIKONA`
- `OWN_SIGN`
- `GREAT_FRIEND`
- `FRIEND`
- `NEUTRAL`
- `ENEMY`
- `DEBILITATED`

## Guardrail Resolution Rules

The guardrail must not stack.

Resolution order:

1. If source data required to identify route-relevant planets is missing, set:
   - `status = "blocked"`
   - `score_delta = 0`
2. If relevant planets contain both:
   - at least one `NEECHA_BHANGA`
   - at least one `GREAT_ENEMY`
   then set:
   - `status = "conflict"`
   - `score_delta = 0`
3. Else if any relevant planet has `NEECHA_BHANGA`, set:
   - `status = "caution"`
   - `score_delta = 5`
4. Else if any relevant planet has `GREAT_ENEMY`, set:
   - `status = "caution"`
   - `score_delta = -5`
5. Else set:
   - `status = "ok"`
   - `score_delta = 0`

Even if multiple relevant planets match, the maximum absolute adjustment is `5`.

## Event Judgement Integration

### Shared Rules

`dignity_guardrail` may affect only:

- `event_judgement.score`
- `event_judgement.secondary_context`
- `confidence_cap` when `status == "conflict"`

`dignity_guardrail` may not affect:

- `dominant_label`
- `primary_drivers`
- `wealth_promise_strength`
- `jaimini_marriage_support`
- `avayogi_risk`

### Relationship Integration

Allowed `secondary_context` additions:

- `dignity_supportive_recovery`
- `dignity_high_friction`
- `dignity_conflict`

Score change:

- add `score_delta` once

### Finance Integration

Allowed `secondary_context` additions:

- `dignity_supportive_recovery`
- `dignity_high_friction`
- `dignity_conflict`

Score change:

- add `score_delta` once

This must not change the existing `income_growth` vs `public_wealth_status` label logic.

## Blocked Conditions

Set `status = "blocked"` if any of the following prevents a reliable guardrail:

- missing `chart`
- missing `chart.ascendant.sign`
- unable to resolve required lords for the route
- a required relevant planet exists conceptually but lacks `status`

When blocked:

- keep `score_delta = 0`
- do not add a positive or negative dignity context
- optionally add `dignity_guardrail_blocked` to `secondary_context`

## Implementation Shape

Implementation should follow the same pattern as the existing small bridge helpers:

- add a dedicated helper such as `_derive_dignity_guardrail(route, present)`
- call it during strict evidence collection
- store the result in `present["dignity_guardrail"]`
- consume it in `_derive_event_judgement(...)`

Do not inline dignity scanning directly inside the scoring block.

## Testing Requirements

Add focused tests that prove the boundary:

1. `relationship` ignores non-relevant planets even if they have `Neecha Bhanga` or `Great Enemy`
2. `finance` ignores non-relevant planets even if they have `Neecha Bhanga` or `Great Enemy`
3. route-relevant `Neecha Bhanga` yields `score_delta = 5`
4. route-relevant `Great Enemy` yields `score_delta = -5`
5. mixed relevant signals yield `status = "conflict"` and `score_delta = 0`
6. missing chart or unresolved lord yields `status = "blocked"`
7. no test may allow dignity to change `dominant_label`
8. no test may allow repeated relevant planets to stack score beyond `5`

## Risks and Containment

### Risk 1: D1 dignity leaks into divisional logic

Containment:

- v1 reads only D1 `chart.planets.status`

### Risk 2: Dignity becomes an alternate scoring engine

Containment:

- two codes only
- one score delta only
- no stacking

### Risk 3: Domain boundaries get blurred

Containment:

- route-specific relevant planet lists
- explicit `ignored_planets`

## Next Step After v1

After this guardrail lands and is verified, the next bridge should be a separate `functional_role_guardrail` that consumes the already existing Functional Benefic/Malefic layer without mixing that logic into dignity v1.
