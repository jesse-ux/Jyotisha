# Public Jyotish Benchmark Dashboard

Generated: `2026-06-26T18:30:41.336555+00:00`

## Capability Registry

- technique_count: `79`
- capability_valid: `true`
- problem_count: `0`

## Dasha/Shadbala Oracle Readiness

- total_packets: `5`
- valid_packets: `4`
- ready_for_calibration: `4`
- production_tuning_allowed: `false`
- valid_dasha_packets: `3`
- total_dasha_packets: `3`
- external_verified_shadbala_tasks: `4`
- shadbala_task_count: `4`

## Boundary Audit

- external_verified_template_cases: `4`
- template_comparison_count: `4`
- production_tuning_recommended: `false`

## Global First Claim

- can_claim_global_first: `false`
- reason: Do not claim global first until Dasha/Shadbala external oracle packets are valid, production tuning is allowed, and public benchmark history is stable.

## Remaining Gap

Dasha-only external oracle readiness is 3/3; Shadbala external absolute-value readiness is 4/4; public long-term benchmark history is not yet comparable to the strongest global open-source projects.

## Next Actions

- Fill the next open Tajika/Sahams or Shadbala external packet under references/oracle/artifacts/pending_packets.
- Run oracle_evidence_validator.py until at least one packet is valid.
- Run oracle_boundary_audit.py to inspect Dasha/Shadbala deltas without tuning constants.
- Publish this dashboard after each validated sample batch.
