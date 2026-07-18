# Task 3 — TypeScript Engine Adapter and Trust Boundary

## Implementation

- Added snake-case serializers for dynamic opportunity and deterministic choice-scoring requests. Only server-resolved `ServerChoiceEvidence` becomes `partition_id` / `candidate_scores`; client option IDs and confidence fields are never serialized.
- Added strict dynamic response adapters. Opportunity responses are versioned, endpoint-bound, exact-field parsed, and split into a model-safe `packet`, private `candidateModel`, and private `scoringPartitions`.
- Candidate score maps must contain finite nonnegative values keyed by exactly every minute in the submitted range, including cross-midnight ranges. Duplicate opportunity/partition IDs and unexpected response fields are rejected.
- Dynamic scoring responses require `birth-time-choice-scoring-v2`, `dynamic_choice` evidence mode, empty public evidence, matching compatibility/effective counts, and the existing deterministic candidate safety gates.
- Added authenticated server-only engine calls for both dynamic Python endpoints. They fail before fetch when `JYOTISH_DYNAMIC_RECTIFICATION_TOKEN` is absent and send the configured value only as a bearer header. Legacy scan, questionnaire score, and dated-event score calls remain unauthenticated.
- Extended the legacy-compatible engine contract with optional dynamic methods and added `DynamicBirthTimeJourneyEngine`, where both methods are required. The production factory returns the required dynamic subtype while existing legacy-only test doubles remain source-compatible.
- Raised only the shared candidate-result compatibility cap from 6 to 10 and changed the high-gate message to “effective evidence items.” The dated-event request contract remains capped at 6.
- Added source-contract coverage preventing snake-case or camel-case candidate model, partition, score, and token identifiers from entering client, request, response, component, or hook modules.

## Files changed

- `frontend/src/lib/birth-time-journey-service.ts`
- `frontend/src/lib/birth-time-journey-engine.ts`
- `frontend/src/lib/birth-time-journey-adapters.ts`
- `frontend/src/lib/birth-time-journey-engine-model.ts`
- `frontend/src/lib/birth-time-evidence.ts`
- `frontend/tests/birth-time-journey-engine.test.ts`
- `frontend/tests/birth-time-journey-adapters.test.ts`
- `.superpowers/sdd/task-3-report.md`

## RED

1. Bundled Node focused run:
   - `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/birth-time-journey-engine.test.ts tests/birth-time-journey-adapters.test.ts`
   - Failed during module instantiation because `parseCandidateDifferenceBuild` and `parseDynamicChoiceScoring` did not exist. Baseline result: 1 pass, 1 file-load failure.
2. After the first adapter implementation, the malformed score-key regression failed because a response containing `candidate_scores: { "not-a-time": 1 }` was accepted.
3. The exact-range regression then failed because an otherwise valid `05:34` score key could be added outside the `05:30—05:33` range.
4. The initial source-level legacy-auth assertion was too broad and matched the next dynamic method. It was narrowed to the exact legacy method section; production behavior did not change for this test-only correction.

## GREEN

1. Focused Task 3 suite:
   - `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/birth-time-journey-engine.test.ts tests/birth-time-journey-adapters.test.ts`
   - 21 passed, 0 failed.
2. Complete birth-time frontend regression suite:
   - `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/birth-time*.test.ts`
   - 207 passed, 0 failed.
3. Focused ESLint over all Task 3 source and test files:
   - `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node node_modules/eslint/bin/eslint.js ...`
   - Passed with no diagnostics.
4. TypeScript diagnostic:
   - `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node node_modules/typescript/bin/tsc --noEmit --pretty false`
   - No Task 3 diagnostics. It reproduces only the existing baseline `TS1501` in `tests/profile-persistence.test.ts:7` because the project targets ES2017 while that test uses an ES2018 regex flag.
5. `git diff --check`
   - Passed with no whitespace errors.

## Pre-work gate

- Ran `/Users/jesse/Downloads/Copse/astrology/yinduzhanxing/.venv/bin/python scripts/pre_work_check.py --remote-timeout 8 --command-timeout 45` after reading both required sweep documents and the error ledger.
- The gate remained red only on the unrelated known fragment-governance baseline: `candidate_count` expected `0`, observed `1`. Remote visibility was blocked, so no cloud-sync claim is made.

## Self-review

- Dynamic secrets and score vectors stay behind the existing server-only engine entrypoint. The public dynamic packet deliberately drops `candidateScores`, while the private partition map retains the exact server vector for later binding.
- Both response adapters are strict at their dynamic endpoint roots; model-controlled extra fields cannot be silently retained.
- The dynamic scorer cannot elevate confidence by mismatching effective counts, dimensions, evidence mode, evidence contents, algorithm version, or the existing high-confidence candidate gates.
- Cross-midnight ranges enumerate minutes modulo 24 hours, preventing a valid `23:59—00:00` result from being rejected or split.
- Legacy request payloads, endpoints, timeout, parsing behavior, and authentication remain unchanged. The event request schema remains at 6 even though the shared result compatibility schema can represent the v2 cap of 10.
- No dependency, logging, model prompt field, client response field, or persistence write was added.

## Concerns

- The repository still lacks a standalone runtime `server-only` package for direct Node imports. Per the approved module-boundary decision, verification uses the production file's existing `import "server-only"` plus strict projection and source-contract tests rather than adding an unavailable dependency.
- The complete TypeScript diagnostic remains blocked by the unrelated ES2017/ES2018 regex baseline described above.

## Review fixes

- Restored byte-compatible legacy candidate parsing. Unknown nested evidence metadata is accepted and stripped exactly as before Task 3; dynamic response parsing no longer changes the legacy schema.
- Moved every v2 response schema, invariant, and mapping into `birth-time-journey-dynamic-adapters.ts`. Root responses, ranges, opportunities, partitions, and winning segments are strict; empty dynamic evidence is enforced before candidate construction.
- Split dynamic adapter regressions into `birth-time-journey-dynamic-adapters.test.ts`. Added duplicate opportunity/partition attacks, nested extra-field attacks, exact-range keys, cross-midnight mapping, and independent expected-value assertions.
- Made `buildDifferencePacket` and `scoreChoices` required on the primary `BirthTimeJourneyEngine`. Existing services use the explicit `LegacyBirthTimeJourneyEngine` pick, and legacy-only test doubles were narrowed without runtime behavior changes.
- Refactored HTTP execution into `createJourneyEngineWire`, whose `post` accepts one typed request object. The server-only factory remains the environment owner; engine assembly is injectable for executable fake-fetch verification without adding the unavailable `server-only` runtime dependency.
- Replaced greedy source-regex authentication tests with executable coverage for both exact dynamic URLs, serialized bodies, POST method, bearer header, 45-second abort signal, and missing-token zero-fetch behavior. All three legacy engine endpoints execute without an Authorization header.
- Removed newly introduced non-null assertions and narrowed the ownership scan to the client/request/component/hook boundary named by the plan.
- Kept every modified production and test TypeScript module at or below 250 pure LOC. The largest is `birth-time-journey-test-support.ts` at 249; Task 3 production modules range from 19 to 239.

### Review RED

1. The legacy compatibility regression failed with `unrecognized_keys` when an existing engine evidence item contained extra server metadata.
2. The new dynamic adapter suite failed to load because the protocol-specific module did not yet exist.
3. Independent review probes had shown nested dynamic `winning_segment` extras were silently stripped, optional primary engine methods weakened consumers, and the source-regex auth proof could remain green after removing authentication from one endpoint.

### Review GREEN

1. Focused legacy/dynamic/wire suite:
   - `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/birth-time-journey-engine.test.ts tests/birth-time-journey-adapters.test.ts tests/birth-time-journey-dynamic-adapters.test.ts`
   - 24 passed, 0 failed.
2. Complete birth-time suite:
   - `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/birth-time*.test.ts`
   - 210 passed, 0 failed.
3. Full frontend suite:
   - `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/*.test.ts`
   - 285 passed, 0 failed.
4. Focused ESLint across all changed production/test TypeScript modules:
   - Passed with no diagnostics.
5. TypeScript diagnostic:
   - No Task 3 diagnostics; only the known `tests/profile-persistence.test.ts:7 TS1501` baseline remains.
6. Pure-LOC audit and `git diff --check`:
   - Every changed TypeScript file is at or below 250 pure LOC; no whitespace errors.
