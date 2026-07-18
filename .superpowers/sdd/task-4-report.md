# Task 4 Report — Selection-Only Dynamic Choice Generation

## Outcome

Task 4 now implements the approved hybrid boundary:

- the deterministic engine creates opportunities, candidate partitions, selectable answer
  semantics, localized prompts, and localized labels;
- the Agent may only select one exact server opportunity ID or return advisory
  `no_useful_question`;
- the server validates and renders all public copy, attaches private score vectors, creates
  public UUIDs, and decides retry, fallback, and termination behavior; and
- the raw unmatched-answer note remains available to later workflow layers but is completely
  omitted from the Agent prompt.

The Agent cannot author a question, option, label, partition ID, birth-time claim, confidence
claim, or control instruction. Those fields are unrepresentable in its strict output schema.
This supersedes the keyword-filter/substring-grounding design reviewed in
`.omo/evidence/task-4-rereview.md` and the earlier interim `CLEAR` narrative.
The final acceptance correction has been implemented and independently re-audited by the
executor, but the main acceptance reviewer remains authoritative for completion status.

## RED evidence

Artifact: `.omo/evidence/task-4-finite-red.log`

Tests were changed before production code:

- TypeScript: 14 tests, 9 expected failures. The failures demonstrated that the note still
  crossed the prompt, selection-only output was rejected, old free-copy output remained
  possible, selected server copy was not rendered, and duplicate server labels were accepted.
- Python: 7 tests, 1 expected failure. Two distinct same-year windows both rendered as the
  indistinguishable label `2012—2012 年`.

Final-fix RED artifact: `.omo/evidence/task-4-final-red.log`.

- TypeScript: 17 tests, 2 expected failures. Exact and NFKC/whitespace-equivalent primary
  labels matching either reserved choice were accepted by both binder and service instead of
  failing before ID allocation.
- Python: 4/4 passed, including the new same-month/day-precision regression, confirming that
  the production behavior existed but previously lacked durable coverage.

## Implementation

- `birth-time-dynamic-question-copy.ts` now contains only server-copy structural validation,
  NFKC/whitespace label normalization, the note-free opportunity-selection projection, and
  deterministic server-copy fingerprinting. The former note blacklist and substring
  grounding logic were removed.
- `birth-time-dynamic-question-validator.ts` accepts only strict selection objects. Binding
  resolves the selected server opportunity, validates the prompt and normalized uniqueness
  across every primary and reserved visible label, validates every matching private
  partition, and only then allocates IDs. Malformed
  server copy, private bindings, UUIDs, and persisted records raise
  `BirthTimeDynamicBindingError` and cannot be retried into a false low result.
- Fallback sorts opportunities by information gain descending and then opportunity ID,
  independent of packet order. Repeated fingerprints alone are skipped as recoverable.
- `dynamic_rectification_copy.py` owns localized contexts and the least detailed
  year/month/day range representation needed to distinguish visible windows. Cross-year
  ranges stay concise; same-year or same-month collisions gain month or day precision.
  `dynamic_rectification_opportunities.py` is again below the 250-pure-LOC boundary.
- The Mastra contract describes selection only and forbids prompt/options/labels/partition
  fields in Agent output.

The real Python-shaped fixture retains structural CJK/no-ASCII copy, normalized label
uniqueness, partition count, opportunity ID, fingerprint, and partition-ID seam checks without
pinning exact natural-language prose. It is parsed through the Task 3 adapter and exercised
through the Task 4 service. Task 5 persistence was not changed.

## Verification

| Gate | Result | Artifact |
| --- | --- | --- |
| Final-fix RED | expected 2 TS failures; Python 4/4 | `.omo/evidence/task-4-final-red.log` |
| Focused dynamic/guide TypeScript | 38/38 pass | `.omo/evidence/task-4-final-focused-ts.log` |
| Focused Task 2 Python | 26/26 pass | `.omo/evidence/task-4-final-focused-python.log` |
| Legacy Python rectification | 22/22 pass | `.omo/evidence/task-4-final-legacy-python.log` |
| All birth-time TypeScript | 225/225 pass | `.omo/evidence/task-4-final-birth-time.log` |
| Full frontend | 300/300 pass | `.omo/evidence/task-4-final-frontend-full.log` |
| Cumulative changed TypeScript ESLint | pass, zero diagnostics | `.omo/evidence/task-4-final-eslint.log` |
| Cumulative changed Python Ruff | pass | `.omo/evidence/task-4-final-ruff.log` |
| Diff check and all changed TS/Python LOC | pass; every audited file <=250 | `.omo/evidence/task-4-final-quality.log` |
| Full TypeScript check | only known unrelated `profile-persistence.test.ts:7` TS1501 | `.omo/evidence/task-4-final-tsc.log` |
| Fresh final-fix review | CLEAR / APPROVE; no blockers or WATCH items | `.omo/evidence/task-4-final-fix-code-review.md` |

The TypeScript command remains non-zero solely because the pre-existing profile-persistence
test uses a regular-expression flag newer than the configured target. No Task 4 file reports
a type error.
The earlier `.omo/evidence/task-4-selection-boundary-code-review.md` `CLEAR` is explicitly
superseded by `.omo/evidence/task-4-final-review.md`; it is not cited as current acceptance.
The final reviewer independently rechecked reserved-label normalization, zero allocation and
commit, the packet-only prompt API, typed Python range-copy boundary, same-month day precision,
prose-pin removal, and cumulative LOC. Both required programming language perspectives and the
remove-slops perspective returned `CLEAR / APPROVE` with no remaining WATCH item.
