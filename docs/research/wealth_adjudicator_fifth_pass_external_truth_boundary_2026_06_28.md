# Wealth Adjudicator Fifth Pass External Truth Boundary (2026-06-28)

## What Was Fixed

This pass closed a structural contradiction in the finance adjudicator:

- one branch of the codebase was already moving toward `external_truth.yogi_planet`
- another branch was still internally deriving Yogi from Sun/Moon degrees and letting that influence finance promise folding

That violated the new high-rigor boundary.

## Boundary Now Enforced

The finance adjudicator now follows this rule:

1. No external `yogi_planet` -> no Yogi contribution
2. External `yogi_planet` present -> lightweight D1 gate only
3. Only then may Yogi enter:
   - `wealth_promise_strength.supporting_sources`
   - `source_diversity`
   - `secondary_context` as `yogi_active`

## Removed Risk

The following behavior is no longer allowed:

- deriving Yogi from internal Sun/Moon degrees
- upgrading `dhana_yogas` to `dhana_yogi_hooks` without upstream truth
- creating `yogi_support_only` from local chart math

## Regression Contract

The finance regression suite now locks these four truths:

1. `dhana` alone must stay `dhana_yogas` without external truth
2. `dhana + lakshmi` must stay `dhana_lakshmi_hooks` without external truth
3. Yogi-only local chart inputs must not produce a finance promise
4. External truth + valid Kendra/Trikona placement may promote to `dhana_yogi_hooks`

## Verification

Command:

```bash
python3 -m pytest tests/test_mcp_strict_workflow_finance.py -q
```

Observed:

- `12 passed`

Manual probe confirmed:

- `NO_EXTERNAL` -> no Yogi source in promise folding
- `WITH_EXTERNAL` -> `supporting_sources = ["dhana", "yogi"]`
- `secondary_context` includes `yogi_active`

## Why This Matters

This is not just a bug fix. It restores honesty at the adjudication layer.

The finance engine can now say:

- "Yogi affected this judgement because an upstream truth source supplied it"

but can no longer silently smuggle Yogi into the result from local chart math.

## Next Step

Keep the same discipline for all future high-order promise hooks:

1. external truth first
2. lightweight downstream gating second
3. no hidden internal recomputation
