# Task 4 Report — Constrained Dynamic Question Generation

## Scope

- Base implementation commit: `437d50f` (with plan-only commits through `f90a3bd`).
- Implemented only the Task 4 files listed in `.superpowers/sdd/task-4-brief.md`.
- Preserved the untracked `.omo/` directory and did not change dependencies.

## RED evidence

1. After adding the dynamic prompt/parser/binding and guide-service tests:
   - Command: bundled Node `--test tests/birth-time-guide-agent.test.ts tests/birth-time-guide-route.test.ts`
   - Expected failures: `ERR_MODULE_NOT_FOUND` for `birth-time-dynamic-question-validator.ts` and four `generateQuestion is not a function` failures.
   - Legacy guide-route tests remained green.
2. After adding the exact-JSON boundary test:
   - Command: bundled Node `--test tests/birth-time-guide-route.test.ts`
   - Expected failure: wrapped commentary was accepted in one call (`1 !== 2`) instead of being rejected, retried once, and falling back.

## GREEN implementation

- Added a strict discriminated model-output parser for one server-issued opportunity and its exact unique partition set.
- The prompt projection contains only model-safe opportunity copy and an optional trimmed unmatched note. It excludes candidate times, score vectors, candidate model state, confidence/control fields, ranges, information-gain values, and history fingerprints.
- Added content/length controls for one Simplified-Chinese-facing question, 2–4 labels, birth-time strings, confidence, candidate support, methodology, and server-control claims.
- Added server-created UUID injection, private score-vector attachment, two server-owned special choices, SHA-256 normalized public-semantic fingerprints, and repeated question/partition rejection.
- Added one model retry, exact-JSON enforcement, deterministic top-opportunity fallback, advisory-only `no_useful_question`, and a persisted low terminal transition when no usable opportunity remains.
- Added the Mastra dynamic task contract while preserving legacy question-variant and evidence-draft behavior.

## Verification

- Focused guide tests: **31/31 pass**.
- All frontend birth-time tests: **218/218 pass**.
- ESLint on all six owned source/test targets: **pass**.
- `git diff --check`: **pass**.
- Source LOC: validator **233**, guide agent **216**, guide service **250**.
- Full `tsc --noEmit`: Task 4 has no type errors; the command still fails only at the pre-existing `tests/profile-persistence.test.ts:7` ES2018 regex-target error.
- Mandatory pre-work check reached all audits but retains the known unrelated fragment-governance mismatch: `candidate_count` expected `0`, actual `1`; remote visibility remained blocked and no synchronization claim was made.

## Integration note

`createBirthTimeGuideService()` commits both question and terminal outcomes through the injected `commitDynamicQuestion` port. Task 5/6 own the transactional store implementation and irreversible turn guards; this task does not bypass or pre-implement those later persistence transitions.
