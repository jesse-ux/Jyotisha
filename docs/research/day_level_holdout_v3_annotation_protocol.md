# Day-Level Holdout V3 Annotation Protocol

Purpose: collect independent, source-backed timing labels for
`references/real_case_calibration/day_level_holdout_v3_preregistration.json`.
This packet does not alter chart rules, thresholds, or product wording.

## Independence

- The annotator must not have edited timing rules or existing control dates.
- `adjudicator` identifies the independent person or organization that resolved
  ambiguity. It must not be the timing-rule author.
- Use a public source URL for every row. Do not use an absent search result as
  evidence of `no_target_event`.

## One annotation row

```json
{
  "case_id": "public_subject_stable_id",
  "domain": "career",
  "label": "target_event",
  "start": "YYYY-MM-DD",
  "end": "YYYY-MM-DD",
  "source_url": "https://public-source.example/event",
  "adjudicator": "independent-labeler-id",
  "time_uncertainty_days": 0
}
```

`label` is exactly one of:

- `target_event`: source establishes the requested event in the stated interval.
- `no_target_event`: source establishes a genuine non-event interval, such as a
  dated diary, schedule, or contemporaneous record that would have recorded the
  target event. Mere silence is invalid.

Use day precision only when the source supports it. Otherwise widen `start` and
`end`, and record the uncertainty in `time_uncertainty_days`.

## Frozen acceptance gate

- At least 20 independently labeled positive cases.
- At least 80 independently labeled negative intervals.
- Every row has all eight fields shown above and a public URL.
- Existing four-control and pilot files remain prohibited from tuning.

Before submitting labels, run:

```bash
python3 scripts/day_level_holdout_validator.py \
  references/real_case_calibration/day_level_holdout_v3_preregistration.json
```

Only `ready_for_blind_replay` permits a blind replay. It still does not permit
retuning the frozen rules.
