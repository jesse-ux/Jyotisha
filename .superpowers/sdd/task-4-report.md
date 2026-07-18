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

## RED evidence

Artifact: `.omo/evidence/task-4-finite-red.log`

Tests were changed before production code:

- TypeScript: 14 tests, 9 expected failures. The failures demonstrated that the note still
  crossed the prompt, selection-only output was rejected, old free-copy output remained
  possible, selected server copy was not rendered, and duplicate server labels were accepted.
- Python: 7 tests, 1 expected failure. Two distinct same-year windows both rendered as the
  indistinguishable label `2012—2012 年`.

## Implementation

- `birth-time-dynamic-question-copy.ts` now contains only server-copy structural validation,
  NFKC/whitespace label normalization, the note-free opportunity-selection projection, and
  deterministic server-copy fingerprinting. The former note blacklist and substring
  grounding logic were removed.
- `birth-time-dynamic-question-validator.ts` accepts only strict selection objects. Binding
  resolves the selected server opportunity, validates the prompt and normalized-unique
  labels, validates every matching private partition, and only then allocates IDs. Malformed
  server copy, private bindings, UUIDs, and persisted records raise
  `BirthTimeDynamicBindingError` and cannot be retried into a false low result.
- Fallback sorts opportunities by information gain descending and then opportunity ID,
  independent of packet order. Repeated fingerprints alone are skipped as recoverable.
- `dynamic_rectification_opportunities.py` selects the least detailed year/month/day range
  representation needed to distinguish visible windows. Cross-year ranges stay concise;
  same-year or same-month collisions gain month or day precision.
- The Mastra contract describes selection only and forbids prompt/options/labels/partition
  fields in Agent output.

The real Python-shaped fixture is checked against fresh Task 2 localized context, prompt,
labels, opportunity ID, fingerprint, and partition IDs, then parsed through the Task 3 adapter
and exercised through the Task 4 service. Task 5 persistence was not changed.

## Verification

| Gate | Result | Artifact |
| --- | --- | --- |
| Selection-only RED | expected 9 TS + 1 Python failures | `.omo/evidence/task-4-finite-red.log` |
| Focused dynamic/guide TypeScript | 36/36 pass | `.omo/evidence/task-4-finite-focused-ts.log` |
| Focused Task 2 Python | 29/29 pass | `.omo/evidence/task-4-finite-focused-python.log` |
| Legacy Python rectification | 22/22 pass | `.omo/evidence/task-4-finite-legacy-python.log` |
| All birth-time TypeScript | 223/223 pass | `.omo/evidence/task-4-finite-birth-time.log` |
| Full frontend | 298/298 pass | `.omo/evidence/task-4-finite-frontend-full.log` |
| Changed TypeScript ESLint | pass, zero diagnostics | `.omo/evidence/task-4-finite-eslint.log` |
| Changed Python Ruff | pass | `.omo/evidence/task-4-finite-ruff.log` |
| Diff check and TypeScript pure-LOC audit | pass; all audited modules <=250 | `.omo/evidence/task-4-finite-quality.log` |
| Full TypeScript check | only known unrelated `profile-persistence.test.ts:7` TS1501 | `.omo/evidence/task-4-finite-tsc.log` |
| Fresh selection-boundary review | CLEAR / APPROVE | `.omo/evidence/task-4-selection-boundary-code-review.md` |

The TypeScript command remains non-zero solely because the pre-existing profile-persistence
test uses a regular-expression flag newer than the configured target. No Task 4 file reports
a type error.
The fresh reviewer independently probed extra model fields, note omission, normalized label
collisions, malformed private bindings, server-failure propagation, fallback ordering,
all-repeated behavior, and Python month/day collisions. Both `omo:programming` language
perspectives and `omo:remove-ai-slops` returned no blocker.
