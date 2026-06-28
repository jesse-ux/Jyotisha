# Argala / Virodhargala Adjudicator Bridge

Date: 2026-06-28

## Scope

This pass connects an already computed Jyotish technique into strict adjudication:

- Career route reads `modules.argala.houses.house_10`.
- Relationship route reads `modules.argala.houses.house_7`.
- The bridge never recalculates Argala and never overrides the native `scripts/argala.py` result.

## Contract

`present_evidence.argala_support` is a secondary modifier:

```json
{
  "level": "none | supportive | obstructive",
  "target_house": 10,
  "source": "argala_house_bridge_v1",
  "signals": ["argala_support"],
  "raw": {
    "net_result": "supported",
    "argala_count": 2,
    "virodhargala_count": 0
  }
}
```

## Scoring Boundary

- `supportive`: `score +5`, `secondary_context += ["argala_support"]`
- `obstructive`: `score -5`, `secondary_context += ["virodhargala_obstruction"]`
- `none`: no score effect

Argala is not a hard gate. Missing Argala must not block the route.

## Anti-Overclaim Rule

Argala / Virodhargala cannot directly set:

- `dominant_label`
- `payout_label`
- route `verdict`

It can only nudge the score through the normal threshold system. This preserves the project's rule that no single technique may override D1/Varga/Dasha/Transit convergence.

## Regression Targets

- Career: supportive 10th-house Argala is collected and appears as `argala_support`.
- Relationship: obstructive 7th-house Virodhargala is collected and appears as `virodhargala_obstruction`.
- Existing Jaimini, VedAstro, dignity, finance, and native Argala tests remain green.

