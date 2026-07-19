# Real-case timing optimization audit — 2026-07-19

## Current verified layer

Positive-event replay is healthy:

| Manifest | Cases | Ready | Boundary |
|---|---:|---:|---|
| `references/real_case_calibration/replay_manifest.json` | 10 | 10 | known positive events only |
| `references/real_case_calibration/replay_manifest_holdout_v2.json` | 10 | 10 | blind positive holdout; not specificity proof |
| `references/real_case_calibration/replay_manifest_probe3_v2.json` | 3 | 3 | probe batch only |

This verifies technical recall around known dated events. It does not verify day/month predictive specificity.

## Current blocked layer

Day-level negative holdout remains empty:

- `references/real_case_calibration/day_level_holdout_v3_preregistration.json`
- `annotation_count = 0`
- `negative_count = 0`
- `positive_count = 0`
- `production_tuning_allowed = false`
- `status = awaiting_independent_labels`

Existing 40 control dates remain diagnostic only because they were already observed before preregistration and are not independent human-reviewed labels.

Pilot source queue exists at `references/real_case_calibration/day_level_holdout_v3_pilot_source_queue_2026_07_19.json`.

Boundary: the queue contains public-source candidates for Steve Jobs, Barack Obama, and Albert Einstein. It is not a holdout manifest and must not be used for timing evaluation until independent adjudication converts rows into frozen annotations.

## Optimization needed

1. Collect independent human-labeled non-event intervals for the same subjects/domains.
2. Freeze labels before scoring.
3. Run candidate day/month ranking over positive and negative windows together.
4. Promote timing claims only if positive windows rank above negative windows under frozen rules.

Until then, precise day/month output must stay:

- `timing_precision = candidate_day_window`
- `claim_status = exploratory_unvalidated`
- `production_tuning_allowed = false`

Allowed UX: ranked candidate windows w/ evidence and confidence caps.

Forbidden UX: packaging candidate dates as verified event promises.
