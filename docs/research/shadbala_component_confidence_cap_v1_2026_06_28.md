# Shadbala Component Confidence Cap v1

Date: 2026-06-28

## Scope

This pass connects Shadbala quality into the finance strict adjudicator.

Before this change, `shadbala.planets` acted mostly as a presence gate. A planet with only `total_rupa` could satisfy the route even when the six classical components were missing.

## Required Components

The v1 audit requires each listed planet to expose all six components:

- `sthana`
- `dig`
- `kala`
- `chesta`
- `naisargika`
- `drik`

Accepted layouts:

- `planet.components.sthana`
- direct `planet.sthana`

## Contract

`present_evidence.shadbala_component_audit`:

```json
{
  "status": "complete | incomplete | blocked",
  "source": "shadbala.planets",
  "required_components": ["sthana", "dig", "kala", "chesta", "naisargika", "drik"],
  "missing": {
    "Venus": ["sthana", "dig"]
  }
}
```

## Adjudication Boundary

- `complete`: no confidence penalty.
- `incomplete` or `blocked`: `confidence_cap = "low"` and `secondary_context += ["shadbala_component_gap"]`.

This does not claim Shadbala absolute calibration is complete. It only prevents a partial Shadbala packet from supporting high-confidence finance timing.

## Anti-Overclaim Rule

This v1 pass does not:

- compare Rupa values against JHora/PyJHora absolute truth
- score individual components
- change `dominant_label` or `payout_label`
- affect career or relationship routes

External oracle closure is still required before claiming mature Shadbala absolute accuracy.

