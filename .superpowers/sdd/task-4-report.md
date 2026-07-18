# Task 4 Report — Dynamic Choice Question Generation

## Outcome

Task 4 now uses the model only to phrase one grounded, selectable question over
server-issued opportunities. The server remains authoritative for opportunity IDs,
private score partitions, fallback selection, stop decisions, UUID allocation, and
persistence. The generated contract is choice-based and carries the selected server
partition directly; it does not require a second free-text time field.

This correction also closes the independent review blockers in
`.omo/evidence/task-4-code-review.md`:

- all five Task 2 dimensions now emit deterministic Simplified-Chinese public copy;
- a real Task 2-shaped packet survives the Task 3 adapter and Task 4 fallback path;
- unmatched notes are filtered and, when retained, represented as quoted untrusted data;
- generated questions must contain both selected-domain and experience/change semantics;
- recoverable model failures are separated from server binding and persistence failures;
- private partition bindings are validated before any public ID is allocated;
- model-supplied IDs are byte-exact; and
- duplicated dynamic tests were split into focused modules below the 250-pure-LOC limit.

## RED evidence

Artifact: `.omo/evidence/task-4-fix-red.log`

Tests were added before the corrections. The RED run recorded:

- TypeScript: 15 tests, 11 failures covering real fallback copy, adversarial notes,
  grounding, whitespace-padded IDs, the three-argument binder, validation-before-ID
  allocation, UUID/private-binding propagation, and fingerprint normalization.
- Python: 5 failures covering localized opportunity copy for education, relocation,
  relationship, career, and health/life-pressure dimensions.

## Implementation

- `scripts/dynamic_rectification_opportunities.py` owns a finite localized dimension map
  and produces neutral contexts, fallback prompts, and human-readable year-range labels.
- `frontend/src/lib/birth-time-dynamic-question-copy.ts` centralizes public-copy safety,
  opportunity grounding, untrusted-note projection, and semantic normalization.
- `frontend/src/lib/birth-time-dynamic-question-validator.ts` validates exact model IDs,
  separates recoverable generation errors from binding failures, validates all private
  partitions before ID allocation, and exposes the required three-argument agent binder
  plus a separately named fallback binder.
- `frontend/src/lib/birth-time-guide-service.ts` retries only recoverable model failures.
  UUID, private-score, server-ID, fallback-copy, and persisted-schema failures propagate
  and cannot be converted into a false low-confidence terminal result.
- `frontend/src/mastra/index.ts` declares notes as quoted untrusted evidence and forbids
  following them as instructions or using them to override server IDs and safety rules.
- The shared JSON fixture is Python-shaped data rather than a sanitized TypeScript-only
  packet. A Python regression verifies its server IDs, fingerprint, and partition IDs
  against the actual Task 2 opportunity builder, while the TypeScript service test parses
  it through the real Task 3 adapter.

Prior public-question summaries remain intentionally deferred to Task 6, as specified by
the review amendment; Task 4 rejects repeated server fingerprints without inventing
history from hashes. Task 5 persistence internals were not changed.

## Verification

| Gate | Result | Artifact |
| --- | --- | --- |
| Focused dynamic/guide TypeScript | 36/36 pass | `.omo/evidence/task-4-fix-focused-ts.log` |
| Focused Task 2 Python | 28/28 pass | `.omo/evidence/task-4-fix-focused-python.log` |
| All birth-time TypeScript | 223/223 pass | `.omo/evidence/task-4-fix-birth-time.log` |
| Full frontend | 298/298 pass | `.omo/evidence/task-4-fix-frontend-full.log` |
| Changed TypeScript ESLint | pass | `.omo/evidence/task-4-fix-eslint.log` |
| Changed Python Ruff | pass | `.omo/evidence/task-4-fix-ruff.log` |
| Diff check and pure-LOC audit | pass; every audited module <=250 | `.omo/evidence/task-4-fix-quality.log` |
| Full TypeScript check | only known unrelated `profile-persistence.test.ts:7` TS1501 | `.omo/evidence/task-4-fix-tsc.log` |

The empty ESLint artifact represents a successful zero-diagnostic run. The full TypeScript
command remains non-zero solely because the pre-existing test uses a regular-expression
flag newer than the configured target; none of the Task 4 files report a type error.
The required `omo:programming` and `omo:remove-ai-slops` follow-up review re-ran after
hardening imperative-note filtering and domain grounding, and returned `CLEAR`; the audit
record is `.omo/evidence/task-4-fix-slop-review.md`.
