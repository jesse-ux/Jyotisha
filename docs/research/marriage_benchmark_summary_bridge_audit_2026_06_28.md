# Marriage Benchmark Summary Bridge Audit - 2026-06-28

## Scope

This pass turns the v6.1 marriage verification dataset from a large historical JSON asset into a small adjudicator-ready summary.

## Entrypoint

- `/Users/wuyongnaren/Documents/印度占星/scripts/marriage_benchmark_summary.py`
- Source dataset: `/Users/wuyongnaren/Documents/印度占星/tests/test-data/verify-results-v6.1.json`

## Why This Was Needed

The v6.1 benchmark already contains:

- 18 public cases
- 26 marriage events
- Rao P1-P8 hit data
- UL / Argala / D7 / D60 / Karakamsha context
- divorce markers

But the useful event statistics were buried inside a large JSON file and a generated report. The new summary helper makes the benchmark reusable by strict adjudicators without requiring every agent to manually parse the full file.

## Current Summary

- `case_count = 18`
- `ascendant_match_count = 18`
- `marriage_event_count = 26`
- `divorce_event_count = 15`
- Rao hit distribution:
  - `2/8`: 2 events
  - `3/8`: 2 events
  - `4/8`: 9 events
  - `5/8`: 8 events
  - `6/8`: 2 events
  - `7/8`: 3 events

## Label-Lift Seed Cases

The helper exposes the strongest `label_lift_failure_seed` candidates:

- `Britney Spears|Kevin Federline|2004-10-06`
- `Elon Musk|Justine Wilson|2000-01-01`
- `Tom Cruise|Katie Holmes|2006-11-18`
- `Albert Einstein|Mileva Maric|1903-01-06`
- `Nelson Mandela|Winnie Madikizela|1958-06-14`

These are high-signal calibration targets for future relationship adjudicator work.

## Boundary

- The helper does not recompute astrology.
- It does not alter the source dataset.
- It does not promote `legal_marriage` or any other label by itself.
- It only exposes benchmark evidence in a stable shape.

## Regression Coverage

- `/Users/wuyongnaren/Documents/印度占星/tests/test_marriage_benchmark_summary.py`
