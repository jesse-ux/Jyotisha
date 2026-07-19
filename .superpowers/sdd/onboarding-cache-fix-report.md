# Onboarding cache identity final-review fix

## Outcome

- Status: `DONE_WITH_CONCERNS`
- Base SHA: `308e5d532ae10846ef196cf21eea3efc49a843dd`
- Commit: `fix: bind onboarding cache to profile identity`
- Resulting commit SHA: reported in the task handoff. A Git commit cannot embed its own resulting SHA without changing that SHA.

The onboarding cache now derives deterministic SHA-256 ready and pending versions from every
profile field used by the route's completeness/generation decision. The database version contains
no raw name, birth date/time, or location value. A ready value is accepted only for the current
profile identity, a fresh pending value blocks only that same identity, and a completion can update
the cache only while its exact pending identity still owns the row.

The claim write compares both the observed old version and the observed
`onboarding_generated_at`. The timestamp predicate preserves the existing two-minute TTL while
ensuring concurrent reclaimers cannot both acquire an expired deterministic pending identity.

The requested candidate-completion negative matrix exposed one real policy gap: the pure validator
accepted any nonempty stored owner. It now receives the authenticated user ID and requires exact
owner equality in addition to the route's owner-scoped query. No confidence, status, or billing
policy changed.

## Files

- `frontend/src/app/api/onboarding/route.ts`
- `frontend/src/lib/onboarding-cache-policy.ts`
- `frontend/tests/onboarding-cache-policy.test.ts`
- `frontend/src/app/api/birth-time-candidate-completion/route.ts`
- `frontend/src/lib/birth-time-candidate-completion.ts`
- `frontend/tests/birth-time-candidate-completion.test.ts`
- `.superpowers/sdd/onboarding-cache-fix-report.md`

Unrelated `.superpowers/sdd/task-1-report.md` and `.omo/` changes were preserved and excluded from
the staged commit.

## TDD evidence

### RED — profile-aware cache policy

The shell's bare `node` command first failed with exit 127, so it was not counted as behavioral
evidence. Using the installed Node 24.14.0 runtime:

```text
/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/onboarding-cache-policy.test.ts
```

Result before the policy module existed: exit 1, `ERR_MODULE_NOT_FOUND` for
`src/lib/onboarding-cache-policy.ts`; 0 passed, 1 failed. The missing public policy seam was the
expected RED.

### RED — candidate owner matrix

```text
/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/birth-time-candidate-completion.test.ts
```

Result before owner binding: exit 1; 13 passed, 2 failed. Both failures returned `"04:53"` instead
of `null` for (1) a case owned by another user and (2) a request authenticated as another user.

### GREEN — focused behavior

```text
/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/onboarding-cache-policy.test.ts tests/birth-time-candidate-completion.test.ts
```

Result: exit 0; 20 passed, 0 failed. Coverage includes cached A to B, active-pending A to B, stale A
completion after B claims, current ready/pending behavior, TTL reclaim, wrong case/owner, all three
result-ID positions, missing winner/time, nonterminal action, and illegal status/action pairings.

## Final verification

Full frontend tests:

```text
/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/*.test.ts
```

Result: exit 0; 444 passed, 0 failed.

Changed-file ESLint:

```text
/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node node_modules/eslint/bin/eslint.js src/app/api/onboarding/route.ts src/lib/onboarding-cache-policy.ts tests/onboarding-cache-policy.test.ts src/app/api/birth-time-candidate-completion/route.ts src/lib/birth-time-candidate-completion.ts tests/birth-time-candidate-completion.test.ts
```

Result: exit 0; zero diagnostics.

Production build with the repository's CI public placeholders and the webpack fallback:

```text
NEXT_PUBLIC_SUPABASE_URL=https://ci-placeholder.supabase.co NEXT_PUBLIC_SUPABASE_ANON_KEY=ci-placeholder PATH=/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH ./node_modules/.bin/next build --webpack
```

Result: exit 0. Next 16.2.10 compiled successfully, finished TypeScript, generated 22/22 pages,
and listed `/api/onboarding` and `/api/birth-time-candidate-completion` as dynamic routes.

Direct TypeScript diagnostic:

```text
PATH=/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH ./node_modules/.bin/tsc --noEmit
```

Result: exit 2 only for eight pre-existing ES2018 regexp-flag diagnostics in unrelated
`tests/consultation-entrypoint.test.ts` and `tests/profile-persistence.test.ts`. No changed file was
reported. The successful Next production build separately completed its TypeScript phase.

Quality checks:

```text
git diff --check
```

Result: exit 0, no output. Pure LOC counts are 182, 82, 107, 62, 38, and 173 for the six changed
TypeScript files respectively; every file is below the 200-line healthy ceiling.

Staged audit:

```text
git diff --cached --check
git diff --cached --name-status
git diff --cached --stat
```

Result: the diff check passed and the staged set contained exactly this report plus the six
TypeScript implementation/test files listed above (`539 insertions, 39 deletions`). The unrelated
modified `.superpowers/sdd/task-1-report.md` and untracked `.omo/` tree remained unstaged.

## Self-review

- Single responsibility: the new module owns only onboarding cache identity and transition policy.
- Boundary purity: the route continues parsing cache payloads with Zod before returning them; the
  policy receives the parsed payload or `null`.
- Variant discrimination: the route exhaustively switches over ready, pending, and claim.
- Privacy: persisted identities contain a version prefix plus SHA-256 only.
- Atomicity: claims compare the observed version/timestamp; completions compare the exact pending
  identity and cannot overwrite a newer profile claim.
- Inputs: the route selects all eight fields included in the fingerprint.
- Candidate policy: only the newly exposed owner mismatch changed; existing terminal/confidence
  pairings and representative-time rules remain intact.

## Concerns

- The mandatory repository pre-work command remains blocked by known host issues: system Python
  3.9 cannot import a PEP 604 annotation, system Python has no pytest, and terminal remote visibility
  is blocked. No remote-synchronization claim is made.
- Default Turbopack rejects this worktree's externally pointed `frontend/node_modules` symlink. The
  webpack production build with the exact CI public placeholders passed completely.
- The programming skill's standalone no-excuse checker could not resolve its own `typescript`
  dependency from the external skill cache. Changed-file ESLint, direct pattern audit, full tests,
  and the production TypeScript build were run instead.

---

## Integration-review follow-up

### Outcome

- Status: `DONE_WITH_CONCERNS`
- Follow-up base SHA: `e13d595d6b3130ee20647ab95b0be3e0af8bdcac`
- Follow-up commit: `fix: verify onboarding cache ownership end to end`
- Resulting follow-up SHA: reported in the task handoff because a Git commit cannot embed its own
  resulting hash without changing that hash.

`POST` now delegates to the injectable `createOnboardingPost` handler. Its stateful repository seam
executes load, version-and-timestamp claim CAS, deterministic generation, and pending-version
completion CAS as one observable HTTP workflow. The production adapter retains the real Supabase
PostgREST filters; the test fake models the same mutable single-row compare-and-set behavior.

Completion now calls `select("id").maybeSingle()` and observes the returned row. A lost pending
identity returns the safe provisional `pending` response, never the stale generated Agent payload.
Database errors retain the prior warning and terminal fallback/Agent response behavior.

### RED/GREEN evidence

Initial route-integration RED:

```text
/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/onboarding-route.test.ts
```

Result before the injectable handler existed: exit 1, `ERR_MODULE_NOT_FOUND` for
`src/lib/onboarding-post.ts`; 0 passed, 1 failed.

The first GREEN exercised two concurrent calls: A claimed and blocked in deterministic generation,
the fake profile changed to B, B claimed and completed, and A then lost its exact pending-version
completion. The handler returned B with `source=agent`, returned A with `source=pending`, and the
repository retained B's payload.

Regression-sensitivity proof temporarily removed the completion result branch and returned the
generated payload unconditionally. The focused stale test failed with actual `agent`, expected
`pending`. Restoring the ownership-result branch made the same test pass 1/1.

The stale root contract RED used the available repository environment:

```text
/Users/jesse/Downloads/Copse/astrology/yinduzhanxing/.venv/bin/python -m pytest -q tests/test_agent_chat_contract.py
```

Result before updating the contract: exit 1; 1 failed and 1 passed. The old contract still expected
the onboarding fetch in `page.tsx` and later expected removed inline version logic. The updated
contract follows the client/factory/cache modules and pins the production version CAS, timestamp
CAS, pending-version completion CAS, completion-row observation, SHA-256 identity, and default POST
delegation. Final result: 2 passed.

### Expanded matrices

- Route integration: ready A to B, active-pending A to B, stale A completion after B wins, observed
  version race, and observed timestamp race.
- Cache policy: each of the eight selected profile inputs independently changes ready and pending
  identities; TTL minus one remains pending while exact TTL reclaims; null and invalid generated
  timestamps reclaim.
- Candidate completion: missing owner, empty owner, and legal `candidate_saved` compatibility were
  added without changing confidence/status policy.

### Follow-up verification

Focused frontend tests:

```text
/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/onboarding-route.test.ts tests/onboarding-cache-policy.test.ts tests/birth-time-candidate-completion.test.ts
```

Result: exit 0; 31 passed, 0 failed.

Full frontend suite:

```text
/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/*.test.ts
```

Result: exit 0; 455 passed, 0 failed.

Changed-file ESLint: exit 0 with zero diagnostics across the route, cache/payload/handler modules,
candidate modules, stateful fake, and focused tests.

Affected Python contract: 2 passed. Changed-file Ruff initially found one extra blank line at the
existing import boundary; it was removed before final verification.

Production build:

```text
NEXT_PUBLIC_SUPABASE_URL=https://ci-placeholder.supabase.co NEXT_PUBLIC_SUPABASE_ANON_KEY=ci-placeholder PATH=/Users/jesse/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH ./node_modules/.bin/next build --webpack
```

Result: exit 0; compiled in 5.9 seconds, completed TypeScript in 10.3 seconds, and generated 22/22
pages. `/api/onboarding` remains a dynamic route.

Direct `tsc --noEmit` still reports only the same eight unrelated ES2018 regexp-flag diagnostics;
no follow-up file is reported. Pure LOC is 80 (production adapter), 184 (handler), 33 (payload), 82
(cache policy), 141 (route integration test), 75 (stateful fake), 165 (policy test), 194 (candidate
test), and 95 (root contract): every touched file remains below 200 pure LOC.

### Follow-up concerns

- The same pre-work Python 3.9/pytest and remote-visibility environment blockers remain; no remote
  synchronization is claimed.
- Default Turbopack still rejects the worktree's external dependency symlink. The complete webpack
  production build with repository-standard CI placeholders passed.

Staged follow-up audit ran `git diff --cached --check`, `--name-status`, and `--stat`. The check
passed, and the staged set contained exactly nine follow-up paths: this report, the production
route adapter, handler, payload boundary, route fake/test, policy test, candidate test, and root CI
contract. Unrelated `.superpowers/sdd/task-1-report.md` and `.omo/` remained unstaged.

## Review cleanup: behavioral authority

The post-review cleanup removes implementation-text assertions from the root Python contract and
leaves stateful TypeScript route tests as the authority for cache claim and completion behavior.
Broad UI, authentication, migration, and structured suggestion-marker coverage remains in the
Python contract; exact natural-language prompt prose is no longer pinned there.

The one-use `createOnboardingCompletionTransition` wrapper and its tautological unit test were
removed. The handler now passes `identity.pendingVersion` and `identity.readyVersion` directly to
the repository completion command. This is a refactor only, so the existing route integration
matrix provided the behavior-preservation check rather than adding a new RED case.

### Cleanup verification

- Focused route, policy, and candidate-completion tests: exit 0; 30 passed, 0 failed.
- Full frontend suite: exit 0; 454 passed, 0 failed.
- Python agent-chat contract: exit 0; 2 passed.
- Changed-file ESLint and Ruff: exit 0 with zero diagnostics.
- Webpack production build: exit 0; compiled successfully, TypeScript completed, and 22/22 pages
  generated.
- `git diff --check`: exit 0.
- Pure LOC: cache policy 70, onboarding handler 182, policy test 154, and root contract 69; every
  modified code/test file remains below 200 pure LOC.

The build continues to use repository-standard CI placeholder Supabase values and webpack because
the worktree's external dependency symlink is incompatible with default Turbopack. No new concern
was introduced by this cleanup.

## Final cleanup: remove the obsolete Python source contract

`tests/test_agent_chat_contract.py` was deleted in full. Its two tests asserted filenames,
implementation tokens, prompt prose, and source layout rather than observable outcomes. No
production logic changed and no replacement source-mirroring test was added.

### Behavioral coverage inventory

- Onboarding route ownership, generated/cache/pending responses, and compare-and-set races:
  `frontend/tests/onboarding-route.test.ts` and `frontend/tests/onboarding-cache-policy.test.ts`.
- Onboarding client recovery, authentication handling, response parsing, suggestion preservation,
  cancellation, and stale presentation rejection: `frontend/tests/onboarding-client.test.ts` and
  `frontend/tests/onboarding-presentation.test.ts`.
- Suggestion metadata removal and visible suggestion lifetime while streaming/editing:
  `frontend/tests/agent-reply.test.ts`, `frontend/tests/chat-stream-layout.test.ts`, and
  `frontend/tests/starter-questions.test.ts`.
- Public model parsing/sanitization and selected-model reservation before billing:
  `frontend/tests/model-catalog.test.ts`, `frontend/tests/public-models.test.ts`, and
  `frontend/tests/consultation-model-selection.test.ts`.
- Owned-session model persistence and per-session write serialization:
  `frontend/tests/session-model-persistence.test.ts`.
- Credit RPC outcomes plus completion/cancellation settlement of streamed consultations:
  `frontend/tests/consultation-billing.test.ts` and `frontend/tests/stream-text-response.test.ts`.

### Final cleanup verification

- Focused behavioral TypeScript inventory: exit 0; 52 passed, 0 failed.
- Full frontend suite: exit 0; 454 passed, 0 failed.
- Remaining Python suite discovery: exit 0.
- Adjacent Python auth and Supabase data contracts: exit 0; 9 passed.
- ESLint across the 12 focused TypeScript test files: exit 0 with zero diagnostics.
- Webpack production build: exit 0; compiled successfully, TypeScript completed, and 22/22 pages
  generated.
- `git diff --check`: exit 0.

The Ruff command over three untouched adjacent Python contract files found existing `I001`
import-order issues in all three. The same exploratory batch also found the existing
`test_session_management_entrypoints.py` expectation for the already-removed `onContextMenu`.
Neither is caused by deleting the agent-chat contract, and neither unrelated file was edited.
Because the only Python change is a deletion, there is no remaining modified Python file to lint.
