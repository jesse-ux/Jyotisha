# Jyotisha Supabase Exit and Self-Hosted Backend Design

Date: 2026-07-20
Status: approved in conversation; awaiting written-spec review

## Goal

Replace Supabase completely with a self-hosted PostgreSQL backend while preserving every existing user and business record. Keep the current email-code login experience through Resend, add a business administration UI on a separate hostname, and prove the migration on the staging VPS before provisioning a future production server.

The current production application and Supabase project remain authoritative until a separately approved production cutover. This design does not authorize deleting, mutating, or disabling the production Supabase project.

## Confirmed decisions

- Preserve all user UUIDs, email addresses, credits, transactions, chats, profiles, chart profiles, synastry reports, rectification cases, scoring jobs, and action receipts.
- Keep passwordless email OTP login and use Resend for delivery.
- Use a Next.js modular monolith for the application backend; keep the Python API focused on astrology calculation.
- Run PostgreSQL 17 on the staging VPS without exposing a host database port.
- Use `staging.jyotisha.chat` for the staging user application and `admin.staging.jyotisha.chat` for the staging administration UI.
- Reserve `admin.jyotisha.chat` for a future production administration UI.
- Keep user and admin host-only session cookies separate.
- Build a business administration UI, not a browser-based SQL editor.
- Permit a future 10–20 minute production maintenance window.
- Do not turn `118.26.111.127` into the final production database server. A new production server will be provisioned after staging proves the design.
- Defer off-site backup setup on disposable staging. Off-site encrypted backup and a restore drill are hard gates for production.
- Add a new automatic GitHub Actions backend quality gate for pull requests and pushes to `staging`, with manual dispatch retained.

## Current coupling and migration boundary

The application is not coupled only to a PostgreSQL connection string. It currently depends on:

- Supabase Auth and `auth.users`;
- browser and server Supabase clients;
- PostgREST/Data API table access;
- RLS policies based on `auth.uid()` and `auth.jwt()`;
- `anon`, `authenticated`, and `service_role` database roles;
- security-definer RPCs for credits and rectification state transitions;
- Supabase session cookies and JWT validation.

The repository currently contains 29 Supabase migrations and many direct table/RPC calls. The exit therefore requires replacement interfaces for identity, authorization, data access, atomic business transitions, operations, and migration—not a connection-string edit.

## Chosen architecture

```text
Caddy
├── staging.jyotisha.chat
│   └── user-facing Next.js routes
└── admin.staging.jyotisha.chat
    └── isolated administration routes and login

Next.js modular monolith
├── Identity module ── Better Auth ── Resend adapter
├── Account and Credit module
├── Chat module
├── Chart Profile module
├── Synastry module
├── Rectification module
├── Admin and Audit module
├── PostgreSQL adapters ── private PostgreSQL 17
└── Astrology adapter ── private Python API
```

The user and admin surfaces share one Next.js image and container initially, but their host routing, pages, cookies, authorization checks, and navigation remain separate. This keeps the initial 2-core/4-GB server viable without coupling the module interfaces to a single deployment topology. A future deployment may split the admin surface into its own process without changing the domain modules.

## Deep module seams

Only adapters at these seams may know database tables, Better Auth internals, Resend payloads, or Python wire formats.

| Module | Interface responsibilities | Hidden implementation |
| --- | --- | --- |
| Identity | request/verify OTP, load/revoke session, require user/admin | Better Auth, Resend, identity tables, cookie configuration |
| Account and Credit | load account, reserve/complete/refund/adjust credit, redeem code | transactions, ledgers, idempotency, database functions |
| Chat | list/create/update/delete owned sessions | PostgreSQL queries and ownership policies |
| Chart Profile | CRUD for owned chart profiles | serialization, owner scoping, persistence |
| Synastry | list/create/delete owned reports | report persistence and owner scoping |
| Rectification | load and advance guarded state machines | atomic functions, jobs, receipts, concurrency guards |
| Admin and Audit | user status, session revocation, credit adjustment, codes, audit search | admin authorization, immutable audit records |
| Migration | export, transform, import, reconcile | Supabase extraction and PostgreSQL bulk loading |

Callers and tests cross the same interfaces. Raw Supabase clients, raw database clients, and table names must not escape these modules.

## PostgreSQL schemas and roles

### Schemas

- `identity`: Better Auth users, sessions, accounts, verifications, roles, and ban state.
- `public`: existing business tables, retained initially to minimize rename risk.
- `audit`: immutable administration and security events.
- `migration`: temporary import manifests and reconciliation results; production runtime roles receive no access.

Better Auth uses UUID identifiers. Existing `auth.users.id` values are inserted unchanged into `identity.users`; business foreign keys are repointed to that table. New users and sessions also use UUIDs. Supabase sessions and JWTs are not migrated, so every user re-authenticates once after cutover.

### Database roles

- `schema_owner`: owns schemas and applies reviewed migrations; never used by the running app.
- `identity_runtime`: limited to Better Auth identity tables.
- `app_runtime`: limited to required business tables/functions and subject to user-scoped policies.
- `admin_runtime`: may execute audited admin functions but cannot issue arbitrary SQL through the UI.
- `migration_runner`: temporary bulk import and reconciliation access.
- `backup_reader`: production-only read access required by backup tooling.

The application uses small independent pools for identity and business operations. Staging starts with at most five application connections per pool and no PgBouncer.

Drizzle supplies runtime query typing and the Better Auth database adapter. Reviewed plain SQL remains the migration source of truth because the application depends on PostgreSQL functions, triggers, grants, and RLS policies that must not be flattened or regenerated by an ORM migration diff.

## Authorization and RLS replacement

Removing Supabase does not mean silently deleting its authorization model.

1. The server validates a Better Auth session before entering a domain module.
2. User-scoped operations receive the authenticated UUID from trusted server context, never from a browser-owned `user_id`.
3. Each user transaction sets a transaction-local `app.user_id` PostgreSQL setting.
4. User-owned table policies read that setting and keep row isolation as defense in depth.
5. Repository queries still include explicit owner predicates; RLS is not a substitute for correct queries.
6. Admin changes execute through narrow audited functions. The admin UI does not receive a `BYPASSRLS` connection.
7. System jobs use explicit, narrowly granted functions rather than pretending to be an end user.

Every existing Supabase policy and grant must appear in a migration authorization matrix with one of three dispositions: preserved as PostgreSQL policy, replaced by server authorization plus a constrained function, or removed with a documented reason and regression test.

## Authentication and Resend

Better Auth provides UUID-backed PostgreSQL persistence and its Email OTP and Admin plugins. The initial configuration is:

- six-digit codes;
- five-minute expiry;
- three verification attempts;
- rotate and invalidate an older code on resend;
- store only a cryptographic hash of the OTP;
- rate-limit by normalized email and source IP;
- return enumeration-safe responses;
- use host-only, secure, HTTP-only, same-site cookies;
- use distinct cookie prefixes and secrets for staging and production;
- keep Resend credentials server-only.

The staging user and staging admin hosts require separate logins. Staging admin access requires a persisted admin role. `ADMIN_EMAILS` may bootstrap the first role but is not the long-term authority.

Production administration requires email OTP followed by TOTP. Staging may initially use email OTP alone while TOTP is implemented and tested before production readiness is declared.

## Business administration UI

The administration UI supports:

- user search and account inspection;
- ban/unban and session revocation;
- credit balance and ledger inspection;
- credit adjustment by appending an idempotent ledger entry, never overwriting a balance;
- redemption code generation, lookup, and deactivation;
- metadata-only inspection of chats, charts, synastry, and rectification records by default;
- database connectivity, disk utilization, and last-backup status;
- immutable audit history.

Every mutation records actor UUID, target, operation, reason, idempotency/request ID, timestamp, and before/after facts. Every `/api/admin/**` route revalidates the admin session and role on the server. Hiding a control in the browser is never treated as authorization.

## Runtime topology on staging

The staging stack contains Caddy, Next.js, Python API, and `postgres:17-alpine`. PostgreSQL uses a named volume, a health check, conservative memory/connection settings, and no published host port. SSH and Caddy remain the only public ingress paths.

The staging VPS remains disposable:

- Supabase production is the data authority.
- Local compressed, encrypted dumps are limited to the newest two or three copies.
- Local dumps are not disaster-recovery backups.
- Imports stop if disk utilization reaches 70%.
- Production data copied into staging receives the same access restrictions as production data and is deleted when the rehearsal ends.

Sustained swap use, database saturation, disk above 70%, or unacceptable request latency triggers a capacity review. The user has chosen not to upgrade the current staging VPS before those signals appear.

## Build and deployment

The VPS must not compile large application images while PostgreSQL is serving tests. GitHub Actions builds web/API images, publishes SHA tags only for discovery, and records the build outputs' immutable manifest digests in an artifact bound to the successful quality-gate run. The VPS validates that artifact and pulls digest references only.

Application deployment and database migration remain different operations:

- application deployment may pull and restart images;
- schema migration is a visible, manually approved job against the intended environment;
- data import/reconciliation is a separate migration-runner operation;
- normal deploys never run database migration implicitly.

Before switching application containers, the staging deployment workflow runs the
exact SHA web image in read-only migration-check mode. With no pending migrations
it continues automatically. With pending or drifted migrations it stops before
touching the running application. After the operator runs the manual migration
workflow successfully, that workflow dispatches staging deployment again for the
same full SHA. The check may read the migration ledger but may never apply SQL.

Deployment and migration share one Actions concurrency group and one host-side lock covering live-tree synchronization through their final database/application verification. The `main` controller owns manifest validation and remote orchestration: it requires a target SHA already present in reviewed `main` history, uploads only allowlisted controller files, and never executes deployment scripts from the target or rollback revision. Deployment records the previous application SHA, image digests, and image IDs. It rejects stale or backward automatic revisions, verifies running container image IDs/RepoDigests plus the application-reported SHA, and requires public and private health checks before updating deployed-revision state. An older application revision requires an explicit manual rollback authorization; application rollback does not claim to roll back database state.

## Automatic backend quality gate

Create `.github/workflows/backend-quality-gate.yml` with these triggers:

- `pull_request` for relevant application, migration, deployment, and workflow paths;
- `push` to `staging`;
- `workflow_dispatch`.

The user explicitly approved automatic execution for this non-production quality gate and for successful `staging` deployments. Production deployment and production migration remain manual-only.

The workflow uses a temporary PostgreSQL 17 service and generated non-production credentials. It uses a fake Resend adapter and sends no real email. It must run:

1. clean-database migration from zero;
2. Better Auth UUID and email-OTP integration tests;
3. repository ownership and RLS integration tests;
4. credit, refund, redemption, idempotency, and concurrency tests;
5. chat, chart, synastry, rectification, admin, and audit integration tests;
6. representative Supabase-export transformation and reconciliation tests;
7. frontend unit tests, lint, and production build;
8. Docker Compose rendering and health-contract checks.

Pull requests test only and cannot publish or deploy. A successful push run on `staging` is the only automatic deployment prerequisite. The deploy workflow consumes that run's immutable `head_sha`; it must not deploy a moving branch ref. New commits cancel older in-progress quality-gate runs for the same ref. Reconciliation reports and useful failure logs are uploaded as artifacts without credentials or personal data.

## Data migration strategy

### Staging rehearsal

1. Build an empty target database entirely from reviewed migrations.
2. Export selected Supabase identity columns and all required public business data without copying Supabase platform internals into runtime schemas.
3. Import users first, preserving UUID and normalized email.
4. Import dependent business tables in foreign-key order.
5. Transform Supabase grants, `auth.uid()`/`auth.jwt()` policies, and `service_role` functions into the new roles and authorization context.
6. Record source and target counts, key-set hashes, foreign-key failures, and credit-ledger reconciliation.
7. Run authenticated user and admin journeys against the imported copy.
8. On any mismatch, discard the target database and rerun from source. Do not repair an unexplained mismatch by hand.

The reconciliation gate includes, at minimum:

- exact user UUID and email sets;
- row counts for every migrated table;
- zero orphaned foreign keys;
- per-user profile, chat, chart, synastry, and rectification ownership;
- per-user credit balance equal to the accepted ledger result;
- unique request/action/idempotency identities;
- sampled semantic equality for JSON payloads and timestamps.

### Future production cutover

The future production server is provisioned separately. Before cutover it must have encrypted off-site backups, retention policy, monitoring, and a successful restore drill.

The approved cutover sequence is:

1. complete a fresh rehearsal using the production migration artifact;
2. enable maintenance mode and stop production writes;
3. take a final Supabase export and immutable backup;
4. import and reconcile the new production PostgreSQL database;
5. run OTP, account, credit, chat, chart, synastry, rectification, admin, and health smoke tests;
6. switch application configuration and domains only after reconciliation succeeds;
7. keep the former Supabase project intact and read-only during the observation window;
8. retire Supabase only under a separate reviewed decision.

If import or verification fails inside the maintenance window, the new database is abandoned and the existing application/Supabase write path is restored. Once writes begin on the new database, rollback requires a written data-reconciliation procedure; DNS rollback alone is not a database rollback.

## Failure handling

- Resend failure creates no authenticated session and returns a generic retryable error.
- OTP exhaustion invalidates the verification record and requires a new code.
- Database mutations run transactionally and expose typed domain errors, not driver messages.
- Credit and admin mutations use unique idempotency keys; retries replay the committed result.
- Migration count, UUID, foreign-key, ledger, or checksum mismatch fails closed.
- Failed staging health checks retain the prior application revision and database volume for inspection.
- Destructive automatic database rollback, volume deletion, and automatic production migration are forbidden.

## Verification strategy

- Unit tests exercise domain rules through module interfaces.
- PostgreSQL integration tests exercise the same adapters used at runtime.
- Authorization tests prove cross-user reads/writes fail at both repository and policy layers.
- Concurrency tests cover credits, refunds, codes, scoring jobs, and exact action receipts.
- Browser tests cover OTP login, logout, session expiry, user journeys, admin isolation, and TOTP before production.
- Migration tests start from representative Supabase exports and produce machine-readable reconciliation reports.
- Restore drills prove production backups can create a working database on a clean host.

## Implementation decomposition

This program is intentionally larger than one implementation plan. It is delivered through independently reviewed milestones, each ending in a runnable system and evidence-backed gate:

1. **Database and quality-gate foundation:** PostgreSQL staging topology, roles, migration runner, test fixtures, automatic backend quality workflow, and GHCR image path.
2. **Identity replacement:** Better Auth UUID schema, Resend/fake adapters, user/admin host isolation, session APIs, and Supabase-user import fixture.
3. **Business module migration:** move browser and server Supabase access behind domain interfaces. Account/credit is migrated first, then chat, charts/synastry, and rectification in separate task groups.
4. **Administration:** independent admin host, role/TOTP policy, user/session operations, credit/code tools, and immutable audit trail.
5. **Migration and reconciliation:** full export-transform-import tooling, authorization matrix, deterministic reports, and repeatable staging rehearsals.
6. **Future production readiness:** new server, off-site backups, restore drill, capacity gate, maintenance procedure, and separately approved cutover.

No milestone may remove the preceding working path until its replacement passes its own integration, migration, and rollback gates. The first implementation plan covers milestone 1 only.

## Acceptance criteria

Staging is complete only when:

- no runtime source imports `@supabase/*` or reads Supabase environment variables;
- no browser performs direct database or PostgREST access;
- all 29 legacy migration outcomes have an explicit preserved/replaced/retired disposition;
- all existing user UUIDs and business records reconcile on a staging import;
- email OTP through the Resend adapter creates a valid host-only session;
- user and admin hosts do not share cookies or authorization state;
- cross-user and non-admin access tests fail closed;
- critical atomic business flows pass concurrency tests;
- the automatic backend quality gate succeeds for the exact deployed SHA;
- the staging VPS can be rebuilt from source, migrations, and an import artifact without Supabase runtime services.

Production readiness additionally requires a new production server, encrypted off-site backups, a successful restore drill, admin TOTP, capacity validation, and a separately approved cutover plan.

## Non-goals

- Self-hosting the Supabase Docker stack.
- Turning the current staging VPS into the final production database server.
- Exposing PostgreSQL, a SQL editor, or a database dashboard publicly.
- Migrating active Supabase JWT sessions.
- Deleting the production Supabase project during staging development.
- Adding zero-downtime dual writes; the approved production path uses a short maintenance window.

## Primary references

- Better Auth database and UUID configuration: <https://better-auth.com/docs/concepts/database>
- Better Auth Email OTP: <https://better-auth.com/docs/plugins/email-otp>
- Better Auth Admin plugin: <https://better-auth.com/docs/plugins/admin>
- Better Auth Supabase migration guide: <https://better-auth.com/docs/guides/supabase-migration-guide>
- Drizzle transactions: <https://orm.drizzle.team/docs/transactions>
- Drizzle PostgreSQL RLS: <https://orm.drizzle.team/docs/rls>
- Supabase platform-to-self-hosted export concepts: <https://supabase.com/docs/guides/self-hosting/restore-from-platform>
