# Public Jyotish Benchmark Dashboard

Generated: `2026-06-28T23:44:26.816376+00:00`

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

- artifact_count: `8`
- packet_count: `8`
- dasha_artifacts: `3`
- shadbala_artifacts: `4`
- tajika_sahams_artifacts: `1`

## Boundary Audit

- external_verified_template_cases: `5`
- template_comparison_count: `5`
- production_tuning_recommended: `false`

## Global First Claim

- can_claim_global_first: `false`
- reason: Do not claim global first until Dasha/Shadbala external oracle packets are valid, production tuning is allowed, and public benchmark history is stable.

## Remaining Gap

Dasha-only external oracle readiness is 3/3; Shadbala external absolute-value readiness is 4/4; PyJHora black-box assets are 8 artifacts / 8 packets; public long-term benchmark history is not yet comparable to the strongest global open-source projects.

## Next Actions

- Fill the next open Tajika/Sahams or Shadbala external packet under references/oracle/artifacts/pending_packets.
- Run oracle_evidence_validator.py until at least one packet is valid.
- Run oracle_boundary_audit.py to inspect Dasha/Shadbala deltas without tuning constants.
- Publish this dashboard after each validated sample batch.
