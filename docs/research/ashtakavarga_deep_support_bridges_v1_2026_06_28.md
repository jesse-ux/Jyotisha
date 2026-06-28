# Ashtakavarga Deep Support Bridges v1

Date: 2026-06-28

## Scope

This pass extends finance strict adjudication beyond raw SAV house support and connects three already-computed evidence layers:

- `PAV / Prastara AV`
- `Sodhita AV`
- `Kakshya`

The bridge is intentionally conservative. All three layers are added as secondary support or friction context only.

## Contract

Finance strict evidence now accepts:

- `present_evidence.pav_finance_support`
- `present_evidence.sodhita_finance_support`
- `present_evidence.kakshya_finance_support`

These can add:

- `pav_finance_support`
- `sodhita_wealth_friction`
- `kakshya_finance_support`
- `kakshya_finance_friction`

to `event_judgement.secondary_context`.

## Boundary

This v1 pass does not:

- directly change `dominant_label`
- directly change `payout_label`
- directly change score thresholds

The goal is to make these layers visible and auditable in the adjudication chain before we let them influence window scoring.

## Current Heuristics

- `PAV`: marks support when a planet shows multiple strong contribution sources.
- `Sodhita`: marks friction when both 2H and 11H resolve to low purified support.
- `Kakshya`: marks support when average degree-level strength is high and friction when it is low.

## Still Open

- route-specific score weighting
- richer mapping from PAV contributor identity to wealth theme
- combining Kakshya with transit timing instead of route-level average only
- external benchmark closure against JHora/PyJHora examples

