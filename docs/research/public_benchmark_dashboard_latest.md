# Public Jyotish Benchmark Dashboard

Generated: `2026-07-01T11:37:25.105482+00:00`

## Capability Registry

- technique_count: `89`
- capability_valid: `true`
- problem_count: `0`

## Dasha/Shadbala Oracle Readiness

- total_packets: `6`
- valid_packets: `5`
- ready_for_calibration: `5`
- production_tuning_allowed: `false`
- valid_dasha_packets: `3`
- total_dasha_packets: `3`
- external_verified_shadbala_tasks: `4`
- shadbala_task_count: `4`

## PyJHora Black-Box Assets

- artifact_count: `12`
- packet_count: `8`
- dasha_artifacts: `3`
- shadbala_artifacts: `4`
- tajika_sahams_artifacts: `5`

## Boundary Audit

- external_verified_template_cases: `5`
- template_comparison_count: `5`
- production_tuning_recommended: `false`

## Global First Claim

- can_claim_global_first: `false`
- reason: Do not claim global first until Dasha/Shadbala external oracle packets are valid, production tuning is allowed, and public benchmark history is stable.

## Remaining Gap

Dasha-only external oracle readiness is 3/3; Shadbala external absolute-value readiness is 4/4; PyJHora black-box assets are 12 artifacts / 8 packets; public long-term benchmark history is not yet comparable to the strongest global open-source projects.

## Next Actions

- Expand public benchmark history instead of over-claiming from the current closed target set.
- Run oracle_boundary_audit.py to inspect Dasha/Shadbala deltas without tuning constants.
- Regenerate Tajika/Dasha/Shadbala status boards after each new external packet batch.
- Publish this dashboard after each validated sample batch so public claim boundaries stay conservative.
