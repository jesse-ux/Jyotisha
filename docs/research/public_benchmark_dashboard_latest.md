# Public Jyotish Benchmark Dashboard

Generated: `2026-06-26T16:09:33.617633+00:00`

## Capability Registry

- technique_count: `79`
- capability_valid: `true`
- problem_count: `0`

## Dasha/Shadbala Oracle Readiness

- total_packets: `5`
- valid_packets: `0`
- ready_for_calibration: `0`
- production_tuning_allowed: `false`

## Boundary Audit

- external_verified_template_cases: `0`
- template_comparison_count: `0`
- production_tuning_recommended: `false`

## Global First Claim

- can_claim_global_first: `false`
- reason: Do not claim global first until Dasha/Shadbala external oracle packets are valid, production tuning is allowed, and public benchmark history is stable.

## Remaining Gap

Dasha/Shadbala external oracle readiness remains 0, Shadbala absolute values still need component-level external evidence, and public long-term benchmark history is not yet comparable to the strongest global open-source projects.

## Next Actions

- Fill the first external JHora/PyJHora packet under references/oracle/artifacts/pending_packets.
- Run oracle_evidence_validator.py until at least one packet is valid.
- Run oracle_boundary_audit.py to inspect Dasha/Shadbala deltas without tuning constants.
- Publish this dashboard after each validated sample batch.
