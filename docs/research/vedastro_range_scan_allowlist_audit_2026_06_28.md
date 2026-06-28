# VedAstro Range Scan Allowlist Audit - 2026-06-28

## Scope

This pass hardens the VedAstro range-scan adapter so external `EventsAtRange`-style responses do not enter the local evidence ledger unfiltered.

## Behavior

`scripts/vedastro_service_adapter.py` now filters range-scan events through a per-domain allowlist before writing `evidence_ledger`.

Supported domains:

- `marriage`
- `wealth`
- `career`

Each domain can accept an event by either:

- known event id, or
- at least one relevant tag.

## Boundary

- The allowlist only filters external candidate evidence.
- It does not promote VedAstro events into final conclusions.
- It does not change local Dasha, Narayana, Jaimini, Varga, Shadbala, Ashtakavarga, or strict workflow scoring.
- External range evidence remains secondary/oracle evidence until a domain adjudicator explicitly promotes it through tests.

## Contract Exposure

`--print-schema` now exposes:

```json
{
  "range_scan_event_allowlist": {
    "marriage": {
      "event_ids": [],
      "tags": []
    }
  }
}
```

This prevents future agents from treating the filtering layer as hidden behavior.

## Regression Coverage

- `/Users/wuyongnaren/Documents/印度占星/tests/test_vedastro_service_adapter_executor.py`
