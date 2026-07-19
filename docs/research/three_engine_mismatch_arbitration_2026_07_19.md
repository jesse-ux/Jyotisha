# Three-engine mismatch arbitration

manifest: `references/oracle/three_engine_parity_replay_manifest.json`
status: `classified_unresolved`
truth_policy: `no_majority_vote`
commercial_sync: `status_and_claim_boundary_only`
mismatch_count: `60`
classified_count: `60`
unclassified_count: `0`

Do not copy raw research debt into commercial runtime. Commercial receives readiness, claim boundary, and user-safe status only.

## Category counts

| category | count |
|---|---:|
| `ashtakavarga_table_or_contributor_variant` | 8 |
| `derived_total_from_component_variants` | 7 |
| `endpoint_or_varga_semantics` | 10 |
| `shadbala_formula_variant` | 35 |

## Closure requirements

- `endpoint_or_varga_semantics`: Confirm VedAstro endpoint returns the requested varga under the same ayanamsa/node/method contract.
- `ashtakavarga_table_or_contributor_variant`: Compare contributor tables, Lagna inclusion, shodhana state, and BAV/SAV row semantics.
- `derived_total_from_component_variants`: Do not arbitrate totals until all six component variants and Virupa/Rupa units are aligned.
- `shadbala_formula_variant`: Compare component formula, units, local solar context, aspect model, and Chesta lineage before totals.
