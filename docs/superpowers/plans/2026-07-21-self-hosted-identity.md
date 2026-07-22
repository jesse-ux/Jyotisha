# Self-Hosted Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a staging-ready, self-hosted email-OTP identity service backed by local PostgreSQL and Resend, while keeping the current Supabase identity path as the default until business data migration is complete.

**Architecture:** Better Auth is isolated behind a small identity boundary and uses only `IDENTITY_DATABASE_URL`. User and admin surfaces share identity records but use different cookie namespaces, allowed hosts, and authorization rules. A host-aware Next.js route exposes Better Auth only on the configured user/admin hosts. Existing Supabase callers remain unchanged in this milestone; switching the application-wide provider is a later, explicit migration step.

**Tech Stack:** Next.js 16 App Router, Better Auth 1.6.23, PostgreSQL 17, `pg`, Resend HTTP API, Node test runner via `tsx`.

## Global Constraints

- Keep `AUTH_PROVIDER=supabase` as the default and reject unknown provider values.
- Never expose a self-hosted session to an existing Supabase-backed business route as though it were a Supabase JWT.
- Use separate host-only cookie prefixes for user and admin surfaces; do not set a shared cookie `Domain`.
- Create all identity objects under the `identity` schema and grant access only to `identity_runtime` and `admin_runtime` as required.
- OTP values, API keys, database URLs, and raw email delivery responses must not be logged.
- CI and local tests use a fake mail sender. Real Resend calls occur only when an explicit API key and verified sender are configured.
- Every implementation task follows RED → GREEN → refactor and runs the smallest relevant test before the broader suite.
- Preserve the Supabase-exit boundaries in `docs/superpowers/specs/2026-07-20-supabase-exit-backend-design.md`; business modules, admin UI, and final cutover are outside this milestone.

---

## Task 1: Pin Better Auth and define identity configuration

**Files:**

- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Create: `frontend/src/modules/identity/config.ts`
- Create: `frontend/src/modules/identity/contracts.ts`
- Test: `frontend/tests/identity-config.test.ts`

**Interfaces:**

```ts
export type IdentitySurface = "user" | "admin";

export interface IdentityConfig {
  provider: "supabase" | "self-hosted";
  databaseUrl: string;
  userOrigin: string;
  adminOrigin: string;
  userSecret: string;
  adminSecret: string;
  resendApiKey: string;
  resendFrom: string;
}

export interface EmailOtpMessage {
  email: string;
  otp: string;
  type: "sign-in" | "email-verification" | "forget-password";
  idempotencyKey: string;
}

export interface EmailOtpSender {
  send(message: EmailOtpMessage): Promise<void>;
}
```

**Steps:**

1. Add tests that prove the provider defaults to `supabase`, `self-hosted` requires every identity/Resend setting, URLs must be HTTPS outside localhost, secrets must meet the configured minimum length, and malformed/unknown values fail without printing secret contents.
2. Run `npm test --prefix frontend -- identity-config.test.ts` and confirm failure because the configuration module does not exist.
3. Implement the typed parser with explicit environment injection and safe error messages.
4. Install the exact dependency with `npm install --prefix frontend better-auth@1.6.23` and verify the lockfile pins the intended version.
5. Rerun the focused test, then run `npm run lint --prefix frontend -- frontend/src/modules/identity frontend/tests/identity-config.test.ts`.
6. Commit as `feat(identity): define self-hosted identity configuration`.

## Task 2: Create least-privilege identity database objects

**Files:**

- Create: `frontend/db/migrations/20260721000100_self_hosted_identity.sql`
- Create: `frontend/tests/database-self-hosted-identity.test.ts`
- Modify: `frontend/tests/database-postgres-test-helper.ts` if the existing helper needs a schema query utility

**Database objects:**

- `identity.users`: UUID primary key, canonical unique email, display name/image, verified timestamp, admin role/ban fields, created/updated timestamps.
- `identity.sessions`: UUID primary key, opaque unique token, user foreign key with cascade delete, expiry, IP/user-agent, impersonation metadata, timestamps.
- `identity.accounts`: UUID primary key, provider/account identity, user foreign key, credential/token columns required by Better Auth, timestamps, unique provider/account pair.
- `identity.verifications`: UUID primary key, identifier/value, expiry, timestamps, lookup index.
- `identity.otp_rate_limits`: normalized email plus IP hash, window timestamps and attempt counters, with no plaintext OTP storage.

**Steps:**

1. Add a PostgreSQL integration test that runs the foundation and identity migrations from a clean database and asserts UUID defaults, foreign keys, canonical email uniqueness, indexes, schema ownership, and grants.
2. Prove `app_runtime` cannot read identity tables, `identity_runtime` can perform only identity operations, and `admin_runtime` has the documented administrative access.
3. Run `npm test --prefix frontend -- database-self-hosted-identity.test.ts` and confirm failure because the migration is absent.
4. Add the idempotent SQL migration with explicit grants and revoked public access.
5. Run the focused database test twice against the same database to prove migration idempotency, then run `npm run db:migrate:check --prefix frontend`.
6. Commit as `feat(identity): add local postgres identity schema`.

## Task 3: Implement fake and Resend OTP mail adapters

**Files:**

- Create: `frontend/src/modules/identity/email/fake-email-otp-sender.ts`
- Create: `frontend/src/modules/identity/email/resend-email-otp-sender.ts`
- Test: `frontend/tests/identity-email-sender.test.ts`

**Steps:**

1. Test the fake sender captures messages without network access.
2. Test the Resend adapter sends `POST https://api.resend.com/emails` with bearer authorization, `User-Agent`, JSON content, and `Idempotency-Key`; inject `fetch` so tests never contact Resend.
3. Test non-2xx responses throw a generic delivery error that excludes the API key, OTP, recipient, and raw provider response.
4. Run the focused test and confirm failure because the adapters do not exist.
5. Implement the minimum adapters and a small escaped HTML/plain-text OTP template.
6. Rerun the focused tests and lint the new files.
7. Commit as `feat(identity): add resend otp delivery adapter`.

## Task 4: Build Better Auth user/admin instances

**Files:**

- Create: `frontend/src/modules/identity/auth-factory.ts`
- Create: `frontend/src/modules/identity/auth.ts`
- Create: `frontend/src/modules/identity/model.ts`
- Test: `frontend/tests/identity-auth-factory.test.ts`

**Steps:**

1. Add tests around an injectable factory proving it selects the `identity` schema, maps Better Auth models/fields to the migration, generates UUIDs, hashes stored OTPs, uses six-digit five-minute OTPs, rotates resend codes, and caps attempts at three.
2. Add tests proving user/admin instances use distinct secrets and cookie prefixes (`jyotisha-user` and `jyotisha-admin`) with `Secure`, `HttpOnly`, and `SameSite=Lax`, and do not emit a cookie domain.
3. Add an admin authorization hook that refuses admin-surface session creation unless the persisted role includes `admin`; test ordinary users remain able to use the user surface.
4. Run `npm test --prefix frontend -- identity-auth-factory.test.ts` and confirm failure because the factory is absent.
5. Implement the factory with `better-auth`, the email OTP plugin, the admin plugin, an injected `pg.Pool`, and an injected `EmailOtpSender`.
6. Rerun focused tests and `npx tsc --noEmit -p frontend/tsconfig.json`.
7. Commit as `feat(identity): configure better auth surfaces`.

## Task 5: Add host-isolated auth routing and session DAL

**Files:**

- Create: `frontend/src/modules/identity/host.ts`
- Create: `frontend/src/modules/identity/session.ts`
- Create: `frontend/src/app/api/auth/[...all]/route.ts`
- Test: `frontend/tests/identity-host-routing.test.ts`
- Test: `frontend/tests/identity-session.test.ts`

**Steps:**

1. Test exact, port-normalized matching for configured user/admin hosts; reject unknown, suffix-confused, missing, and malformed hosts.
2. Test the route dispatches to only the matching handler and returns `421` before reading or issuing cookies on unknown hosts.
3. Test `getIdentitySession`, `requireIdentityUser`, and `requireIdentityAdmin` return narrow DTOs and perform server-side role checks; cookie presence alone must never authorize.
4. Run focused tests and confirm failure because routing/DAL modules are absent.
5. Implement `toNextJsHandler` dispatch and session helpers using awaited Next.js `headers()` at the boundary.
6. Rerun focused tests, TypeScript, and lint.
7. Commit as `feat(identity): isolate auth routes by host`.

## Task 6: Add a gated self-hosted OTP client without switching the app

**Files:**

- Create: `frontend/src/modules/identity/client.ts`
- Create: `frontend/src/components/self-hosted-login-form.tsx`
- Modify: `frontend/src/app/login/page.tsx`
- Test: `frontend/tests/identity-login-provider.test.ts`

**Steps:**

1. Add tests proving the existing Supabase login renders when the provider is absent/default and the Better Auth form renders only when the validated server configuration explicitly selects `self-hosted`.
2. Test send/verify flows use Better Auth email OTP endpoints, preserve generic account-enumeration-safe messages, prevent double submission, and never store OTP/session tokens in local storage.
3. Run focused tests and confirm failure because the self-hosted client/form are absent.
4. Implement the Better Auth browser client with `emailOTPClient` and the gated form.
5. Add an explicit warning in code/docs that `AUTH_PROVIDER=self-hosted` is integration-only until business modules stop relying on Supabase JWT/RLS.
6. Rerun focused tests, TypeScript, and lint.
7. Commit as `feat(identity): add gated self-hosted otp login`.

## Task 7: Add deterministic Supabase-auth user import tooling

**Files:**

- Create: `frontend/scripts/import-supabase-auth-users.mjs`
- Create: `frontend/tests/fixtures/supabase-auth-users.json`
- Create: `frontend/tests/identity-user-import.test.ts`

**Steps:**

1. Add tests that preserve source UUID, normalized email, verification timestamp, created/updated timestamps, and display metadata.
2. Test dry-run is the default, apply requires an explicit flag and `IDENTITY_DATABASE_URL`, duplicate canonical emails abort the entire import, reruns are idempotent, and sessions/JWTs/password hashes/provider secrets are ignored.
3. Run the focused test and confirm failure because the importer is absent.
4. Implement streaming JSON parsing for the supported export shape, one transaction, deterministic upserts, and a summary containing counts but no emails.
5. Rerun focused and database tests.
6. Commit as `feat(identity): add auth user import tool`.

## Task 8: Wire staging configuration, quality gates, and operator documentation

**Files:**

- Modify: `frontend/scripts/validate-database-env.mjs`
- Modify: `frontend/tests/database-env-validator.test.ts`
- Modify: `frontend/scripts/backend-quality-gate.mjs`
- Modify: `.github/workflows/staging-deploy.yml`
- Modify: `deploy/staging/Caddyfile`
- Modify: `deploy/staging/.env.staging.example`
- Modify: `docs/operations/staging-backend.md`
- Create: `docs/operations/self-hosted-identity.md`
- Test: `frontend/tests/staging-backend-workflows.test.ts`

**Steps:**

1. Add failing tests for the new identity/Resend variables, redacted validation output, exact admin host routing, and required identity tests in the backend gate.
2. Extend the validator and staging example with `AUTH_PROVIDER`, identity database URL, user/admin origins and secrets, and Resend settings. Document safe generation commands and verified-sender requirements without example secrets.
3. Update Caddy so `admin.staging.jyotisha.chat` can reach `/api/auth/**` and the gated login while other admin paths remain closed until the admin UI milestone.
4. Ensure deployment preflight refuses `AUTH_PROVIDER=self-hosted` unless identity migration, host separation, and Resend configuration validate; keep staging’s checked-in default as `supabase`.
5. Document smoke tests, rollback to Supabase provider, import dry-run/apply, session revocation, secret rotation, and the fact that business data remains on Supabase in this milestone.
6. Run deployment tests, database tests, and the backend quality gate.
7. Commit as `chore(identity): wire staging identity operations`.

## Task 9: Final verification and review

**Files:**

- Review every file changed since `origin/main`.

**Steps:**

1. Run `npm test --prefix frontend`.
2. Run `npm run lint --prefix frontend`.
3. Run `npx tsc --noEmit -p frontend/tsconfig.json`.
4. Run `npm run build --prefix frontend` using a non-secret build-safe environment.
5. Run `/opt/anaconda3/bin/python scripts/pre_work_check.py --remote-timeout 8 --command-timeout 45` and record any remote visibility limitation accurately.
6. Search the diff for secrets, database URLs, OTP logging, permissive cookie domains, placeholder text, and accidental Supabase-default changes.
7. Perform a code review against `origin/main`, fix all high/medium findings, rerun the affected gates, and run `git diff --check`.
8. Push `codex/self-hosted-identity`, open a PR targeting `main`, and report exact checks plus the deliberate non-cutover status.
