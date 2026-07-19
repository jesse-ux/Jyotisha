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
