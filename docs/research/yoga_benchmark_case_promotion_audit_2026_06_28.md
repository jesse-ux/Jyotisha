# Yoga Benchmark Case Promotion Audit - 2026-06-28

## Scope

This pass converts the untracked `tests/test_yoga_benchmark_cases.py` scratch smoke test into an executable Yoga benchmark.

## Problem With The Old Fragment

The old file only verified that `detect_yogas_from_json()` returned a list and ended with `assert True`. It did not constrain any specific Yoga rule, category, strength, or metadata.

## Promoted Test Contract

The promoted test uses the same B.V. Raman-style static Aquarius chart but now asserts stable rule ids:

- `dharma_karmadhipati`
- `chandra_yoga_exalted`
- `shakti_yoga_9_10_lord`
- `bvr_016_vesi_precise`
- `budha_shukra_yoga`
- `kalatra_yoga_venus_kendra`
- `raja_yoga_5_10_lord`
- `raja_yoga_4_10_lord`

It also verifies that the metadata contract remains useful:

- `category`
- `strength`
- `source`
- human-readable `combination`

## Boundary

- This is a deterministic engine benchmark, not a life prediction.
- It does not claim B.V. Raman biography validation.
- It guards the data-driven Yoga engine and rule metadata against silent drift.

## Regression Coverage

- `/Users/wuyongnaren/Documents/印度占星/tests/test_yoga_benchmark_cases.py`
- `/Users/wuyongnaren/Documents/印度占星/tests/test_yoga_rules_integrity.py`
