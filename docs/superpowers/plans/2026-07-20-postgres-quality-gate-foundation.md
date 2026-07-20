# PostgreSQL and Backend Quality-Gate Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the self-hosted PostgreSQL staging foundation, least-privilege roles, reviewed SQL migration runner, automatic backend quality gate, immutable GHCR images, and exact-SHA staging deploy path without moving authentication or business traffic off Supabase.

**Architecture:** PostgreSQL 17 runs on the private Compose network of the Hong Kong staging VPS. A separate deployment-user-owned database env file supplies bootstrap and schema credentials only to PostgreSQL and an opt-in migrator; normal web/API containers never receive them. Reviewed plain SQL is the schema source of truth, while `pg` and Drizzle provide the future runtime seam. PRs and `staging` pushes run database/backend/frontend/configuration tests; successful `staging` pushes publish web/API images and a run-bound SHA-to-digest manifest, and staging deploys only those exact digests. Migrations remain a separate manual workflow.

**Tech Stack:** PostgreSQL 17 Alpine, Docker Compose, Node.js 22, Next.js 16, TypeScript, `pg`, Drizzle ORM, Python 3.12, GitHub Actions, GHCR, Bash, OpenSSL.

## Global Constraints

- Scope is only Milestone 1 of `docs/superpowers/specs/2026-07-20-supabase-exit-backend-design.md`.
- Prerequisite: merge `codex/staging-deployment-automation` commit `801666a6c71b8efc220afa4248f42c5c776ba9e6` into `main`, then create the implementation worktree from that updated `main`.
- Before starting, these prerequisite files must exist: `.github/workflows/deploy-staging.yml`, `deploy/Caddyfile.staging`, and `deploy/validate-staging-env.sh`.
- Supabase remains source of truth. Do not add Better Auth, identity cutover, admin UI, dual writes, or business-table migration in this milestone.
- Staging PostgreSQL has no published port. Only the CI overlay may bind a loopback port.
- `.env.staging.database` is server-side only, mode `0600`, and excluded from Git/rsync. It contains bootstrap and migration credentials. `.env.staging` must not contain them.
- Normal web/API containers never receive `SCHEMA_DATABASE_URL`.
- App deployment never runs schema migration. Migration is manual and separately serialized.
- Before changing app containers, staging deploy runs the exact SHA image in read-only migration-check mode. No pending migration means automatic continuation. Pending or checksum-drifted migration stops before app changes; a successful manual migration dispatches staging deploy again for the same full SHA.
- Production defaults remain manual-only and unchanged.
- Staging publication uses full Git SHA tags for discovery, but deployment is
  authorized and pinned by the build outputs' `sha256` manifest digests. Never
  deploy a mutable tag such as `latest`, or treat a tag alone as image identity.
- The `main` workflow revision is the trusted deployment controller. Target and
  rollback SHAs must already be ancestors of reviewed `main`; their code is
  represented by the digest-pinned images, but their validators and remote
  orchestration scripts are never executed with staging Environment privileges.
- Finish each task with the focused commit shown.

## Planned Files

```text
.github/workflows/backend-quality-gate.yml
.github/workflows/deploy-staging.yml
.github/workflows/migrate-staging-database.yml
deploy/backup-staging-postgres.sh
deploy/docker-compose.postgres-ci.yml
deploy/docker-compose.postgres.yml
deploy/docker-compose.server.yml
deploy/postgres/001-bootstrap-roles.sh
deploy/validate-staging-database-env.sh
frontend/db/migrations/20260720000100_backend_foundation.sql
frontend/scripts/db-migrate.mjs
frontend/src/lib/db/client.ts
frontend/src/lib/db/config.ts
frontend/tests/database-backup.test.ts
frontend/tests/database-foundation.test.ts
frontend/tests/database-topology.test.ts
frontend/tests/helpers/postgres-fixture.ts
frontend/tests/staging-backend-workflows.test.ts
```

---

### Task 1: Private PostgreSQL topology and roles

**Files:**

- Create: `deploy/docker-compose.postgres.yml`
- Create: `deploy/docker-compose.postgres-ci.yml`
- Create: `deploy/postgres/001-bootstrap-roles.sh`
- Create: `deploy/validate-staging-database-env.sh`
- Create: `frontend/tests/helpers/postgres-fixture.ts`
- Create: `frontend/tests/database-topology.test.ts`
- Modify: `frontend/package.json`

- [ ] **Step 1: Verify prerequisite**

```bash
git merge-base --is-ancestor 801666a6c71b8efc220afa4248f42c5c776ba9e6 HEAD
test -f .github/workflows/deploy-staging.yml
test -f deploy/Caddyfile.staging
test -x deploy/validate-staging-env.sh
```

Expected: all exit `0`. Otherwise stop; do not duplicate the prerequisite branch.

- [ ] **Step 2: Write the failing topology test**

Add `frontend/tests/helpers/postgres-fixture.ts` exporting:

```ts
export type PostgresFixture = {
  projectName: string;
  databaseEnvFile: string;
  hostPort: number;
  connectionUrl(role: string, password: string): string;
  psql(sql: string): string;
  stop(): void;
};
export function startPostgresFixture(): PostgresFixture;
```

It creates a mode-`0600` temp env, chooses an unused port from `55432..55531`, starts Compose with the two files below and `--wait postgres`, and always runs `down -v --remove-orphans` in `stop()`. Use only these deterministic test values:

```text
POSTGRES_DB=jyotisha
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres-test-password
SCHEMA_OWNER_PASSWORD=schema-owner-test-password
IDENTITY_RUNTIME_PASSWORD=identity-runtime-test-password
APP_RUNTIME_PASSWORD=app-runtime-test-password
ADMIN_RUNTIME_PASSWORD=admin-runtime-test-password
MIGRATION_RUNNER_PASSWORD=migration-runner-test-password
BACKUP_READER_PASSWORD=backup-reader-test-password
STAGING_BACKUP_ENCRYPTION_KEY=staging-backup-test-password
SCHEMA_DATABASE_URL=postgresql://schema_owner:schema-owner-test-password@postgres:5432/jyotisha
```

Add `frontend/tests/database-topology.test.ts`:

```ts
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { startPostgresFixture } from "./helpers/postgres-fixture";

test("staging postgres is private and CI binds loopback only", () => {
  const staging = readFileSync("../deploy/docker-compose.postgres.yml", "utf8");
  const ci = readFileSync("../deploy/docker-compose.postgres-ci.yml", "utf8");
  assert.match(staging, /image:\s*postgres:17-alpine/);
  assert.doesNotMatch(staging, /^\s+ports:/m);
  assert.match(ci, /127\.0\.0\.1:\$\{POSTGRES_HOST_PORT:-55432\}:5432/);
});

test("database roles have no cluster privileges", () => {
  const fixture = startPostgresFixture();
  try {
    assert.equal(
      fixture.psql(`
        select rolname || ':' || rolsuper || ':' || rolcreatedb || ':' ||
               rolcreaterole || ':' || rolbypassrls
        from pg_roles
        where rolname in ('schema_owner','identity_runtime','app_runtime',
          'admin_runtime','migration_runner','backup_reader')
        order by rolname
      `),
      [
        "admin_runtime:f:f:f:f",
        "app_runtime:f:f:f:f",
        "backup_reader:f:f:f:f",
        "identity_runtime:f:f:f:f",
        "migration_runner:f:f:f:f",
        "schema_owner:f:f:f:f",
      ].join("\n"),
    );
  } finally {
    fixture.stop();
  }
});
```

Add:

```json
"test:db": "tsx --test --test-concurrency=1 tests/database-*.test.ts"
```

- [ ] **Step 3: Confirm red**

```bash
cd frontend && npm run test:db
```

Expected: FAIL because the Compose topology does not exist.

- [ ] **Step 4: Add staging and CI Compose files**

Create `deploy/docker-compose.postgres.yml`:

```yaml
services:
  postgres:
    image: postgres:17-alpine
    restart: unless-stopped
    shm_size: 128mb
    env_file:
      - ${DATABASE_ENV_FILE:-../.env.staging.database}
    command:
      - postgres
      - -c
      - max_connections=30
      - -c
      - shared_buffers=256MB
      - -c
      - effective_cache_size=1GB
      - -c
      - work_mem=4MB
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/001-bootstrap-roles.sh:/docker-entrypoint-initdb.d/001-bootstrap-roles.sh:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \"$${POSTGRES_USER}\" -d \"$${POSTGRES_DB}\""]
      interval: 5s
      timeout: 5s
      retries: 20
      start_period: 10s
    networks: [app]

  migrator:
    image: ${WEB_IMAGE:-jyotisha-web:local}
    profiles: ["migration"]
    restart: "no"
    env_file:
      - ${DATABASE_ENV_FILE:-../.env.staging.database}
    working_dir: /app/frontend
    command: ["npm", "run", "db:migrate"]
    depends_on:
      postgres:
        condition: service_healthy
    networks: [app]

  migration-checker:
    image: ${WEB_IMAGE:-jyotisha-web:local}
    profiles: ["migration-check"]
    restart: "no"
    env_file:
      - ${DATABASE_ENV_FILE:-../.env.staging.database}
    working_dir: /app/frontend
    command: ["npm", "run", "db:migrate:check"]
    depends_on:
      postgres:
        condition: service_healthy
    networks: [app]

volumes:
  postgres_data:

networks:
  app:
```

Create `deploy/docker-compose.postgres-ci.yml`:

```yaml
services:
  postgres:
    ports:
      - "127.0.0.1:${POSTGRES_HOST_PORT:-55432}:5432"
```

- [ ] **Step 5: Implement idempotent role bootstrap**

Create executable `deploy/postgres/001-bootstrap-roles.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
set +x

required=(
  POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD
  SCHEMA_OWNER_PASSWORD IDENTITY_RUNTIME_PASSWORD APP_RUNTIME_PASSWORD
  ADMIN_RUNTIME_PASSWORD MIGRATION_RUNNER_PASSWORD BACKUP_READER_PASSWORD
)
for key in "${required[@]}"; do
  if [ -z "${!key:-}" ]; then
    echo "required database bootstrap variable is missing: $key" >&2
    exit 1
  fi
done

psql --set ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --set database_name="$POSTGRES_DB" \
  --set schema_owner_password="$SCHEMA_OWNER_PASSWORD" \
  --set identity_runtime_password="$IDENTITY_RUNTIME_PASSWORD" \
  --set app_runtime_password="$APP_RUNTIME_PASSWORD" \
  --set admin_runtime_password="$ADMIN_RUNTIME_PASSWORD" \
  --set migration_runner_password="$MIGRATION_RUNNER_PASSWORD" \
  --set backup_reader_password="$BACKUP_READER_PASSWORD" <<'SQL'
SELECT format(
  'CREATE ROLE schema_owner WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L',
  :'schema_owner_password'
) WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'schema_owner'
) \gexec
SELECT format(
  'CREATE ROLE identity_runtime WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L',
  :'identity_runtime_password'
) WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'identity_runtime'
) \gexec
SELECT format(
  'CREATE ROLE app_runtime WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L',
  :'app_runtime_password'
) WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'app_runtime'
) \gexec
SELECT format(
  'CREATE ROLE admin_runtime WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L',
  :'admin_runtime_password'
) WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'admin_runtime'
) \gexec
SELECT format(
  'CREATE ROLE migration_runner WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L',
  :'migration_runner_password'
) WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'migration_runner'
) \gexec
SELECT format(
  'CREATE ROLE backup_reader WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L',
  :'backup_reader_password'
) WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'backup_reader'
) \gexec

SELECT format(
  'GRANT CONNECT, CREATE ON DATABASE %I TO schema_owner',
  :'database_name'
) \gexec
SELECT format(
  'GRANT CONNECT ON DATABASE %I TO identity_runtime, app_runtime, admin_runtime, migration_runner, backup_reader',
  :'database_name'
) \gexec
SQL
```

Run `chmod +x deploy/postgres/001-bootstrap-roles.sh`. Do not grant role membership, `BYPASSRLS`, database ownership, or public-schema creation.

- [ ] **Step 6: Add database-env validator**

Create executable `deploy/validate-staging-database-env.sh`. Reuse the safe parser pattern in `validate-staging-env.sh`, never `source`/`eval`. Require exactly once and non-empty:

```text
POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD
SCHEMA_OWNER_PASSWORD IDENTITY_RUNTIME_PASSWORD APP_RUNTIME_PASSWORD
ADMIN_RUNTIME_PASSWORD MIGRATION_RUNNER_PASSWORD BACKUP_READER_PASSWORD
STAGING_BACKUP_ENCRYPTION_KEY SCHEMA_DATABASE_URL
```

Reject missing files, symlinks, foreign ownership, or mode other than `600`. Require `POSTGRES_DB=jyotisha`, `POSTGRES_USER=postgres`, and a schema URL shaped as `postgresql://schema_owner:<encoded>@postgres:5432/jyotisha`. Print values never; success output is exactly `staging database environment validated`.

- [ ] **Step 7: Verify**

```bash
chmod +x deploy/postgres/001-bootstrap-roles.sh \
  deploy/validate-staging-database-env.sh
cd frontend && npm run test:db
```

Expected: PASS and fixture volumes removed.

- [ ] **Step 8: Commit**

```bash
git add deploy/docker-compose.postgres.yml deploy/docker-compose.postgres-ci.yml \
  deploy/postgres/001-bootstrap-roles.sh deploy/validate-staging-database-env.sh \
  frontend/tests/helpers/postgres-fixture.ts frontend/tests/database-topology.test.ts \
  frontend/package.json
git commit -m "feat: add private staging postgres topology"
```

---

### Task 2: Reviewed SQL migrations and runtime DB seam

**Files:**

- Create: `frontend/scripts/db-migrate.mjs`
- Create: `frontend/db/migrations/20260720000100_backend_foundation.sql`
- Create: `frontend/src/lib/db/config.ts`
- Create: `frontend/src/lib/db/client.ts`
- Create: `frontend/tests/database-foundation.test.ts`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Modify: `deploy/railway-web.Dockerfile`

- [ ] **Step 1: Write failing tests**

`frontend/tests/database-foundation.test.ts` must test:

1. `readDatabaseUrl({}, "APP_DATABASE_URL")` throws `APP_DATABASE_URL is required`.
2. First `node scripts/db-migrate.mjs` applies one file and records a 64-character checksum.
3. Second run is a no-op with the same ledger row.
4. Applying a copied migration directory, changing one byte, then rerunning exits non-zero with `migration checksum mismatch: <filename>`.
5. `app_runtime` cannot `CREATE SCHEMA` or select `migration.schema_migrations`.
6. Test stderr/output never includes any fixture password.

Spawn the runner with only `SCHEMA_DATABASE_URL` and optional `MIGRATIONS_DIRECTORY`.

- [ ] **Step 2: Confirm red**

```bash
cd frontend && npm run test:db
```

Expected: FAIL on missing runner/config/migration.

- [ ] **Step 3: Install runtime packages**

```bash
cd frontend
npm install pg drizzle-orm
npm install --save-dev @types/pg
```

Add `"db:migrate": "node scripts/db-migrate.mjs"` and
`"db:migrate:check": "node scripts/db-migrate.mjs --check"`.

- [ ] **Step 4: Add typed URL config and lazy client**

Create `frontend/src/lib/db/config.ts`:

```ts
export type DatabaseUrlKey =
  | "IDENTITY_DATABASE_URL"
  | "APP_DATABASE_URL"
  | "ADMIN_DATABASE_URL";

export function readDatabaseUrl(
  env: NodeJS.ProcessEnv,
  key: DatabaseUrlKey,
): string {
  const value = env[key]?.trim();
  if (!value) throw new Error(`${key} is required`);
  if (!value.startsWith("postgresql://")) {
    throw new Error(`${key} must be a PostgreSQL URL`);
  }
  return value;
}
```

Create `frontend/src/lib/db/client.ts`:

```ts
import { drizzle, type NodePgDatabase } from "drizzle-orm/node-postgres";
import { Pool } from "pg";

export type DomainDatabase = { pool: Pool; db: NodePgDatabase };

export function createDomainDatabase(
  connectionString: string,
  maxConnections = 5,
): DomainDatabase {
  const pool = new Pool({
    connectionString,
    max: maxConnections,
    idleTimeoutMillis: 30_000,
    connectionTimeoutMillis: 5_000,
    application_name: "jyotisha-web",
  });
  return { pool, db: drizzle(pool) };
}
```

Do not instantiate a global pool yet.

- [ ] **Step 5: Implement `db-migrate.mjs`**

Export:

```js
export async function runMigrations({
  connectionString,
  migrationsDirectory,
  logger = console,
}) {}
```

Required behavior:

- Accept only sorted `/^\d{14}_[a-z0-9_]+\.sql$/` files.
- SHA-256 exact file bytes.
- One `pg.Client`.
- Acquire `select pg_advisory_lock(hashtext('jyotisha_schema_migrations'))`.
- Create `migration` owned by `schema_owner`, revoke public access, and create:

```sql
create table if not exists migration.schema_migrations (
  filename text primary key,
  checksum text not null check (length(checksum) = 64),
  applied_at timestamptz not null default now()
);
```

- Matching row: log `already applied <filename>`.
- Changed checksum: throw `migration checksum mismatch: <filename>`.
- New file: `BEGIN`, execute file, insert ledger row, `COMMIT`; rollback on error.
- With `--check`, perform no DDL/DML: compare exact files with the existing ledger, print pending filenames only, exit `0` when current, exit `3` when any file is pending, and exit `1` on checksum drift or unsafe failure. A missing ledger means every file is pending.
- Release lock and close in `finally`.
- Never log URL, SQL, env, or driver config.
- Direct invocation defaults to `frontend/db/migrations`, requires `SCHEMA_DATABASE_URL`, prints safe filename-only errors, and exits `1`.

- [ ] **Step 6: Add foundation migration**

Create `frontend/db/migrations/20260720000100_backend_foundation.sql`:

```sql
create schema if not exists identity authorization schema_owner;
create schema if not exists audit authorization schema_owner;
revoke all on schema public from public;
revoke all on schema identity from public;
revoke all on schema audit from public;
grant usage on schema identity to identity_runtime, admin_runtime;
grant usage on schema public to app_runtime, admin_runtime;
grant usage on schema audit to admin_runtime;

alter default privileges for role schema_owner in schema identity
  revoke all on tables from public;
alter default privileges for role schema_owner in schema public
  revoke all on tables from public;
alter default privileges for role schema_owner in schema audit
  revoke all on tables from public;
```

Do not create business or auth tables. The foundation grants schema discovery only;
later reviewed migrations grant access to named tables and narrow functions. Never
grant runtime roles broad default DML on future tables.

- [ ] **Step 7: Put runner in final web image**

Before the existing `RUN npm run build && npm prune --omit=dev` line in the single-stage `deploy/railway-web.Dockerfile`, add:

```dockerfile
COPY frontend/scripts ./scripts
COPY frontend/db ./db
```

Keep `pg` in production dependencies.

- [ ] **Step 8: Verify**

```bash
cd frontend && npm run test:db
cd ..
docker build -f deploy/railway-web.Dockerfile \
  --build-arg NEXT_PUBLIC_SUPABASE_URL=https://placeholder.supabase.co \
  --build-arg NEXT_PUBLIC_SUPABASE_ANON_KEY=placeholder \
  -t jyotisha-web:migration-foundation .
docker run --rm --entrypoint node jyotisha-web:migration-foundation \
  scripts/db-migrate.mjs
```

Expected: tests and build PASS; last command exits `1` with only `SCHEMA_DATABASE_URL is required`.

- [ ] **Step 9: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/scripts/db-migrate.mjs \
  frontend/db/migrations/20260720000100_backend_foundation.sql \
  frontend/src/lib/db/config.ts frontend/src/lib/db/client.ts \
  frontend/tests/database-foundation.test.ts deploy/railway-web.Dockerfile
git commit -m "feat: add reviewed postgres migration foundation"
```

---

### Task 3: Encrypted local staging backups

**Files:**

- Create: `deploy/backup-staging-postgres.sh`
- Create: `frontend/tests/database-backup.test.ts`

- [ ] **Step 1: Write failing integration test**

Start the Postgres fixture, run the backup script four times with deterministic `BACKUP_TIMESTAMP` values, then assert:

- Each invocation exits `0`.
- Completed names match `jyotisha-staging-YYYYMMDDTHHMMSSZ.dump.enc`.
- No `.partial` remains and only the newest three encrypted files remain.
- Decryption with `openssl enc -d -aes-256-cbc -pbkdf2` produces a dump accepted by `pg_restore --list`.
- Output contains no fixture passwords.

- [ ] **Step 2: Confirm red**

```bash
cd frontend && npm run test:db
```

Expected: FAIL because the script is absent.

- [ ] **Step 3: Implement backup script**

Interface:

```text
backup-staging-postgres.sh DATABASE_ENV_FILE BACKUP_DIRECTORY
```

Use `set -euo pipefail`, `set +x`, validate the env first, refuse disk usage `>=70%`, create directory `0700`, output file `0600`, and run:

```bash
DATABASE_ENV_FILE="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
export DATABASE_ENV_FILE
docker compose -p "${COMPOSE_PROJECT_NAME:-jyotisha-staging}" \
  -f deploy/docker-compose.postgres.yml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner |
openssl enc -aes-256-cbc -salt -pbkdf2 \
  -pass env:STAGING_BACKUP_ENCRYPTION_KEY > "$PARTIAL_FILE"
```

Atomically rename after success. Delete only older matching dumps inside the explicit backup directory, retaining three. Print path/count only.

- [ ] **Step 4: Verify and commit**

```bash
chmod +x deploy/backup-staging-postgres.sh
cd frontend && npm run test:db
cd ..
git add deploy/backup-staging-postgres.sh frontend/tests/database-backup.test.ts
git commit -m "feat: add encrypted staging database backups"
```

---

### Task 4: Automatic backend gate and GHCR publishing

**Files:**

- Create: `.github/workflows/backend-quality-gate.yml`
- Create: `frontend/tests/staging-backend-workflows.test.ts`
- Modify: `frontend/package.json`

- [ ] **Step 1: Write failing workflow contracts**

Assert the new workflow:

- Is named `Staging Backend Quality Gate`.
- Runs on PR, push to `staging`, and manual dispatch.
- Cancels superseded same-ref runs.
- Runs `npm run test:db`, frontend tests/lint/build, and the exact passing Python quick gate from `.github/workflows/ci.yml`.
- Publishes only after validation and only on `staging` push.
- Gives `packages: write` only to publish.
- Pushes web/API tags with `${{ github.sha }}` and no `latest`.

Add:

```json
"test:deployment": "tsx --test tests/health-deployment.test.ts tests/staging-backend-workflows.test.ts"
```

- [ ] **Step 2: Confirm red**

```bash
cd frontend && npm run test:deployment
```

- [ ] **Step 3: Create workflow**

Use this job structure:

```yaml
name: Staging Backend Quality Gate
on:
  pull_request:
  push:
    branches: [staging]
  workflow_dispatch:
concurrency:
  group: backend-quality-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
permissions:
  contents: read
jobs:
  validate:
    runs-on: ubuntu-latest
    timeout-minutes: 30
  publish:
    if: github.event_name == 'push' && github.ref == 'refs/heads/staging'
    needs: validate
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
```

Validation checks out, sets Python `3.12` and Node `22`, installs with `python -m pip install -r requirements.txt -r requirements-dev.txt` and `npm ci --prefix frontend`, then runs the exact existing Python gate:

```bash
ruff check scripts/run_quality_gate.py tests/test_varga_bphs.py \
  tests/test_ashtakavarga_invariants.py tests/test_cli_smoke.py \
  tests/test_yoga_rules_integrity.py
python -m py_compile scripts/*.py jyotish_vedic/*.py mcp_server.py
mkdir -p artifacts
python scripts/run_quality_gate.py \
  --profile quick --skip-yoga-logic --skip-frontend-runtime \
  2>&1 | tee artifacts/quick-quality-gate.log
python -m build --no-isolation
```

It then runs `npm run test:db`, `npm test`, `npm run lint`, and `npm run build` with non-production Supabase placeholders. Upload `artifacts/quick-quality-gate.log` with `if: always()`.

Publish logs into GHCR using `GITHUB_TOKEN`, then use `docker/build-push-action@v6`. The API build uses repository context `.` with `file: deploy/railway-api.Dockerfile`:

```yaml
tags: ghcr.io/jesse-ux/jyotisha-api:${{ github.sha }}
```

The web build uses repository context `.` with `file: deploy/railway-web.Dockerfile`:

```yaml
tags: ghcr.io/jesse-ux/jyotisha-web:${{ github.sha }}
build-args: |
  NEXT_PUBLIC_SUPABASE_URL=https://placeholder.supabase.co
  NEXT_PUBLIC_SUPABASE_ANON_KEY=placeholder
```

- [ ] **Step 4: Verify and commit**

```bash
cd frontend
npm run test:deployment
npm run test:db
npm test
npm run lint
NEXT_PUBLIC_SUPABASE_URL=https://placeholder.supabase.co \
NEXT_PUBLIC_SUPABASE_ANON_KEY=placeholder npm run build
cd ..
ruff check scripts/run_quality_gate.py tests/test_varga_bphs.py \
  tests/test_ashtakavarga_invariants.py tests/test_cli_smoke.py \
  tests/test_yoga_rules_integrity.py
python -m py_compile scripts/*.py jyotish_vedic/*.py mcp_server.py
python scripts/run_quality_gate.py \
  --profile quick --skip-yoga-logic --skip-frontend-runtime
python -m build --no-isolation
git add .github/workflows/backend-quality-gate.yml \
  frontend/tests/staging-backend-workflows.test.ts frontend/package.json
git commit -m "ci: add automatic backend quality gate"
```

Expected: all commands PASS.

---

### Task 5: Exact-image staging deployment

**Files:**

- Modify: `deploy/docker-compose.server.yml`
- Modify: `.github/workflows/deploy-staging.yml`
- Modify: `frontend/tests/health-deployment.test.ts`
- Modify: `frontend/tests/staging-backend-workflows.test.ts`

- [ ] **Step 1: Add failing contracts**

Assert:

- Base Compose has `image: ${API_IMAGE:-jyotisha-api:local}` and `image: ${WEB_IMAGE:-jyotisha-web:local}`, while retaining both `build:` blocks.
- Staging listens to successful `Staging Backend Quality Gate`; manual validation queries `backend-quality-gate.yml` for exact SHA.
- Every staging Compose invocation uses server and Postgres files plus explicit app/database env, Caddyfile, hostname, API image, and web image.
- Workflow logs into GHCR, pulls, and runs `up -d --no-build`.
- It never invokes the applying `db:migrate` command, `migrator` service, or `--profile migration`.
- It runs the exact web image through `migration-checker`/`db:migrate:check` before changing any app container.
- Pending migrations stop before `api`, `web`, or `caddy` changes and print the manual workflow name plus exact SHA.
- Rollback uses recorded prior digest references, image IDs, and SHA.

- [ ] **Step 2: Confirm red**

```bash
cd frontend && npm run test:deployment
```

- [ ] **Step 3: Add image indirection**

Keep build definitions and add:

```yaml
services:
  api:
    image: ${API_IMAGE:-jyotisha-api:local}
  web:
    image: ${WEB_IMAGE:-jyotisha-web:local}
```

No-selector production invocations must still build locally.

- [ ] **Step 4: Update workflow**

- Listen to `["Staging Backend Quality Gate"]`.
- Manual API lookup uses `/actions/workflows/backend-quality-gate.yml/runs`.
- Add `packages: read`.
- Pin every remote Compose call with:

```text
APP_ENV_FILE=../.env.staging
DATABASE_ENV_FILE=../.env.staging.database
CADDYFILE_PATH=./Caddyfile.staging
SITE_ADDRESS=staging.jyotisha.chat
API_IMAGE=ghcr.io/jesse-ux/jyotisha-api@sha256:<manifest-digest>
WEB_IMAGE=ghcr.io/jesse-ux/jyotisha-web@sha256:<manifest-digest>
```

- Validate both env files and Compose config.
- Send GHCR token through `docker login --password-stdin`; never save it in either env file.
- Pull `api web postgres`, start/wait for PostgreSQL, then run the exact web image through `--profile migration-check run --rm migration-checker`.
- Continue to `up -d --no-build --remove-orphans` only after check exit `0`; treat exit `3` as a safe stop with no application changes.
- Download and validate the successful gate run's SHA-to-digest manifest. Record
  prior container digest references, image IDs, and SHA before switching. Roll
  back with those exact digest references and `--no-build`.
- Log out in an always-running cleanup step.
- Never run migrations.

- [ ] **Step 5: Verify production/staging compatibility**

```bash
cd frontend && npm run test:deployment
cd ..
docker compose --env-file "$APP_ENV_FIXTURE" \
  -f deploy/docker-compose.server.yml config --quiet
DATABASE_ENV_FILE="$DATABASE_ENV_FIXTURE" \
docker compose --env-file "$APP_ENV_FIXTURE" \
  -f deploy/docker-compose.server.yml \
  -f deploy/docker-compose.postgres.yml config --quiet
```

Expected: contracts PASS and both configs validate.

- [ ] **Step 6: Commit**

```bash
git add deploy/docker-compose.server.yml .github/workflows/deploy-staging.yml \
  frontend/tests/health-deployment.test.ts \
  frontend/tests/staging-backend-workflows.test.ts
git commit -m "ci: deploy immutable staging images"
```

---

### Task 6: Separate manual staging migration workflow

**Files:**

- Create: `.github/workflows/migrate-staging-database.yml`
- Modify: `frontend/tests/staging-backend-workflows.test.ts`

- [ ] **Step 1: Add failing contracts**

Assert manual-only dispatch, full 40-character SHA, `staging` environment, successful exact-SHA backend gate, pinned web image, both env validators, Postgres-only start, `--profile migration run --rm migrator`, filename-only ledger output, and no web/API/Caddy restart. Also assert that success dispatches `deploy-staging.yml` with the same full SHA.

- [ ] **Step 2: Confirm red**

```bash
cd frontend && npm run test:deployment
```

- [ ] **Step 3: Create workflow**

Header:

```yaml
name: Migrate Staging Database
on:
  workflow_dispatch:
    inputs:
      deploy_sha:
        description: Full tested commit SHA to migrate
        required: true
        type: string
concurrency:
  group: staging-mutation
  cancel-in-progress: false
permissions:
  contents: read
  actions: write
  packages: read
jobs:
  migrate:
    environment: staging
    runs-on: ubuntu-latest
    timeout-minutes: 20
```

Use the same pinned host/user/path/known-host logic as staging deploy. Reject non-`^[0-9a-f]{40}$`, require a successful backend gate for that SHA on `staging`, check it out, and rsync without `.env*`.

Remote sequence:

```bash
deploy/validate-staging-env.sh \
  .env.staging staging.jyotisha.chat deploy/Caddyfile.staging
deploy/validate-staging-database-env.sh .env.staging.database

DATABASE_ENV_FILE=../.env.staging.database \
docker compose -p jyotisha-staging \
  -f deploy/docker-compose.postgres.yml up -d --wait postgres

DATABASE_ENV_FILE=../.env.staging.database \
WEB_IMAGE="ghcr.io/jesse-ux/jyotisha-web:$DEPLOY_SHA" \
docker compose -p jyotisha-staging \
  -f deploy/docker-compose.postgres.yml \
  --profile migration run --rm migrator

docker compose -p jyotisha-staging \
  -f deploy/docker-compose.postgres.yml exec -T postgres \
  psql -U postgres -d jyotisha -Atc \
  'select filename from migration.schema_migrations order by filename'
```

Authenticate GHCR through stdin using run-local Docker state and remove it in
cleanup. Do not start/restart app services. Deployment and migration share the
`staging-mutation` concurrency group and the host mutation lock. After migration
and ledger reporting succeed, recheck that `staging` still points at the validated
SHA, then call the GitHub workflow-dispatch API for `deploy-staging.yml` with the
`main` controller ref, `inputs.deploy_sha` equal to that full SHA, and
`inputs.allow_rollback` set to `false`.

- [ ] **Step 4: Verify and commit**

```bash
cd frontend && npm run test:deployment
cd ..
git add .github/workflows/migrate-staging-database.yml \
  frontend/tests/staging-backend-workflows.test.ts
git commit -m "ci: add manual staging database migrations"
```

---

### Task 7: Operations runbook

**Files:**

- Modify: `deploy/README.md`
- Modify: `frontend/tests/staging-backend-workflows.test.ts`

- [ ] **Step 1: Add failing documentation contracts**

Require the runbook to cover two mode-`0600` env files, exact database keys, private Postgres, manual migration order, automatic PR/`staging` gate, three encrypted local backups, no offsite staging recovery, and no production cutover authorization.

- [ ] **Step 2: Confirm red**

```bash
cd frontend && npm run test:deployment
```

- [ ] **Step 3: Document server bootstrap**

Include:

```bash
cd /opt/jyotisha-staging
umask 077
touch .env.staging.database
chmod 600 .env.staging.database
```

Document exact keys:

```text
POSTGRES_DB=jyotisha
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<generated>
SCHEMA_OWNER_PASSWORD=<generated>
IDENTITY_RUNTIME_PASSWORD=<generated>
APP_RUNTIME_PASSWORD=<generated>
ADMIN_RUNTIME_PASSWORD=<generated>
MIGRATION_RUNNER_PASSWORD=<generated>
BACKUP_READER_PASSWORD=<generated>
STAGING_BACKUP_ENCRYPTION_KEY=<generated>
SCHEMA_DATABASE_URL=postgresql://schema_owner:<percent-encoded-password>@postgres:5432/jyotisha
```

Each secret uses independently generated 32 random bytes. URL password is percent-encoded. State explicitly: no schema URL in `.env.staging`.

Document order:

1. Merge to `staging`.
2. Wait for backend quality gate and its exact-SHA image digest manifest.
3. If automatic deploy reports pending migrations, manually run `Migrate Staging Database` with the reported full SHA.
4. The successful migration workflow re-dispatches exact-SHA staging deploy automatically.
5. Check `https://staging.jyotisha.chat/api/health`.
6. Run:

```bash
./deploy/backup-staging-postgres.sh \
  .env.staging.database \
  /opt/jyotisha-staging/backups/staging-db
```

Also document a restore drill into a disposable `jyotisha_restore_check` database and deletion of only that database and temporary decrypted dump.

- [ ] **Step 4: Verify and commit**

```bash
cd frontend && npm run test:deployment
cd ..
git add deploy/README.md frontend/tests/staging-backend-workflows.test.ts
git commit -m "docs: add staging postgres operations runbook"
```

---

### Task 8: Milestone verification

**Files:** Verify Tasks 1–7 only; add no feature code.

- [ ] **Step 1: Full local gate**

```bash
cd frontend
npm ci
npm run test:db
npm run test:deployment
npm test
npm run lint
NEXT_PUBLIC_SUPABASE_URL=https://placeholder.supabase.co \
NEXT_PUBLIC_SUPABASE_ANON_KEY=placeholder npm run build
cd ..
python -m pip install -r requirements.txt -r requirements-dev.txt
ruff check scripts/run_quality_gate.py tests/test_varga_bphs.py \
  tests/test_ashtakavarga_invariants.py tests/test_cli_smoke.py \
  tests/test_yoga_rules_integrity.py
python -m py_compile scripts/*.py jyotish_vedic/*.py mcp_server.py
python scripts/run_quality_gate.py \
  --profile quick --skip-yoga-logic --skip-frontend-runtime
python -m build --no-isolation
```

Expected: all PASS.

- [ ] **Step 2: Boundary and secret scans**

```bash
rg -n 'db:migrate([^:]|$)|migrator|profile migration' \
  .github/workflows/deploy-staging.yml
rg -n 'up -d.*--build|docker compose build' \
  .github/workflows/deploy-staging.yml
rg -n 'db:migrate|--profile migration' \
  .github/workflows/migrate-staging-database.yml
rg -n 'sb_secret_|sb_publishable_|postgresql://[^:<[:space:]]+:[^<[:space:]]+@' \
  .github deploy frontend/db frontend/scripts frontend/src/lib/db frontend/tests
```

Expected: first two commands have no applying-migration/build matches (the read-only `db:migrate:check` is allowed); third matches manual migration; fourth finds no real credential (inspect and allow only explicit test fixtures or documentation placeholders).

- [ ] **Step 3: Inspect final state**

```bash
git status --short
git diff --check
git log --oneline --decorate -8
git diff --stat "$(git merge-base HEAD main)"..HEAD
```

Expected: clean worktree, no whitespace errors, seven focused commits, Milestone 1 files only.

- [ ] **Step 4: Open implementation PR**

Target updated `main`. Record prerequisite commit, exact test evidence, Supabase-still-source-of-truth status, normal-deploy/no-migration guarantee, server-only database env guarantee, production unchanged, and rollback rule (prior SHA image; database forward-fix unless a reviewed reverse migration exists). Do not merge until the PR’s new backend quality gate succeeds.
