# Whole Project Fragment Sweep And VedAstro Ledger Link - 2026-06-28

## Sweep Result

The current `SKILL.md` and `AGENTS.md` match the installed WorkBuddy skill copy:

- `<repo>/SKILL.md`
- `<home>/.workbuddy/skills/jyotish-vedic-astrology/SKILL.md`
- `<repo>/AGENTS.md`
- `<home>/.workbuddy/skills/jyotish-vedic-astrology/AGENTS.md`

No instruction-layer skill drift was found.

The WorkBuddy `scripts/jyotish_engine.py` and `scripts/jyotish_api_server.py`
are older distribution copies and must not be reverse-copied over the current
repository source.

## Implemented Link

VedAstro range-scan output can now enter local strict workflows as external
activation context:

- relationship domain reads `modules.external_activation.evidence_ledger`
  entries where `domain == "marriage"`.
- finance domain reads `modules.external_activation.evidence_ledger` entries
  where `domain == "wealth"`.
- only `vedastro_service_adapter_candidate` range-scan events are accepted.
- a score of `70+` maps to `level = "moderate"`.
- moderate support adds `external_activation_support` to `secondary_context`.

## Boundary

- external activation does not directly lift `dominant_label`.
- external activation does not change `payout_label`.
- external activation does not bypass D9/UL, D2/D10, dual dasha, or existing
  convergence gates.
- cross-domain events are ignored.

## Verification

- `python3 -m pytest tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_finance.py tests/test_vedastro_service_adapter_executor.py -q`
- Result: `31 passed`

## Next Work

1. Add a domain-specific allowlist for VedAstro event IDs and tags.
2. Add real endpoint field mapping once a stable VedAstro endpoint is configured.
3. Add a benchmark fixture that feeds VedAstro ledger candidates into
   relationship and finance case audits.
