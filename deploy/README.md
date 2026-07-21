# Production deployment and maintenance

This file is the operational source of truth for the current Jyotisha demo deployment.

## Current production

| Item | Value |
| --- | --- |
| Public domain | `https://jyotisha.chat` |
| DNS | Spaceship nameservers (`launch1.spaceship.net`, `launch2.spaceship.net`) |
| Server | Hong Kong VPS, Ubuntu 22.04 x86_64 |
| Public host | `103.117.123.53` |
| SSH | port `22000`, public-key authentication only |
| Capacity | 1 vCPU / 2 GB RAM / 40 GB disk / 5 Mbps |
| App directory | `/opt/jyotisha-app` |
| Environment file | `/opt/jyotisha-app/.env.production` (`0600`) |
| Source repository | `https://github.com/jesse-ux/Jyotisha.git` |
| Supabase project | `vtvnfqmonbfuxmqkqdlc` |

This machine is suitable for a client demo and low concurrency. Supabase and the model provider stay managed externally; do not self-host them on this VPS.

## Architecture

```text
Spaceship DNS
  -> Caddy :80/:443
     -> web:3000 (Next.js + Mastra, Docker-private)
        -> api:5200 (Python Jyotish API, Docker-private)
           -> Swiss Ephemeris / local engine
           -> VedAstro gateway with local fallback
     -> Supabase Cloud
     -> external OpenAI-compatible model API
```

Only Caddy publishes host ports. Ports `3000` and `5200` must remain private.

## DNS and Supabase Auth

Spaceship resource records:

```text
A      @      103.117.123.53
CNAME  www    jyotisha.chat
```

Supabase Authentication URL Configuration:

```text
Site URL:      https://jyotisha.chat
Redirect URLs: https://jyotisha.chat/**
               https://www.jyotisha.chat/**
```

Before changing Caddy to the domain, verify the authoritative DNS result:

```bash
dig +short @launch1.spaceship.net A jyotisha.chat
```

It must return `103.117.123.53`. Caddy provisions and renews HTTPS automatically after DNS resolves.

## Production environment

`.env.production` combines the backend and frontend server variables. Required groups:

```dotenv
SITE_ADDRESS=https://jyotisha.chat
JYOTISH_API_BASE=http://api:5200

NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
ADMIN_EMAILS=...

# Conversational birth-time rectification rollout controls.
# Keep migrations false until the ordered database gate below has passed.
RECTIFICATION_PRICE_CREDITS=3
RECTIFICATION_V3_CREATE_ENABLED=true
RECTIFICATION_V3_MIGRATIONS_READY=false
# Set only after the authenticated synthetic smoke passes on this exact image.
RECTIFICATION_V3_SYNTHETIC_SMOKE_SHA=
# During canary only: one canonical synthetic account UUID. Never print or log it.
RECTIFICATION_V3_SYNTHETIC_SMOKE_USER_IDS=

# Recommended multi-model catalog. The JSON references server-only keys.
LLM_DEFAULT_MODEL_ID=deepseek-pro
LLM_MODELS_JSON='[{"id":"deepseek-pro","label":"DeepSeek V4 Pro","description":"更适合复杂分析","provider":"openai-compatible","baseURL":"https://api.deepseek.com","apiKeyEnv":"DEEPSEEK_API_KEY","model":"deepseek-v4-pro","creditCost":1},{"id":"gpt-5-mini","label":"ChatGPT 5 Mini","description":"响应稳定、速度均衡","provider":"openai","apiKeyEnv":"OPENAI_API_KEY","model":"openai/gpt-5-mini","creditCost":1}]'
DEEPSEEK_API_KEY=<server-secret>
OPENAI_API_KEY=<server-secret>

# Legacy single-model OpenAI configuration remains supported:
# OPENAI_API_KEY=<server-secret>
# MASTRA_MODEL=openai/gpt-5-mini

# Legacy single OpenAI-compatible provider remains supported:
# LLM_BASE_URL=https://provider.example/v1
# LLM_API_KEY=<server-secret>
# LLM_MODEL=provider-model-id

# Required VedAstro server-side upstream for chart creation and rectification:
VEDASTRO_GATEWAY_MODE=official_first
VEDASTRO_API_ENDPOINT=https://api.vedastro.org/api
VEDASTRO_ENABLE_NETWORK=1
VEDASTRO_TIMEOUT_SECONDS=20
VEDASTRO_API_KEY=<server-secret>
```

Never commit `.env.production`, `SUPABASE_SERVICE_ROLE_KEY`, model keys, user JWTs, SSH private keys or passwords. `NEXT_PUBLIC_SUPABASE_ANON_KEY` is intentionally public; authorization is enforced by Supabase RLS and server-side checks.

After changing VedAstro variables, restart the API and verify the configuration without printing credentials:
```bash
docker compose --env-file .env.production -f deploy/docker-compose.server.yml up -d --build api
docker compose --env-file .env.production -f deploy/docker-compose.server.yml exec api python3 scripts/diagnose_vedastro_mode.py
```
The report must show `mode: official_extended` and `network_enabled: true`. A missing raw response remains an upstream response boundary, not a successful external verification.

## Connect and inspect

```bash
ssh -p 22000 root@103.117.123.53
cd /opt/jyotisha-app
COMPOSE='docker compose --env-file .env.production -f deploy/docker-compose.server.yml'
$COMPOSE ps
$COMPOSE logs --tail=100 api web caddy
free -h
docker stats --no-stream
```

The server has a persistent 2 GB `/swapfile`. UFW permits only SSH `22000/tcp`, HTTP `80/tcp`, HTTPS `443/tcp`, and the pre-existing WireGuard `51820/udp` rule.

## Manual deployment with GitHub Actions

Production pushes and pull requests do not start GitHub Actions automatically. Run the required validation workflows from the Actions page, then manually start `.github/workflows/deploy-production.yml` for the tested branch. The deployment workflow syncs that revision with `rsync`, preserves `/opt/jyotisha-app/.env.production`, rebuilds both Docker services, and verifies the public login route, logged-out account response, and private Python health endpoint.

Required GitHub Actions secret:

```text
PRODUCTION_SSH_PRIVATE_KEY = dedicated production deploy private key
```

The workflow pins the VPS Ed25519 host key and serializes deployments with the `production` concurrency group.

## Staging deployment

Staging is isolated from production:

| Item | Value |
| --- | --- |
| URL | `https://staging.jyotisha.chat` |
| Host | `118.26.111.127` |
| Path | `/opt/jyotisha-staging` |
| Runtime app env | `/opt/jyotisha-staging/.env.staging` (`0600`) |
| Runtime database env | `/opt/jyotisha-staging/.env.staging.database` (`0600`) |
| PostgreSQL | private Compose network; no published host port |
| Supabase | separate `Jyotisha Staging` project |
| GitHub Environment | `staging` |

The GitHub `staging` Environment contains the secret `STAGING_SSH_PRIVATE_KEY` and the variables `STAGING_HOST`, `STAGING_PORT`, `STAGING_USER`, `STAGING_PATH`, `STAGING_URL`, and `STAGING_KNOWN_HOSTS`. Its deployment branch policy allows the `main` controller branch: GitHub's `workflow_run` event executes from the default branch while the workflow separately requires the successfully tested upstream branch to be `staging`. The controller checks out only `main` with full history, requires the requested staging SHA to be an ancestor of that reviewed history, and uploads only the allowlisted `deploy/` control files. It never executes deployment validators or remote orchestration scripts from the target/rollback revision. The staging key, database, Supabase keys, and model-provider keys must not be shared with production.

The repository-level public build inputs are configured at GitHub **Settings -> Secrets and variables -> Actions -> Variables** (the UI is also shown as **Settings → Secrets and variables → Actions → Variables**): `STAGING_SUPABASE_URL` and `STAGING_SUPABASE_ANON_KEY`. They are public build inputs, required for publish, and exposed to the browser; keep them staging-only and never print their values in workflow output, summaries, or support messages. The workflow passes them only as the `NEXT_PUBLIC_*` build arguments after non-empty/HTTPS validation.

`Staging Backend Quality Gate` runs for relevant `pull_request` paths, pushes to `staging`, and `workflow_dispatch`. It validates the Python/database/frontend contract; only a successful push to `staging` publishes the API/web images and a run-bound manifest containing their `sha256` digests. `.github/workflows/deploy-staging.yml` consumes that exact successful run, validates its manifest against the full 40-character commit, and deploys digest references rather than trusting the discoverability tags.

The staging env file must include these non-secret selectors so Compose cannot fall back to production paths:

```dotenv
APP_ENV_FILE=../.env.staging
CADDYFILE_PATH=./Caddyfile.staging
SITE_ADDRESS=https://staging.jyotisha.chat
```

After source sync and before `up`, the workflow validates `.env.staging` mode/selectors, explicitly pins the three staging selectors against ambient shell overrides, and runs `docker compose --env-file .env.staging -f deploy/docker-compose.server.yml config --quiet`. For later manual inspections, run the same checks only after the tracked deployment files exist on the server. Do not use a manual gate run from `main` as the first publishing path: publishing requires a successful push to `staging`, while manual `Deploy staging` requires a successful gate run for the exact SHA.

### First-deploy sequence

1. Complete the server and GitHub bootstrap: create both mode-`0600` env files, preload the reviewed `postgres:17-alpine` image, configure the staging Environment variables/secrets, and configure the repository staging build variables. Deployment and migration workflows use `--pull never` for PostgreSQL, so database image upgrades remain an explicit operator-controlled maintenance action rather than an application-deploy side effect.
2. Merge the reviewed change to `main`, then fast-forward/push that exact reviewed SHA to `staging`; do not create a staging-only target or rely on a `main` workflow dispatch to publish images.
3. The `Staging Backend Quality Gate` runs for that push and, when successful, publishes API/web images plus an artifact binding the exact SHA to both immutable image digests.
4. The automatic `Deploy staging` workflow downloads that gate-run artifact, syncs only the trusted `main` controller's allowlisted `deploy/` files under the shared staging host lock, and validates both `.env.staging` and `.env.staging.database` before any app change. The target application's code is carried only by the digest-pinned images.
5. If environment validation fails, fix the server-side env files without committing or copying secrets, then manually rerun `Deploy staging` from `main` with the same successful SHA in `deploy_sha`; the workflow rechecks a successful staging gate for that exact SHA.
6. If the read-only checker reports a pending migration, stop app deployment and run `Migrate Staging Database` manually with the same full SHA; a successful migration re-dispatches `Deploy staging` with that same SHA.
7. Confirm `https://staging.jyotisha.chat/api/health` reports the exact SHA and private API health.

Application rollback uses the same workflow: manually dispatch `Deploy staging` from the `main` controller with a previous known-good full SHA that has a successful `Staging Backend Quality Gate` run, and explicitly set `allow_rollback=true`. Normal and migration-triggered deployments reject stale, divergent, or backward revisions. Rollback still consumes the selected gate run's digest manifest and is supported only during that artifact's 30-day retention window; after expiry, stop and prepare a separately reviewed republish/recovery change rather than substituting a mutable tag or assuming the old run can still be rerun. Database migrations are separate and are not rolled back by an application deployment. Restore a staging database backup before running any destructive migration rehearsal.

Inspect staging without printing secrets:

```bash
ssh -i ~/.ssh/jyotisha-staging deploy@118.26.111.127
cd /opt/jyotisha-staging
docker compose --env-file .env.staging -f deploy/docker-compose.server.yml ps
docker compose --env-file .env.staging -f deploy/docker-compose.server.yml logs --tail=100 api web caddy
curl -fsS https://staging.jyotisha.chat/api/health
```

The normal application deployment workflow never runs database migrations. Apply migrations to the separate staging project first, verify them, and only then deploy application code that depends on them.

## Staging PostgreSQL operations

This section is the server-side runbook for the disposable staging PostgreSQL volume. It does not replace the production instructions above.

### Bootstrap and environment-file boundary

SSH to the staging host as the deployment user and create both environment files with a restrictive umask. The application file and the database file are separate, both are mode `0600`, the database file is owned by the deployment user, and neither is committed or copied through `rsync`:

```bash
cd /opt/jyotisha-staging
umask 077
touch .env.staging
chmod 600 .env.staging
touch .env.staging.database
chmod 600 .env.staging.database
```

`.env.staging` contains application selectors and server-only application credentials. `SCHEMA_DATABASE_URL` must not appear in `.env.staging`; neither may any database bootstrap password, `STAGING_BACKUP_ENCRYPTION_KEY`, or migration-runner credential. In particular, there is no `SCHEMA_DATABASE_URL` in `.env.staging`; the schema URL exists only in `.env.staging.database`, which is read by PostgreSQL and the opt-in migrator.

Generate every `<generated>` value from independently generated 32 random bytes (for example, run `openssl rand -base64 32` separately for each value and place it directly into the mode-`0600` file or an approved secret store). Do not reuse a password between roles, paste values into chat, commit either file, or print them in workflow logs. The schema-owner password in `SCHEMA_DATABASE_URL` is the same secret as `SCHEMA_OWNER_PASSWORD`; use a percent-encoded URL password component only, and do not encode the scheme, host, port, or database name.

The exact database keys are:

```dotenv
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

PostgreSQL is private: `deploy/docker-compose.postgres.yml` has no `ports` mapping, so the staging database is reachable only on the Docker `app` network. The CI overlay is the only host binding and is loopback-only (`127.0.0.1:${POSTGRES_HOST_PORT:-55432}:5432`); do not add a public database port, firewall exception, or browser-facing SQL tool. Normal web/API containers never receive `SCHEMA_DATABASE_URL`.

### Exact deployment and migration order

Use this order for every staging revision:

1. Merge the reviewed revision to `main`, then fast-forward/push that same exact SHA to `staging`.
2. Wait for `Staging Backend Quality Gate` to pass and publish that exact full SHA's API/web digest manifest.
3. The automatic `Deploy staging` workflow checks the exact SHA in read-only migration-check mode before changing API, web, or Caddy. If it reports pending or drifted migrations, stop; do not retry the application deployment as if it were a migration.
4. Open **Migrate Staging Database -> Run workflow**, select **Use workflow from: main**, and enter the reported full lowercase 40-character SHA in `deploy_sha`. The controller validates that exact SHA against a successful `staging` gate and reviewed `main` history, starts only PostgreSQL, and runs the digest-pinned migrator without executing scripts from the target revision.
5. A successful migration rechecks that `staging` still points at the same exact SHA, prints the ordered migration ledger, and dispatches the `main` controller for digest-pinned deployment with `allow_rollback=false`. If `staging` advanced during migration, it refuses the stale dispatch. Do not substitute a branch name, a short SHA, or a newer commit.
6. Confirm `https://staging.jyotisha.chat/api/health` and verify that its deployment SHA is the SHA from step 2.
7. After health verification, create the local encrypted backup described below.

The deploy and migration workflows share the `staging-mutation` Actions concurrency group, and their live-tree sync plus Compose work runs under `/opt/jyotisha-staging/.state/mutation.lock`. The synchronized tree explicitly preserves `/backups/`, `.env*`, `.state`, and `.incoming`. The read-only checker exits before app changes when a migration is pending. Its message includes the exact SHA and the `Migrate Staging Database` workflow name. A failed migration does not re-dispatch deployment. Application rollback restores the previously recorded digest references and SHA, falling back to validated local image IDs only when transitioning from the pre-foundation local-image deployment; it does not roll back database state.

### Local encrypted staging backups (three-copy limit)

After the health check, run the repository backup helper from the synchronized staging checkout:

```bash
cd /opt/jyotisha-staging
./deploy/backup-staging-postgres.sh \
  .env.staging.database \
  /opt/jyotisha-staging/backups/staging-db
```

The helper invokes `pg_dump --format=custom --no-owner` in the PostgreSQL container and encrypts the stream with `openssl enc -aes-256-cbc -salt -pbkdf2 -pass env:STAGING_BACKUP_ENCRYPTION_KEY`. It creates mode-`0600` `.dump.enc` files in a mode-`0700` directory, refuses disk usage at or above 70%, publishes atomically, and retains only the newest three encrypted local backups. The encryption passphrase is supplied through the environment, never as a command-line argument or printed value. Keep the archive directory on this staging VPS only; there is no off-site staging recovery and no off-site staging backup. These three local encrypted copies are rehearsal/rollback aids, not disaster-recovery backups.

### Restore drill into a disposable database

Run a restore drill only against the disposable `jyotisha_restore_check` database. Choose one archive and use a temporary decrypted custom-format dump; the commands below match the backup helper's AES-256-CBC/PBKDF2 and `pg_dump --format=custom` interfaces:

```bash
set -euo pipefail
cd /opt/jyotisha-staging
export DATABASE_ENV_FILE=../.env.staging.database
BACKUP_DIR=/opt/jyotisha-staging/backups/staging-db
BACKUP_FILE="$(find "$BACKUP_DIR" -maxdepth 1 -type f -name 'jyotisha-staging-*.dump.enc' -print | LC_ALL=C sort | tail -n 1)"
test -n "$BACKUP_FILE"
test -f "$BACKUP_FILE"
test ! -L "$BACKUP_FILE"
test -s "$BACKUP_FILE"
RESTORE_DUMP="$(mktemp /tmp/jyotisha-staging-restore.XXXXXX.dump)"
chmod 600 "$RESTORE_DUMP"
trap 'rm -f -- "$RESTORE_DUMP"' EXIT
read -r -s -p 'Backup passphrase: ' STAGING_BACKUP_ENCRYPTION_KEY
printf '\n' >&2
export STAGING_BACKUP_ENCRYPTION_KEY

openssl enc -d -aes-256-cbc -pbkdf2 \
  -pass env:STAGING_BACKUP_ENCRYPTION_KEY \
  -in "$BACKUP_FILE" -out "$RESTORE_DUMP"

docker compose -p jyotisha-staging -f deploy/docker-compose.postgres.yml \
  exec -T postgres createdb -U postgres jyotisha_restore_check
docker compose -p jyotisha-staging -f deploy/docker-compose.postgres.yml \
  exec -T postgres pg_restore -U postgres --no-owner --exit-on-error \
  --dbname=jyotisha_restore_check < "$RESTORE_DUMP"

# Inspect the restored disposable database, then remove only the drill target.
docker compose -p jyotisha-staging -f deploy/docker-compose.postgres.yml \
  exec -T postgres dropdb -U postgres --if-exists jyotisha_restore_check
rm -f -- "$RESTORE_DUMP"
unset STAGING_BACKUP_ENCRYPTION_KEY
```

The passphrase is read silently into an environment variable; do not put it in argv, shell history, logs, or support messages. The cleanup scope is deliberately narrow: delete only `jyotisha_restore_check` and the temporary decrypted dump. Do not run `docker compose down`, `down -v`, `dropdb jyotisha`, volume deletion, or archive deletion as part of this drill. If restore fails, preserve the encrypted archive and PostgreSQL volume for inspection, remove only the temporary dump, and investigate before retrying.

### Staging/production boundary

This disposable staging procedure does not authorize a production migration, production backup policy, production database replacement, domain switch, Supabase deletion, or production cutover. Production deployment and migration remain manual-only and require a separate reviewed approval, off-site encrypted backups, and a successful production restore drill. Keep the production `.env.production` and all production credentials on the production host; never copy them into staging.

## Manual deployment fallback

If GitHub Actions is unavailable, deploy the tracked tree without copying local secrets:

```bash
cd /Users/jesse/Downloads/Copse/astrology/yinduzhanxing
git status --short --branch
rsync -az --delete \
  --exclude='.git/' \
  --exclude='.env.production' \
  --exclude='frontend/node_modules/' \
  --exclude='frontend/.next/' \
  -e 'ssh -p 22000' \
  ./ root@103.117.123.53:/opt/jyotisha-app/
ssh -p 22000 root@103.117.123.53 \
  'cd /opt/jyotisha-app && docker compose --env-file .env.production -f deploy/docker-compose.server.yml up -d --build --remove-orphans'
```

The excluded `.env.production` remains only on the VPS.

## Verification

```bash
curl -fsS https://jyotisha.chat/login >/dev/null
curl -fsS -o /dev/null -w '%{http_code}\n' https://jyotisha.chat/api/account
```

The second command should return `401` while logged out. Verify the private Python API from inside the web container:

```bash
ssh -p 22000 root@103.117.123.53 \
  'cd /opt/jyotisha-app && docker compose --env-file .env.production -f deploy/docker-compose.server.yml exec -T web node -e "fetch(\"http://api:5200/api/health\").then(async r=>{console.log(r.status); console.log(await r.text())})"'
```

Expected: HTTP `200`, `"status": "ok"`, and `"swisseph_available": true`. Public access to `103.117.123.53:5200` must fail.

Before deploying application code that depends on any new Supabase migration (columns, tables, grants, policies, or RPCs), run `cd frontend && npx supabase db push --linked`; the GitHub deployment workflow does not apply database migrations. Multi-model chat specifically requires `20260717010000_chat_session_model.sql` before the new web image is deployed. Then manually verify: OTP login, onboarding/profile persistence, per-session `model_id` persistence, code redemption, admin code generation, authenticated `/api/models` returns only sanitized public metadata, invalid model IDs are rejected before charging, each configured model can answer, the 2.5-second free undo window, streaming response, one-credit charge, refund before the first output chunk, and charged stop with partial output preserved after streaming starts.

For the July 2026 new-user profile save fix, either run the manual GitHub Action
`Apply Supabase profile migrations` after adding `SUPABASE_DB_URL` or `DATABASE_URL`
to `/opt/jyotisha-app/.env.production`, or execute these five SQL migrations in
the Supabase SQL Editor with a project member account:

- `20260718010000_recover_missing_profile_rows.sql`
- `20260718020000_profiles_service_role_upsert_grants.sql`
- `20260718050000_profiles_service_role_upsert_grants.sql`
- `20260718070000_profiles_service_role_upsert_id.sql`
- `20260718080000_profiles_service_role_account_upsert_selects.sql`

Do not treat a green app deployment as proof this database step ran. If the SQL
Editor shows `You do not have access to this project`, use the correct Supabase
organization account or invite the current GitHub user to project
`vtvnfqmonbfuxmqkqdlc` before retrying.

## Conversational birth-time rectification v3 rollout

`conversational-evidence-v3` is an account-level workflow. A web-image rollout
does not prove its database contract is present. Apply migrations before the
web image, in this order:

1. `20260720000000_chat_delete_and_dynamic_candidate_confirmation.sql`
2. `20260720010000_conversational_rectification_schema.sql`
3. `20260720020000_conversational_rectification_billing.sql`
4. `20260720030000_conversational_rectification_transitions.sql`
5. `20260720040000_rectification_question_handoff.sql`
6. `20260721010000_conversational_legacy_import_projection.sql`

Run `cd frontend && npx supabase db push --linked` with the authorized project
account. Verify the linked migration ledger contains all six versions. Do not
print the database URL or any service-role credential. Then set
`RECTIFICATION_V3_MIGRATIONS_READY=true`, keep
`RECTIFICATION_V3_CREATE_ENABLED=true`, set
`RECTIFICATION_V3_SYNTHETIC_SMOKE_USER_IDS` to exactly one canonical UUID for
the synthetic account, leave `RECTIFICATION_V3_SYNTHETIC_SMOKE_SHA` empty, and
deploy the tested Git revision. Never print, log, copy into a ticket, or return
that UUID from health or telemetry. Creation is available only for the
allowlisted smoke account; ordinary authenticated users can still resume and
finish existing cases but cannot start a paid or legacy-imported case.

Before the smoke, fetch `https://jyotisha.chat/api/health` and verify the full
deployment SHA, healthy dependencies, enabled creation, ready migrations,
`creationAudience: smoke_only`, `syntheticSmoke: pending`, and
`readyForNewCases: false`. A missing, abbreviated, malformed, or
previous-revision smoke SHA must remain pending. If the create flag, migration
flag, deployment SHA, or strict UUID allowlist is invalid, creation audience
must be `paused`, including for the smoke account.

After the smoke sequence below passes, set
`RECTIFICATION_V3_SYNTHETIC_SMOKE_SHA` to the exact deployed 40-character
lowercase Git SHA, remove `RECTIFICATION_V3_SYNTHETIC_SMOKE_USER_IDS`, and
restart the web container. Then fetch health again and
verify all of the following against the revision that passed validation:

- `deployment.gitCommit` exactly equals the tested 40-character Git SHA;
- `rollout.conversationalRectificationV3.protocol` is
  `conversational-evidence-v3`;
- `newCaseCreation` and `migrations` are `enabled` and `ready`;
- `creationAudience` is `public`;
- `syntheticSmoke` is `matched`;
- `readyForNewCases` is `true`;
- ordinary health checks remain healthy. The health response must never contain
  environment values or credentials.

Using an authorized synthetic account with no real birth data, run this smoke
sequence. A plain HTTP `200` is not substitute evidence:

1. Finish onboarding without rectification. Verify an unverified reported time
   offers current-chat consent or `先校正再询问`.
2. Save a synthetic ordinary question and start v3. Verify one fixed fee and a
   rich first turn containing the candidate boundary, stable/sensitive layers,
   domain rationale, and a dated historical-event request.
3. Answer with one explicit event, choose `都不符合`, submit one ambiguous
   event, then a clear event. Verify the ambiguous/future facts do not score.
4. Pause, reload, and resume from a second authenticated browser session.
   Verify no second rectification charge.
5. Reach a candidate, verify the prior active time is still in force, reject a
   mismatched candidate confirmation, then explicitly confirm the exact
   candidate. Verify the time changes atomically.
6. Explicitly continue the saved ordinary question. Verify one normal
   consultation reservation. Delete its chat and verify the account case still
   resumes/loads.
7. For an unfinished legacy case, verify exactly one
   `migration_waived` import, unchanged history, and no broad-year questionnaire.
8. Inject one transient 502. Verify byte-identical retry and stable Chinese
   fallback, never raw browser English.

Record only protocol, phase, action kind, result category, latency bucket,
billing state, error category, and deployment SHA. Narrative, event text, birth
data, email, user/user-case identifiers, tokens, and model prompts are forbidden
from telemetry.

### Rollback

Rollback is forward-compatible and non-destructive. First set
`RECTIFICATION_V3_CREATE_ENABLED=false`, clear
`RECTIFICATION_V3_SYNTHETIC_SMOKE_SHA` and
`RECTIFICATION_V3_SYNTHETIC_SMOKE_USER_IDS`, and redeploy a revision that can still
read/resume v3. Health must report `newCaseCreation: paused`. This stops only
new v3 starts: keep reads, resume, answer, pause, confirmation, and saved-question
handoff available for existing cases. Never reverse or delete the v3 migrations,
rows, turns, evidence, receipts, or legacy import links. Never point an imported
case back to mutable legacy history. A revision in progress keeps the account's
prior active time until its exact atomic confirmation succeeds. If no compatible
reader is available, leave the current image serving existing cases and disable
only creation; do not deploy an older schema consumer.

## Common operations

```bash
# Restart without rebuilding
docker compose --env-file .env.production -f deploy/docker-compose.server.yml up -d

# Rebuild only the web container
docker compose --env-file .env.production -f deploy/docker-compose.server.yml up -d --build web caddy

# Rebuild only the Python API
docker compose --env-file .env.production -f deploy/docker-compose.server.yml up -d --build api

# Follow logs
docker compose --env-file .env.production -f deploy/docker-compose.server.yml logs -f --tail=100 api web caddy
```

## Optional Railway deployment

Railway is not the current production target. If needed, create `web` and `api` services from the same repository using `deploy/railway-web.Dockerfile` and `deploy/railway-api.Dockerfile`; keep `api` private and set the web service's `JYOTISH_API_BASE` to Railway's private API hostname.
