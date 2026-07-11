# Public Real-Case Calibration Release Boundary

Date: 2026-07-12

This release publishes reproducible public-case calibration safeguards, not a
claim of predictive accuracy. It contains no user birth data, private feedback,
or private event history.

## Included Evidence

- V2.1 scoring correction: `public_real_case_23_case_v21_corrected_observation_2026_07_11.json`
- Date-control pilot: `public_real_case_negative_control_pilot_2026_07_11.json`
- Annual-control pilot: `public_real_case_annual_control_pilot_2026_07_11.json`
- Human-readable correction and control reports in this directory.

## Current Interpretation Boundary

- V2.1 removes duplicate MD/AD scoring and labels legacy precision-like fields
  as deprecated.
- SAV/BAV remains descriptive, non-scoring evidence.
- The date-control and annual-control pilots do not support exact-day or
  exact-month claims from the current replay score.
- The calibration corpus uses known positive events and partially adjudicated
  control dates. It does not establish specificity, balanced accuracy, or
  general predictive accuracy.
- External same-chart parity is separate. Local replay must not be described as
  VedAstro, PyJHora/JHora, or jyotishganit verified until all required raw
  oracle fields are imported and compared.

## Excluded Local Material

Earlier V1/V2 snapshots, probe outputs, comparison intermediates, and planning
files remain local. They are retained for audit but are not release evidence.
