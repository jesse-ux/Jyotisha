# Task 5 Report: Durable v2 Persistence and Legacy Isolation

## Outcome

Implemented durable `dynamic-choice-v2` persistence with a public/private data split. Public case rows contain only the public dynamic turn projection; the exact candidate model, persisted question binding, answers, server evidence, control state, and bounded Agent context are kept in a service-role-only companion row. Versioned turn and scoring-job writes are transactionally coordinated by service-role-only RPCs and never update `active_birth_time`.

New assessments initialize the public case, private state, and profile pointer in one database RPC transaction. Owner-scoped resume parsing requires complete v2 public/private rows and returns a strict legacy/v2 union; only absent protocol data from old legacy rows retains compatibility defaults. Active legacy cases can be upgraded without losing evidence or audit data, terminal legacy cases remain unchanged, and every legacy guided mutation entry point rejects v2 cases before writing.

The acceptance follow-up preserves an existing chart time when rectification starts, rejects split public/JSON turn versions, and routes v2 resume before any legacy scoring normalization. Legacy store inputs now accept only the strict legacy arm. Direct legacy updates include an atomic protocol predicate, while ordered service-role RPC wrappers lock the case and require `legacy-guided-v1` before invoking the former scoring or candidate transaction. Dynamic action receipts are canonicalized to lowercase in both production and the shared memory fake.

The scoring-persistence follow-up adds typed completion and failure commands that call the exact service-role RPCs, validate the returned version, reload the owner-scoped stored case, and preserve idempotent replay and stale-write behavior. It deliberately does not add stop policy, transition routing, or Task 6 orchestration.

## Files

- `frontend/supabase/migrations/20260718090000_dynamic_choice_birth_time_rectification.sql`
- `frontend/supabase/migrations/20260718091000_dynamic_choice_birth_time_transitions.sql`
- `frontend/supabase/migrations/20260718092000_legacy_scoring_protocol_guards.sql`
- `frontend/supabase/migrations/20260718093000_legacy_candidate_protocol_guards.sql`
- `frontend/src/lib/birth-time-evidence-service.ts`
- `frontend/src/lib/birth-time-guided-candidate.ts`
- `frontend/src/lib/birth-time-guided-draft-revision.ts`
- `frontend/src/lib/birth-time-journey-actions.ts`
- `frontend/src/lib/birth-time-journey-case-loader.ts`
- `frontend/src/lib/birth-time-journey-dynamic-case.ts`
- `frontend/src/lib/birth-time-journey-dynamic-persistence.ts`
- `frontend/src/lib/birth-time-journey-dynamic-state.ts`
- `frontend/src/lib/birth-time-journey-errors.ts`
- `frontend/src/lib/birth-time-journey-response.ts`
- `frontend/src/lib/birth-time-journey-service.ts`
- `frontend/src/lib/birth-time-journey-store-errors.ts`
- `frontend/src/lib/birth-time-journey-stored-protocol.ts`
- `frontend/src/lib/birth-time-journey-store.ts`
- `frontend/src/lib/birth-time-journey-turn-persistence.ts`
- `frontend/src/lib/birth-time-scoring-service.ts`
- `frontend/tests/birth-time-dynamic-persistence-fixture.ts`
- `frontend/tests/birth-time-dynamic-persistence.test.ts`
- `frontend/tests/birth-time-dynamic-resume.test.ts`
- `frontend/tests/birth-time-dynamic-scoring-memory-store.test.ts`
- `frontend/tests/birth-time-dynamic-scoring-persistence.test.ts`
- `frontend/tests/birth-time-journey-memory-store.ts`
- `frontend/tests/birth-time-journey-legacy-isolation.test.ts`
- `tests/test_birth_time_dynamic_persistence_contract.py`
- `tests/test_birth_time_journey_contract.py`

## TDD Evidence

- Migration RED: `.omo/evidence/task-5-python-red.log`
- Persistence RED: `.omo/evidence/task-5-ts-red.log`
- SQL null-state regression RED: `.omo/evidence/task-5-null-state-red.log`
- Unknown-time initialization RED: `.omo/evidence/task-5-unknown-range-red.log`
- Atomic creation RED: `.omo/evidence/task-5-atomic-create-red.log`, `.omo/evidence/task-5-atomic-create-ts-red.log`
- Legacy isolation RED: `.omo/evidence/task-5-guided-isolation-red.log`, `.omo/evidence/task-5-all-legacy-isolation-red.log`
- Memory replay RED: `.omo/evidence/task-5-memory-replay-red.log`
- Profile preservation RED: `.omo/evidence/task-5-profile-preservation-ts-red.log`, `.omo/evidence/task-5-profile-preservation-python-red.log`
- Migration GREEN: `.omo/evidence/task-5-python-green.log`
- Persistence GREEN: `.omo/evidence/task-5-ts-green.log`
- SQL null-state regression GREEN: `.omo/evidence/task-5-null-state-green.log`
- Unknown-time initialization GREEN: `.omo/evidence/task-5-unknown-range-green.log`
- Atomic creation GREEN: `.omo/evidence/task-5-atomic-create-green.log`
- Legacy isolation and replay GREEN: `.omo/evidence/task-5-memory-and-isolation-green.log`
- Profile preservation GREEN: `.omo/evidence/task-5-profile-preservation-ts-green.log`, `.omo/evidence/task-5-profile-preservation-python-green.log`

The scoring-persistence follow-up began RED with all 3 executable tests failing because the completion and failure methods did not exist. After adding only the typed persistence wrappers and memory-fake support, the same 3 tests passed GREEN.

Fresh review then reproduced a shared-fake replay mismatch: completion of one job could be returned for a different failure command at the same expected version. The fake now records the endpoint kind, canonical job identity, fingerprint, algorithm, failure code or candidate result, and returns a replay only for an equivalent operation. Two executable regressions prove exact completion/failure replay and reject changed job, endpoint, fingerprint, algorithm, failure code, or result.

The additional regressions prove that a missing current scoring action cannot pass a SQL `NOT IN` guard through three-valued `NULL` logic, that the supported unknown-time assessment initializes a valid full-day dynamic range, that SQL/public JSON turn versions cannot disagree, that v2 resume performs zero legacy writes, that an upgrade race cannot cross a legacy protocol predicate, and that uppercase UUID retries replay the stored advanced dynamic state. Executable scoring tests additionally prove exact completion/failure RPC names and payloads, returned-version parsing, owner reload, replay, stale and unknown-error propagation, and the public/private payload split without exposing an active or birth time.

## Verification

- Focused persistence, resume, scoring-job, and upgrade-race TypeScript: 33/33 passed.
- Relevant Python persistence, engine, and scoring contracts: 43/43 passed.
- Full birth-time frontend suite: 264/264 passed.
- Full frontend suite: 339/339 passed.
- Changed-file ESLint: passed.
- Changed-file Ruff: passed.
- `git diff --check`: passed.
- All changed TypeScript, test, and ordered migration modules are at most 250 pure LOC; maximum is 250.
- Full TypeScript check reports only the known unrelated baseline at `frontend/tests/profile-persistence.test.ts:7` (`TS1501`, ES2018 regex under the existing target).

Evidence:

- `.omo/evidence/task-5-python-relevant.log`
- `.omo/evidence/task-5-birth-time-suite.log`
- `.omo/evidence/task-5-frontend-full.log`
- `.omo/evidence/task-5-eslint.log`
- `.omo/evidence/task-5-ruff.log`
- `.omo/evidence/task-5-diff-check.log`
- `.omo/evidence/task-5-loc-final.log`
- `.omo/evidence/task-5-tsc.log`

## Review

Final cross-review after the identity-faithful memory replay fix: **CLEAR / APPROVE**, with no remaining blocker. The earlier untracked review artifact records the reproduced mismatch that prompted this final fix and is superseded by the passing cross-review.

Live PostgreSQL execution was not available: Docker CLI is installed, but the daemon socket does not exist. `.omo/evidence/task-5-live-postgres-unavailable.log` records the exact failure. SQL checks are therefore described only as static migration contracts; TypeScript fakes execute the RPC boundary and failure/replay semantics without claiming database execution.

Task 6 remains responsible for routing public `assess`/`resume` responses and dynamic actions through the v2 transition service. Task 5 establishes and verifies the durable store boundary those transitions use.

## Commit

Commit message: `feat: persist dynamic rectification turns`

Follow-up commit message: `fix: isolate dynamic rectification persistence`

Scoring-persistence follow-up commit message: `fix: expose dynamic scoring persistence`
