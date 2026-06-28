# Wealth Adjudicator Fourth Pass Yogi Hook Audit (2026-06-28)

## Scope

This pass closes the smallest safe version of the external-truth Yogi hook for the finance adjudicator.

Guardrail kept intact:

- Do not calculate `yogi_planet` inside this repository.
- Only accept `external_truth.yogi_planet` from upstream truth sources.
- Only allow the hook to influence finance promise folding when the supplied Yogi planet passes a lightweight D1 placement filter.

## Root Cause Found

The first failing test was not exposing a product bug. It was exposing a bad fixture:

- the test expected a Yogi uplift,
- but the supplied `Venus` was in house `11`,
- while the agreed lightweight gate only allows Kendra/Trikona houses: `1, 4, 5, 7, 9, 10`.

So the finance pipeline was correctly rejecting the hook.

## Implemented Behavior

### Positive path

When all of the following are true:

1. `external_truth.yogi_planet` is present
2. matching D1 planet data is present in `modules.chart.planets`
3. the planet is in `1/4/5/7/9/10`
4. the status is not debilitated

Then:

- `present_evidence.yogi_promise` is populated
- `wealth_promise_strength.supporting_sources` gains `"yogi"`
- `source_diversity` increases accordingly
- `count` increases by `1`
- `primary_source` upgrades to `dhana_yogi_hooks` when the combined sources are `dhana + yogi`
- `secondary_context` gains `yogi_active` when a finance dominant label already exists

### Negative path

If the externally supplied Yogi planet falls outside Kendra/Trikona, the hook does nothing:

- `yogi_promise = None`
- no wealth promise promotion
- no `yogi_active` secondary context

## Regression Coverage

Added / confirmed:

1. Yogi hook activates only when external truth is present and D1 placement passes the filter.
2. Yogi hook does not activate for house `11`.
3. Existing finance adjudicator regressions remain green.

## Verification

Command:

```bash
python3 -m pytest tests/test_mcp_strict_workflow_finance.py -q
```

Observed:

- `9 passed`

Manual evidence probe also confirmed:

- house `10` case -> `dhana_yogi_hooks` + `yogi_active`
- house `11` case -> unchanged `dhana_yogas` promise fold and no Yogi secondary context

## Next Recommended Step

Keep the same non-destructive pattern and extend only one notch:

1. allow externally supplied Yogi truth to enrich `wealth_promise_strength`
2. do not compute Yogi internally
3. next, add a very small `Yogi` source-aware bump only through source structure, not direct verdict jumping
4. after that, move to `dominant_label + secondary_context` refinement for finance edge cases
