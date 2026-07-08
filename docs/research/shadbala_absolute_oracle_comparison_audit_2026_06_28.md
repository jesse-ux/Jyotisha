# Shadbala Absolute Oracle Comparison Audit - 2026-06-28

## Scope

This pass promotes the local Shadbala absolute-value comparison helper from an untracked fragment into a formal oracle-closure asset.

## New Entrypoint

- `<repo>/scripts/shadbala_oracle_comparison.py`
- Primary function: `compare_case(oracle_file, case_id)`
- CLI example:

```bash
python3 scripts/shadbala_oracle_comparison.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --case-id template_steve_jobs_dasha_lahiri \
  --format json
```

## Output Contract

The report exposes:

- `scope = shadbala_absolute_oracle_comparison`
- `case_id`
- external oracle `status`
- birth and settings metadata
- per-planet `oracle_total_rupa`, `local_total_rupa`, and `diff_total_rupa`
- per-component Rupa deltas
- `global_scaling_check`
- tolerance metadata

## Boundary

- This is diagnostic oracle evidence.
- It does not authorize global Shadbala scaling.
- It does not tune constants from a single case.
- It preserves component-level deltas so future fixes can target the actual failing sub-strength instead of hiding mismatch inside a total score.

## Current External-Verified Case Snapshot

For `template_steve_jobs_dasha_lahiri`:

- `planet_count = 7`
- `planets_within_total_tolerance = 5`
- `max_abs_total_delta_rupa = 2.085`

This is useful enough to keep in the main repo, but not sufficient to claim Shadbala oracle closure.

## Regression Coverage

- `<repo>/tests/test_shadbala_oracle_comparison.py`
