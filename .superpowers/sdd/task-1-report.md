# Task 1 — Dynamic Choice Contracts and Stop Policy

## Implementation

- Added browser-safe dynamic choice and time-range Zod schemas. Public question parsing is strict and rejects hidden partition fields.
- Added internal-only dynamic choice contracts, persisted/private question schemas, candidate-difference packet schemas, and an explicit public projection helper.
- Added pure deterministic stop policy with the specified precedence and a material-change calculation for candidate range, representative time, and two-point margin changes.
- Added separate `DynamicNextAction` and `DynamicJourneyProgress` schemas, preserving the legacy guided-v1 `NextAction` and `JourneyProgress` parser path.
- Kept the internal contract module dependency-free as resolved by the user. A source-contract test scans components, hooks, client transports, and response schemas to prohibit imports of the private module.
- Dynamic IDs are opaque nonempty server-issued strings, rather than being overconstrained to UUIDs.

## Files changed

- `frontend/src/lib/birth-time-dynamic-choice.ts`
- `frontend/src/lib/birth-time-dynamic-choice-internal.ts`
- `frontend/src/lib/birth-time-dynamic-stop-policy.ts`
- `frontend/src/lib/birth-time-journey-turn-protocol.ts`
- `frontend/src/lib/birth-time-journey-turn.ts`
- `frontend/tests/birth-time-dynamic-choice.test.ts`
- `frontend/tests/birth-time-dynamic-stop-policy.test.ts`

## RED

1. `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/birth-time-dynamic-choice.test.ts`
   - Failed as expected before the public contract existed: `ERR_MODULE_NOT_FOUND` for `birth-time-dynamic-choice.ts`.
2. `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/birth-time-dynamic-stop-policy.test.ts`
   - Failed as expected before the policy existed: `ERR_MODULE_NOT_FOUND` for `birth-time-dynamic-stop-policy.ts`.
3. After the boundary resolution, the dynamic choice test failed as expected while the obsolete `server-only` marker remained: `ERR_MODULE_NOT_FOUND: Cannot find package 'server-only'`.
4. The opaque-ID regression initially failed because the first implementation required UUIDs.

## GREEN

1. `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/birth-time-dynamic-choice.test.ts tests/birth-time-dynamic-stop-policy.test.ts tests/birth-time-journey-turn.test.ts`
   - `14` passed, `0` failed.
2. `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/birth-time-*.test.ts`
   - `194` passed, `0` failed, duration `1449ms`.
3. `git diff --check`
   - Passed with no whitespace errors.

## Self-review

- Public choices are strict, require 2–4 primary options plus exactly one unknown and one unmatched option, reject duplicate IDs, cap labels at 80 characters, and reject private fields.
- Persisted primary choices require nonempty partitions and finite score maps. Unknown/unmatched choices require both private fields to be `null`.
- The public projection parses through the public schema, so partition IDs and candidate scores cannot cross the browser boundary.
- Stop ordering is high confidence, effective-answer safety cap, plateau, no information gain, repeated partition, then continue. Non-effective answers retain the prior plateau count.
- Legacy schemas and turn behavior remain unchanged; v2 schemas use distinct dynamic names and are re-exported from the turn module.
- All created/modified source files are within the 250 pure-LOC threshold (largest: `birth-time-journey-turn.ts`, 229 lines; new internal contract, 208 lines).

## Concerns

- Full `tsc --noEmit --incremental false` remains blocked by an unrelated existing error in `frontend/tests/profile-persistence.test.ts:7`: the project targets ES2017 while that test uses an ES2018 regular-expression flag. None of the Task 1 files produced a TypeScript error.
- The supplied no-excuse checker could not run because it is outside the frontend dependency tree and cannot resolve its own `typescript` package. The focused runtime suite, full birth-time suite, diff check, and manual forbidden-pattern scan completed successfully.

## Review fixes

- `DynamicStopInput.result` is now nullable, so a dynamic flow can finish before its first score. It also carries the explicit `forcedReason` union: `user_finished`, `generation_unavailable`, or `null`.
- Forced terminal reasons now win over every score-derived condition. A null result preserves the current plateau count instead of attempting score comparison.
- Added and re-exported `dynamicJourneyTurnStateSchema` / `DynamicJourneyTurnState`. The schema is strict and explicitly requires `journeyProtocol: "dynamic-choice-v2"`, a nonnegative turn version, a dynamic action, dynamic progress, and the existing permissions shape. The legacy `journeyTurnStateSchema` is unchanged.
- Added regressions for both forced terminal reasons, their high-confidence precedence, the dynamic discriminator, and rejection of a valid legacy action under the v2 schema.

### Review RED

`/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/birth-time-dynamic-choice.test.ts tests/birth-time-dynamic-stop-policy.test.ts`

- Failed before implementation because `dynamicJourneyTurnStateSchema` was not exported.
- Existing stop policy threw on `result: null` and returned `high_confidence` instead of the forced `user_finished` reason.

### Review GREEN

1. `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/birth-time-dynamic-choice.test.ts tests/birth-time-dynamic-stop-policy.test.ts tests/birth-time-journey-turn.test.ts`
   - `16` passed, `0` failed.
2. `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/birth-time-*.test.ts`
   - `196` passed, `0` failed, duration `1472ms`.
3. `/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node ./node_modules/typescript/bin/tsc --noEmit --incremental false`
   - Still reports only the existing `tests/profile-persistence.test.ts:7` ES2018-regexp/ES2017-target incompatibility; no Task 1 diagnostic was emitted.
