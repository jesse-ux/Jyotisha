# Oracle Blocker Resolution Attempt - 2026-07-17

## Summary

This pass converts the three non-fakeable blockers into executable evidence gates.

## VedAstro hosted identity / output drift

- Added `scripts/vedastro_identity_archive.py`.
- Archived NuGet self-host candidate identity for `VedAstro.Library` `1.2.0`:
  - package hash algorithm: `SHA512`
  - NuGet catalog commit: `c707690b-f7bd-4813-a2cb-876e943e9667`
  - license: `MIT`
  - target framework dependencies include `SwissEphNet [2.8.0.2, )`
- Evidence: `references/oracle/vedastro_reproducible_identity_archive_2026_07_17.json`.
- Boundary: this fixes a reproducible NuGet package identity only. It does not prove `api.vedastro.org` runs that package, DLL, container, or method semantics.
- Status: `hosted_api_status=blocked`.

## Timing independent negative holdout

- Added `scripts/timing_negative_holdout_audit.py`.
- Audited current candidate sources:
  - public positive timelines are not negative labels.
  - existing 40 control dates are observed and not independently reviewed, so diagnostic only.
- Evidence: `references/real_case_calibration/timing_negative_holdout_source_audit_2026_07_17.json`.
- Output policy remains: return ranked `candidate_day_window` with `claim_status=exploratory_unvalidated`; do not label day/month candidates as verified predictions.

## Xalen / Shadbala / Ashtakavarga arbitration

- Added `scripts/xalen_arbitration_gate.py`.
- Regenerated:
  - `references/oracle/xalen_formula_unit_attribution_2026_07_17.json`
  - `references/oracle/xalen_public_case_batch_2026_07_17.json`
  - `references/oracle/xalen_ephemeris_mode_comparison_2026_07_17.json`
  - `references/oracle/xalen_formula_arbitration_gate_2026_07_17.json`
- Five public AA cases replayed.
- Independent ephemeris comparison remains ready:
  - max longitude delta: `0.005305966338369217` degrees
  - varga differences: `0`
- Gate result: `truth_status=blocked`, `unresolved_variant_count=46`, `promotion_allowed=false`.
- Boundary: multi-case replay and independent ephemeris reduce implementation risk; they do not arbitrate formula variants without external numeric worked examples.

