# VedAstro External Technique Evidence Contract - 2026-06-28

## Scope

This pass adds a thin `external_technique_evidence` bridge for VedAstro
calculation methods / API endpoints.

VedAstro's `596+` surface is treated here as a broad calculation-method and
astrological-event compute library. It is not modeled as `596` user-facing life
event categories.

Examples of supported external method intent:

- low-level astronomy and longitude methods
- dignity and strength methods
- Vargas and per-chart placement methods
- Dasha calculation methods
- Yoga / Gochar / FindLifeEvents-triggered calculation records

## Boundary

`external_technique_evidence` may enter:

- `secondary_context`
- `technique_audit`

It must not:

- change strict workflow `score`
- set or lift `dominant_label`
- set or lift `payout_label`
- replace local Dasha, Varga, Shadbala, Ashtakavarga, Jaimini, or functional benefic/malefic judgement

## Adapter Contract

`scripts/vedastro_service_adapter.py` now exposes:

```bash
python3 scripts/vedastro_service_adapter.py \
  --external-technique \
  --domain wealth \
  --method CalculateShadbala \
  --api-endpoint Calculate/Shadbala
```

When network execution is disabled, the adapter emits a request preview and
provenance metadata. When network execution is enabled, the normalized response
is wrapped into an `evidence_ledger` item with:

- `source = vedastro_service_adapter_candidate`
- `operation = calculation_method`
- `role = external_technique_evidence`
- `domain`
- `method`
- `api_endpoint`

## Strict Workflow Policy

The local adjudicator remains final. VedAstro external method records are
filtered by source, operation, role, and domain before being accepted.

Accepted evidence produces:

- `present_evidence.external_technique_evidence.level = context_only`
- `event_judgement.secondary_context += ["external_technique_evidence"]`
- a top-level `technique_audit` row marking the evidence as `external_evidence_only`

No scoring branch reads this evidence.

## Verification

Fresh checks:

- `python3 -m pytest tests/test_vedastro_external_technique_evidence.py -q`
- `python3 -m pytest tests/test_vedastro_service_adapter_executor.py tests/test_vedastro_parity_matrix.py tests/test_vedastro_adapter_candidate_guard.py tests/test_vedastro_external_technique_evidence.py -q`
- `python3 -m pytest tests/test_mcp_strict_workflow_finance.py tests/test_mcp_strict_workflow_career.py tests/test_mcp_strict_workflow_relationship.py tests/test_life_event_graph_v1.py -q`

