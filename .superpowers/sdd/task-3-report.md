# Task 3 — TypeScript Engine Adapter and Trust Boundary

## Final design

- `BirthTimeJourneyEngine` requires both dynamic operations: `buildDifferencePacket` and `scoreChoices`. Existing scan/score consumers depend on the explicit `LegacyBirthTimeJourneyEngine` pick instead of weakening the primary interface.
- The server-only engine factory owns `JYOTISH_DYNAMIC_RECTIFICATION_TOKEN`. Both dynamic endpoints use an authenticated POST and a 45-second abort signal; all three legacy endpoints remain unauthenticated.
- Request serializers expose only server-resolved choice evidence. Client option IDs, confidence, applicability, and model-controlled safety gates are never sent as scoring authority.
- Dynamic v2 responses have a dedicated strict adapter. Root objects, ranges, opportunities, partitions, winning segments, score-map keys, counts, versions, modes, and duplicate identifiers are validated before mapping.
- Public difference packets omit private candidate score vectors. Private scoring partitions retain the exact server vector used by the later deterministic scoring call.
- Legacy response parsing remains compatibility-oriented: unknown server metadata is accepted and stripped. Only the shared result representation supports up to ten effective items; the legacy dated-event request remains capped at six.
- The HTTP wire accepts injected fetch and timeout-signal factories for executable contract tests. Production still defaults to `AbortSignal.timeout`.

## Files changed

Production:

- `frontend/src/lib/birth-time-evidence.ts`
- `frontend/src/lib/birth-time-journey-service.ts`
- `frontend/src/lib/birth-time-journey-engine.ts`
- `frontend/src/lib/birth-time-journey-engine-model.ts`
- `frontend/src/lib/birth-time-journey-adapters.ts`
- `frontend/src/lib/birth-time-journey-dynamic-adapters.ts`
- `frontend/src/lib/birth-time-journey-assessment.ts`

Tests and support:

- `frontend/tests/birth-time-journey-engine.test.ts`
- `frontend/tests/birth-time-journey-adapters.test.ts`
- `frontend/tests/birth-time-journey-dynamic-adapters.test.ts`
- `frontend/tests/birth-time-journey-memory-store.ts`
- `frontend/tests/birth-time-journey-test-support.ts`
- `frontend/tests/birth-time-journey-service.test.ts`
- `frontend/tests/birth-time-agent-flow-test-support.ts`

Documentation:

- `docs/superpowers/plans/2026-07-18-dynamic-choice-birth-time-rectification.md`
- `.superpowers/sdd/task-3-report.md`

## RED evidence

1. The initial focused run failed to load because the dynamic response parsers did not exist.
2. Adapter regressions then exposed acceptance of malformed score keys, keys outside the submitted range, duplicate opportunity/partition identifiers, nested extra fields, and legacy evidence metadata incompatibility.
3. Interface and wire review probes exposed optional primary dynamic methods, source-regex authentication assertions, and a missing executable proof for exact URLs, bodies, authorization, and timeout behavior.
4. The final wire cleanup test injected a timeout factory and failed with `[]` instead of `[45000, 45000]`, proving that the seam was initially ignored.

## Final verification

1. Focused adapter, wire, and evidence suite:
   - `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/birth-time-journey-engine.test.ts tests/birth-time-journey-adapters.test.ts tests/birth-time-journey-dynamic-adapters.test.ts tests/birth-time-evidence.test.ts`
   - 29 passed, 0 failed.
2. Complete birth-time frontend suite:
   - `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/birth-time*.test.ts`
   - 208 passed, 0 failed.
3. Full frontend suite:
   - `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/*.test.ts`
   - 283 passed, 0 failed.
4. ESLint across every changed production/test TypeScript module:
   - Passed with no diagnostics.
5. TypeScript diagnostic:
   - No Task 3 diagnostics. The only result is the known baseline `tests/profile-persistence.test.ts:7 TS1501`, caused by an ES2018 regex flag under the project's ES2017 target.
6. Pure-LOC audit:
   - Every changed TypeScript file is at or below 250 pure LOC. The largest is `frontend/src/lib/birth-time-journey-service.ts` at 239; the split test-support modules are 171 and 111.
7. `git diff --check`:
   - Passed with no whitespace errors.

## Pre-work gate

- `/Users/jesse/Downloads/Copse/astrology/yinduzhanxing/.venv/bin/python scripts/pre_work_check.py --remote-timeout 8 --command-timeout 45` remained red only on the unrelated known fragment-governance baseline: `candidate_count` expected `0`, observed `1`.
- Remote visibility was blocked, so no cloud-sync claim is made.

## Self-review

- Dynamic secrets and candidate score vectors remain behind the server boundary.
- Wire tests use independent literal request bodies rather than production serializers and directly assert two `45_000` timeout calls and the exact injected signals.
- Missing-token tests prove both dynamic operations fail before fetch. Executable legacy tests prove no Authorization header reaches any legacy endpoint.
- Dynamic parsing is fail-closed; legacy parsing preserves its prior accept-and-strip behavior.
- Cross-midnight ranges enumerate minutes modulo 24 hours and bind score keys to the exact submitted interval.
- The extracted memory store has no dependency on the fixture module, so its re-export does not create a runtime cycle.
- No dependency, logging field, client response field, or persistence write was added.

## Known unrelated baseline

- A clean TypeScript run is still blocked by `tests/profile-persistence.test.ts:7 TS1501`; Task 3 introduces no additional diagnostic.
