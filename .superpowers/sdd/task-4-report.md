# Task 4 report: v3 public contract and domain errors

## Status

Implemented and committed as `18234e7 feat: define conversational rectification contract`.

## Files

- `frontend/src/lib/conversational-rectification/contracts.ts`
- `frontend/src/lib/conversational-rectification/errors.ts`
- `frontend/tests/conversational-rectification-contracts.test.ts`

## TDD evidence

### RED

Command:

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test frontend/tests/conversational-rectification-contracts.test.ts
```

Result: failed as intended with `ERR_MODULE_NOT_FOUND` for
`frontend/src/lib/conversational-rectification/contracts.ts`; 0 passed, 1 failed.

### GREEN

Command:

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test frontend/tests/conversational-rectification-contracts.test.ts
```

Result: 6 passed, 0 failed.

### Full frontend suite

Command:

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test frontend/tests/*.test.ts
```

Result: 482 passed, 0 failed.

`git diff --check` over the three task files also exited successfully before the commit.

## Self-review

- Commands are a strict discriminated union of exactly `start`, `resume`, `answer`,
  `pause`, `abandon`, and `confirm`.
- Every action-bearing command requires a UUID `actionId`; every command after `start`
  requires a nonnegative integer `turnVersion`; answers are trimmed, nonblank, and at
  most 4,000 characters; confirmation time is strict 24-hour `HH:mm`.
- Strict command objects reject client candidate scores, technical receipts, and other
  unknown fields. The response schema matches the prescribed public v3 turn shape and
  rejects extra nested candidate or technical fields.
- Domain errors expose fixed Chinese `error` and `message` values. Unknown browser,
  SQL, and model errors are converted to the stable `service_unavailable` response;
  their raw messages are never copied into public output.
- Tests use synthetic UUIDs, times, and event text only.

## Concerns

- None for this contract boundary. Future route/orchestrator work must return only
  `toConversationalRectificationPublicError()` output to preserve the non-leakage
  guarantee.

## Review remediation: safe route-facing error DTO

### RED

After adding the public-boundary regressions, the focused test command failed as
expected because `toConversationalRectificationPublicError` was not exported:

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test frontend/tests/conversational-rectification-contracts.test.ts
```

### GREEN

`toConversationalRectificationPublicError()` now returns a plain, frozen public DTO
with only stable `code`, `status`, `error`, `message`, and `retryable` fields. It
does not retain the unknown input, its `cause`, or any browser, SQL, or model-error
properties. The compatibility mapper delegates to that same safe route-facing mapper.

The catch-all copy is now neutral: `服务暂时不可用，请稍后重试。` It makes no data-retention
promise when persistence could have failed.

The new regressions recursively inspect all own keys and value descriptors of the
complete mapper result, serialize it with `JSON.stringify`, assert that a synthetic
raw browser/SQL/model failure message is unreachable, and prove the returned DTO is
immutable.

Focused result: 7 passed, 0 failed.

### Full frontend suite

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test frontend/tests/*.test.ts
```

Result: 483 passed, 0 failed.

### Pre-work gate

The required `python3 scripts/pre_work_check.py --remote-timeout 8 --command-timeout 45`
was run. It remains blocked by the repository's documented host-wide Python 3.9 /
missing-pytest and fragment-scan compatibility failures; this frontend-only change
does not alter those checks.
