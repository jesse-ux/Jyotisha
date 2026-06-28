# VedAstro Adapter Range Scan MVP - 2026-06-28

## Scope

This pass adds the first executable VedAstro range-scan boundary. It is not a
full VedAstro API integration and does not replace local Jyotish adjudication.

## Implemented

- `scripts/vedastro_service_adapter.py` now exposes a `--range-scan` mode.
- Supported first-pass domains are `marriage`, `wealth`, and `career`.
- The adapter builds a provenance-preserving request preview when
  `VEDASTRO_API_ENDPOINT` is configured but `VEDASTRO_ENABLE_NETWORK` is not
  enabled.
- If network execution is explicitly enabled, the adapter can normalize a
  VedAstro-like event payload into an `evidence_ledger`.

## Boundary

- VedAstro output is treated as external candidate evidence only.
- The adapter does not emit final marriage, wealth, or career verdicts.
- The local adjudicators remain responsible for promise, activation,
  manifestation, confidence, and conflict handling.
- Network execution remains opt-in through `VEDASTRO_ENABLE_NETWORK=1`.

## Verification

- `python3 -m pytest tests/test_vedastro_service_adapter_executor.py -q`
- Result: `10 passed`

## Next Work

1. Map real VedAstro endpoint response fields into the current `evidence_ledger`
   contract.
2. Add domain-specific event allowlists for marriage and wealth windows.
3. Feed the normalized range-scan ledger into the local relationship and finance
   strict workflow as external activation evidence.
4. Only after the above is stable, expand from MVP boundary to full VedAstro API
   radar integration.
