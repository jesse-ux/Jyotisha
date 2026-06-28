# Wealth Adjudicator Seventh Pass Ashtakavarga Bridge (2026-06-28)

## What This Pass Freezes

This pass does not invent a new finance scoring path.

It locks an already-landed bridge in `/Users/wuyongnaren/Documents/印度占星/mcp_server.py` with an explicit regression test and puts it back into the audit trail.

The bridge is:

- `present_evidence.ashtakavarga_finance_support`
- `event_judgement.secondary_context += ["ashtakavarga_wealth_support"]`

when `Ashtakavarga house_scores` show supportive SAV values on wealth houses.

## Boundary

This bridge remains a secondary modifier.

It does:

- read native `modules.ashtakavarga.house_scores`
- inspect wealth houses `2` and `11`
- emit a compact evidence block
- append context for downstream finance adjudication

It does not:

- recalculate Ashtakavarga
- override `wealth_promise_strength`
- mint a new payout label
- bypass D2 / Dasha / convergence requirements

## Contract

The frozen structure is:

```json
{
  "ashtakavarga_finance_support": {
    "level": "supportive | none",
    "source": "ashtakavarga_house_scores_bridge_v1",
    "target_houses": [2, 11],
    "signals": ["wealth_sav_support"],
    "raw_scores": {
      "2": 33,
      "11": 35
    }
  }
}
```

And the finance event judgement can add:

```json
{
  "secondary_context": ["ashtakavarga_wealth_support"]
}
```

## Regression Locked

Test file:

- `/Users/wuyongnaren/Documents/印度占星/tests/test_mcp_strict_workflow_finance.py`

Locked case:

- supportive SAV score on house `2`
- supportive SAV score on house `11`
- native Dhana support already present

Expected:

- `present_evidence.ashtakavarga_finance_support.level == "supportive"`
- `secondary_context` includes `ashtakavarga_wealth_support`

## Why This Matters

This closes a small but important gap:

- the code path was present
- the strict workflow test suite had started to expect it
- but the bridge had not yet been frozen into the research trail

That is exactly how high-value logic turns back into an underused fragment. This pass prevents that drift.

## Verification

Ran:

```bash
python3 -m pytest tests/test_mcp_strict_workflow_finance.py -q
python3 -m pytest tests/test_mcp_strict_workflow_career.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_finance.py -q
```

## Still Open After This Pass

- richer wealth use of Ashtakavarga beyond simple supportive bridge
- Vimsopaka semantic mapping for `NEECHA_BHANGA / GREAT_FRIEND / GREAT_ENEMY`
- functional-role guardrail
- VedAstro adapter MVP
- oracle pending packets and benchmark closure
