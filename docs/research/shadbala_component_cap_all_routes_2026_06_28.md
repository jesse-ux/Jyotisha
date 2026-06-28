# Shadbala Component Cap Across Core Routes

Date: 2026-06-28

## Scope

This pass extends the Shadbala six-component completeness cap beyond finance into the three core strict adjudication routes:

- career
- relationship
- finance

## Route Boundary

Finance still requires `shadbala.planets`.

Career and relationship do not make Shadbala a hard route requirement in v1. Instead:

- if Shadbala is absent, the existing route continues unchanged;
- if Shadbala is present, its six-component completeness is audited;
- incomplete Shadbala lowers `confidence_cap` to `low`.

This prevents a partial strength packet from inflating high-rigor readings while preserving backward compatibility for career and relationship routes.

## Required Components

- `sthana`
- `dig`
- `kala`
- `chesta`
- `naisargika`
- `drik`

Accepted layouts:

- `planet.components.<component>`
- direct `planet.<component>`

## Adjudication Effect

When the component audit is `blocked` or `incomplete`:

- `confidence_cap = "low"`
- `secondary_context += ["shadbala_component_gap"]`

When complete:

- no confidence penalty
- no gap context

## Anti-Overclaim Rule

This is not Shadbala absolute calibration. It only enforces component completeness.

Still open:

- absolute Rupa comparison against JHora/PyJHora/VedAstro
- six-component value tolerance tests
- route-specific Shadbala planet selection and score weighting
- public benchmark history for Shadbala drift

