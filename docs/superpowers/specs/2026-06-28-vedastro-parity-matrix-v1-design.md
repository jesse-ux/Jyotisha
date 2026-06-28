# VedAstro Parity Matrix v1 Design

## Goal

Create a repeatable parity matrix that compares public VedAstro capability areas with this repository's local assets and recommends the safest integration path for each area.

## Boundary

The matrix is a planning and audit artifact. It does not claim that local behavior equals VedAstro behavior unless the local registry, tests, and external oracle status support that claim.

## Inputs

- `scripts/audit_capabilities.py --mode validate`
- `scripts/vedastro_service_adapter.py` schema and supported range-scan domains
- A curated public VedAstro capability seed list kept in the generator script
- Existing research indexes under `docs/research/ACTIVE_FRONTS.md`

## Output Contract

Each row includes:

- `vedastro_capability`
- `category`
- `local_status`
- `local_assets`
- `can_call_vedastro`
- `recommended_path`
- `priority`
- `license_boundary`
- `adjudicator_use`
- `gap_notes`

Allowed `recommended_path` values:

- `local_native`
- `vedastro_adapter`
- `new_local_impl`
- `external_evidence_only`
- `hybrid_local_plus_vedastro`

## v1 Priorities

P0 rows cover: range scanning, ayanamsa parity, D1-D60/varga parity, Ashtakavarga/Shadbala oracle checks, Jaimini/Chara Dasha, Synastry/Ashtakoot, Tajika annual, Prashna, report rendering, and MCP/API parity.

## Honesty Rule

External VedAstro output must be marked as adapter evidence unless it is independently promoted through local tests or an oracle artifact. Local adjudicators remain the final reasoning layer.
