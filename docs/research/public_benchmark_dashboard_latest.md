# Public Jyotish Benchmark Dashboard

Generated: `2026-07-17T07:10:35.764614+00:00`

## Capability Registry

- technique_count: `91`
- capability_valid: `true`
- problem_count: `0`

## Dasha/Shadbala Oracle Readiness

- total_packets: `4`
- valid_packets: `3`
- ready_for_calibration: `3`
- production_tuning_allowed: `false`
- valid_dasha_packets: `2`
- total_dasha_packets: `2`
- external_verified_shadbala_tasks: `2`
- shadbala_task_count: `2`

## PyJHora Black-Box Assets

- artifact_count: `9`
- packet_count: `6`
- dasha_artifacts: `2`
- shadbala_artifacts: `2`
- tajika_sahams_artifacts: `5`

## Boundary Audit

- external_verified_template_cases: `3`
- template_comparison_count: `3`
- production_tuning_recommended: `false`

## Global First Claim

- can_claim_global_first: `false`
- reason: Do not claim global first until Dasha/Shadbala external oracle packets are valid, production tuning is allowed, and public benchmark history is stable.

## Remaining Gap

Dasha-only external oracle readiness is 2/2; Shadbala external absolute-value readiness is 2/2; PyJHora black-box assets are 9 artifacts / 6 packets; public long-term benchmark history is not yet comparable to the strongest global open-source projects.

## Next Actions

- Expand public benchmark history instead of over-claiming from the current closed target set.
- Run oracle_boundary_audit.py to inspect Dasha/Shadbala deltas without tuning constants.
- Regenerate Tajika/Dasha/Shadbala status boards after each new external packet batch.
- Publish this dashboard after each validated sample batch so public claim boundaries stay conservative.
