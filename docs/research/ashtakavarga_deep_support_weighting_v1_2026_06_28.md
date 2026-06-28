# Ashtakavarga Deep Support Weighting v1

Date: 2026-06-28

## Scope

This pass upgrades the newly bridged finance evidence layers from visibility-only into controlled low-weight score modifiers:

- `PAV / Prastara AV`
- `Sodhita AV`
- `Kakshya`

## Weighting

The v1 weights are intentionally small:

- `PAV supportive`: `+2`
- `Kakshya supportive`: `+2`
- `Sodhita obstructive`: `-2`
- `Kakshya obstructive`: `-2`

## Boundary

These weights are not allowed to directly mint or revoke:

- `dominant_label`
- `payout_label`

They only adjust the route score through the existing threshold system.

## Why This Matters

The project already computed these layers, but they were previously dead weight inside strict adjudication.

This pass keeps the scoring conservative while letting deeper Ashtakavarga and degree-trigger signals actually influence finance ranking.

## Still Open

- calibrating whether `PAV` should distinguish contributor identity more sharply
- deciding whether `Sodhita` should also have a positive support path
- tying `Kakshya` more directly to transit timing instead of route-average usage
- validating the weights against external oracle cases before claiming mature timing precision

