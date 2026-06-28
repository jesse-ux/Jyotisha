# Life Event Graph v1 Audit - 2026-06-28

## Scope

`life_event_graph_v1` is a compact graph contract added to strict workflow outputs. It is not a high-frequency probability curve yet; it is the first product-ready ledger-to-graph bridge for front-end rendering and future VedAstro range-scan overlays.

## Output Contract

Each strict workflow response now includes:

```json
{
  "life_event_graph": {
    "version": "life_event_graph_v1",
    "route": "relationship | career | finance | ...",
    "dominant_label": "string | null",
    "verdict": "string",
    "confidence_cap": "string",
    "blocked": false,
    "missing_evidence": [],
    "event_nodes": [],
    "secondary_context": [],
    "primary_drivers": []
  }
}
```

## Node Types

- `judgement`: strict workflow verdict and score.
- `dasha_window`: Vimshottari or Narayana current window.
- `convergence`: domain convergence from local Dasha convergence.
- `external_window`: VedAstro adapter range-scan event evidence after provenance filtering.

## Boundary

- This is not `EventsAtRange` parity.
- It does not create new event predictions.
- It reflects already-collected strict workflow evidence.
- External windows remain oracle evidence until promoted by adjudicator tests.

## Why This Matters

The parity matrix identified Life Event Graphs as a P0 VedAstro gap. This v1 creates the stable semantic payload that the local PWA can render later without changing the adjudicator evidence contract.

## Verification

- `tests/test_life_event_graph_v1.py`
- `tests/test_mcp_strict_workflow_relationship.py`
- `tests/test_mcp_strict_workflow_career.py`
- `tests/test_mcp_strict_workflow_finance.py`
