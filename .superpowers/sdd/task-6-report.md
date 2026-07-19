# Task 6 Report: Dynamic Journey Orchestration

## Outcome

Implemented the `dynamic-choice-v2` journey as a persisted, Agent-driven state machine rather
than a fixed questionnaire loop. A primary click resolves only its server-owned private
partition, records one canonical evidence item, and creates one idempotent scoring job in the
same versioned transition. Unknown and unmatched choices remain non-evidence actions; unmatched
free context is bounded, stored separately for the Agent, and never enters scoring.

Question generation uses the full difference packet and persists the chosen question/private
binding before exposing it. Repeated generation fingerprints fail closed to a terminal low
result. Scoring claims the durable job, validates identity/fingerprint/algorithm, scores once,
and saves the result and deterministic stop decision in the same turn. Continuation depends on
available information and plateau/confidence state, not a fixed round count. High confidence
still requires explicit candidate confirmation and never applies a minute during orchestration.

Pause stores the exact current dynamic action and resume reconstructs that persisted action.
Terminal low, medium, confirmation, and ready turns are one-way: answer, generation, retry,
pause, and finish mutations cannot restart them. New assessments reload and return their
persisted v2 generation turn instead of projecting the former legacy baseline question.

The focused review follow-up closes three additional safety seams. Scoring now independently
recomputes the deterministic confidence class from persisted effective evidence/domain counts,
margin thresholds, and segment width; medium and high cannot be accepted below their gates.
Winning segments must be a chronological subset of the persisted range, with exact inclusive
width and midpoint representative time, including across midnight. Unmatched-context, pause,
and finish retries now carry a private typed receipt and replay only the identical action,
version, and payload; cross-action or changed-payload receipt reuse is stale.

The second review follow-up closes the database success-path seam. Every action-bearing v2
mutation now persists a canonical strict receipt: answers bind question and option, question
commits bind submitted/result fingerprints or a terminal result, and special actions/resume
bind their exact payload. A new ordered migration replaces the already-deployed generic turn
save: it locks case then private state and permits processed-action success only for version
`expected + 1` plus exact JSONB receipt equality. Dynamic scoring-job creation applies the same
locked private receipt check. TypeScript revalidates version and receipt after both successful
and failed RPC responses, so a normal duplicate-success response cannot bypass comparison.

## Persistence Amendment

Added service-role-only `create_birth_time_dynamic_scoring_job` and
`claim_birth_time_dynamic_scoring_job` RPCs. Creation owner-locks the v2 case and atomically
validates/persists the public turn, private state, canonical receipt, and pending job. Claiming
checks ownership, job identity, evidence fingerprint, algorithm version, current action, and
lease; completed replay requires a coherent persisted result/action. Production store methods
use these RPCs directly and do not call legacy scoring wrappers or expose the private row.
Claim now locks job then case, matching completion/failure order and removing the prior lock
cycle. The executable memory store also models the 60-second processing lease and reclaim.
Its completed replay additionally binds the current job action and checks persisted candidate
result/action coherence.

## Main Files

- `frontend/src/lib/birth-time-dynamic-actions.ts`
- `frontend/src/lib/birth-time-dynamic-special-actions.ts`
- `frontend/src/lib/birth-time-dynamic-action-replay.ts`
- `frontend/src/lib/birth-time-dynamic-action-receipt.ts`
- `frontend/src/lib/birth-time-dynamic-result-validator.ts`
- `frontend/src/lib/birth-time-dynamic-transitions.ts`
- `frontend/src/lib/birth-time-dynamic-scoring-service.ts`
- `frontend/src/lib/birth-time-dynamic-scoring-job-store.ts`
- `frontend/src/lib/birth-time-dynamic-engine-input.ts`
- `frontend/src/lib/birth-time-dynamic-service-methods.ts`
- `frontend/src/lib/birth-time-journey-service.ts`
- `frontend/src/lib/birth-time-journey-store.ts`
- `frontend/src/lib/birth-time-scoring-job.ts`
- `frontend/supabase/migrations/20260718094000_dynamic_choice_scoring_job_lifecycle.sql`
- `frontend/supabase/migrations/20260718095000_dynamic_choice_exact_action_receipts.sql`
- `frontend/tests/birth-time-dynamic-actions.test.ts`
- `frontend/tests/birth-time-dynamic-scoring.test.ts`
- `frontend/tests/birth-time-dynamic-scoring-store.test.ts`
- `frontend/tests/birth-time-dynamic-terminal.test.ts`
- `tests/test_birth_time_dynamic_scoring_job_contract.py`

## TDD Evidence

- Initial action RED: dynamic answer/generation methods and modules were absent.
- Scoring RED: the first implementation exposed legacy mutation behavior and later failed
  completed-job replay because it inspected a now-terminal action before claiming the job.
- Persistence RED: all SQL contract cases failed before the ordered v2 job migration existed.
- Assessment regression RED: a newly persisted v2 case returned a response with no
  `journeyProtocol`; GREEN now reloads and returns the stored dynamic generation turn.
- Review RED: `medium + null segment + 1/1` was accepted, claim locked case before job, and
  unmatched/pause/finish lost-response retries failed before receipt replay. Dedicated tests
  reproduced each failure before the focused fix.
- Second review RED: database duplicate-success returned on action ID alone, answer/commit did
  not write typed receipts, and TypeScript trusted a successful RPC version without comparing
  the reloaded receipt. SQL and RPC fakes now reproduce exact duplicate success, concurrent
  cross-action success, changed answer/commit payloads, lease reclaim, and corrupted completed
  result/action replay.

Final verification:

- Focused Task 6 TypeScript: **43/43 passed**.
- Route/telemetry regression subset after v2 assessment routing: **28/28 passed**.
- Full frontend TypeScript tests: **358/358 passed**.
- Dynamic action-receipt and scoring-job SQL contracts: **7/7 passed**.
- ESLint: **0 errors**, with the two pre-existing `page.tsx` hook warnings.
- `git diff --check`: passed.
- Every changed/new Task 6 TypeScript, test, and migration module is at most 250 pure LOC.
- TypeScript check reports only the known unrelated baseline at
  `frontend/tests/profile-persistence.test.ts:7` (`TS1501`, ES2018 regex under the existing
  target).

Live PostgreSQL execution was unavailable from the inherited Task 5 environment because the
Docker daemon socket was absent. The database claim is therefore limited to static SQL
token/order contracts plus executable TypeScript RPC fakes; no live-database pass is claimed.
The SQL tests do not simulate PostgreSQL locking; the lock-order assertion is structural, while
lease/reclaim behavior is executed by the typed memory store.

## Handoff

Task 7 should expose the new v2 commands through authenticated request/response schemas and
browser coordination. In particular, v2 polling must call `pollDynamicScoringJob`; the legacy
`pollScoringJob` remains legacy-only. The route change in this task only permits a fresh v2
assessment response through the existing telemetry wrapper.

Commit message: `feat: orchestrate dynamic rectification turns`

Focused review fix commit message: `fix: harden dynamic rectification orchestration`

Exact receipt fix commit message: `fix: close dynamic receipt replay gaps`
