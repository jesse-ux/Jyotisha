# Wealth Adjudicator Sixth Pass Avayogi Boundary (2026-06-28)

## Scope

This pass adds the smallest safe `Avayogi` risk hook to the finance adjudicator.

The hook follows the same guardrail style already enforced for `Yogi`:

- upstream truth first
- downstream lightweight gate second
- no internal recomputation of the governing symbolic source

## Contract

The finance adjudicator now accepts:

```json
{
  "external_truth": {
    "avayogi_planet": "Saturn"
  }
}
```

It does **not** compute `Avayogi` on its own.

## Implemented Behavior

### When it triggers

The hook returns `moderate` risk only when:

1. `external_truth.avayogi_planet` is present
2. a matching D1 planet record exists
3. the planet falls in `1/2/5/9/10/11`
4. the status is not obviously protected (`Own Sign`, `Moolatrikona`, `Exalted`)

### What it does

When triggered:

- `present_evidence["avayogi_risk"]` is populated
- finance adjudication applies `score -5`
- `secondary_context` gains `avayogi_active`

### What it does not do

- does not alter `dominant_label`
- does not alter `payout_label`
- does not alter `wealth_promise_strength`
- does not manufacture any new finance promise

## Why This Boundary Matters

`Avayogi` is treated as a leakage / obstruction refiner, not as a primary promise engine.

That matches:

- `event_judgment_wealth.md`
- `yogi-asc-tight-orb-wealth-freeze-guide.md`
- the existing interpretation templates that frame `Avayogi` as friction, delay, or loss-management context

## Regression Coverage

Added coverage for:

1. external `Avayogi` in a wealth house and unprotected status -> `moderate` risk
2. external `Avayogi` in `Own Sign` -> no risk trigger
3. no external `Avayogi` truth -> no risk trigger

## Verification

Commands:

```bash
python3 -m pytest tests/test_mcp_strict_workflow_finance.py -q
python3 -m pytest tests/test_mcp_strict_workflow_finance.py -q -k avayogi
```

Observed:

- full suite: `16 passed`
- Avayogi subset: `3 passed`

## Result

The finance adjudicator now has:

- a native positive `Yogi` wealth-support hook
- an external-truth positive `Yogi` enrichment path
- an external-truth negative `Avayogi` risk path

All three remain explicitly separated by boundary rules.
