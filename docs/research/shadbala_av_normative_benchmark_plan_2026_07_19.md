# Shadbala / Ashtakavarga normative benchmark plan — 2026-07-19

## Current status

Current Shadbala target set is closed, but global tuning is not allowed.

- current target set: `external_verified`
- `can_claim_shadbala_absolute_closure = true`
- `production_tuning_allowed = false`
- three-engine mismatch report: 60 mismatches, 60 classified, 0 unclassified
- Shadbala formula/component variants: 35 component rows + 7 derived-total rows
- Ashtakavarga table/contributor variants: 8 rows

## What this means

The research repo can claim closure for the current curated Shadbala target package. It must not claim universal Shadbala or AV truth across all schools/software.

## Required benchmark ladder

1. Source provenance
   - VP Jain: page/edition/source hash or explicit retrieval gap.
   - Xalen: source commit, package hash, executable hash if available, method list.
   - PyJHora/JHora: isolated AGPL oracle only; no copied implementation.
   - jyotishganit: permissive observation adapter where license permits.

2. Component normalization
   - `sthana`
   - `dig`
   - `kala`
   - `chesta`
   - `naisargika`
   - `drik`
   - `total_rupa`

3. Unit contract
   - Virupa vs Rupa must be explicit.
   - Totals cannot be arbitrated before components.
   - Component caps/floors must be named.

4. Formula variant registry
   - legitimate school variants become `method_variant`;
   - unresolved variants stay `classified_unresolved`;
   - no majority vote.

5. Independent ephemeris mode
   - same raw input mode isolates formula layer;
   - independent ephemeris mode checks longitude/ayanamsa layer;
   - both must be reported separately.

## Commercial sync rule

Commercial may receive:

- readiness status;
- user-safe confidence cap;
- claim boundary;
- supported component list.

Commercial must not receive:

- unresolved raw research debt;
- forced absolute Virupa truth;
- AGPL implementation code;
- production tuning flag while `production_tuning_allowed = false`.

## Next implementation task

Create a component provenance registry that maps each Shadbala/AV mismatch category to:

- source artifact;
- component;
- unit;
- likely reason;
- allowed claim;
- next evidence required.
