# Self-hosted identity operations

Staging uses Better Auth and the private local PostgreSQL cluster for both identity and business data. Production remains on Supabase; this runbook does not authorize a production cutover.

## Staging mode

Keep these two values exactly as shown:

```dotenv
AUTH_PROVIDER=self-hosted
SELF_HOSTED_IDENTITY_ENABLED=true
```

This makes both login hosts use isolated Better Auth surfaces. Public and admin sessions have different secrets and host-only cookie prefixes. Server routes translate the Better Auth session into PostgreSQL request claims and use the reviewed existing RLS/RPC business contract. The browser uses only same-origin APIs and does not need Supabase configuration.

Use [the tracked staging identity example](../../deploy/.env.staging.identity.example) as a list of names only. Replace bracketed values directly on the server and keep `/opt/jyotisha-staging/.env.staging` owned by `deploy` with mode `0600`.

Generate separate secrets locally on the server:

```bash
openssl rand -base64 32
openssl rand -base64 32
```

Do not reuse either value as a PostgreSQL password. `IDENTITY_DATABASE_URL`, `APP_DATABASE_URL`, and `ADMIN_DATABASE_URL` use their matching passwords from `.env.staging.database`, percent-encoded only in each URL password component. All three must point to the private Compose hostname `postgres:5432/jyotisha`; never publish PostgreSQL on a host port.

The Resend key must be staging-only. `RESEND_FROM_EMAIL` must use a sender/domain verified in Resend. CI never receives this key and uses an in-memory sender.

Set `ADMIN_EMAILS` to the staging administrator allowlist. Generate an independent `JYOTISH_DYNAMIC_RECTIFICATION_TOKEN` and place the same value in the shared application env consumed by the web and private API containers; do not reuse a database or Better Auth secret.

Validate without printing values:

```bash
cd /opt/jyotisha-staging
chmod 600 .env.staging
bash deploy/validate-staging-env.sh .env.staging
```

## Migration and smoke checks

Apply the reviewed PostgreSQL migrations through the existing `Migrate Staging Database` workflow before deploying the web image. The workflow first ensures the compatibility roles exist, then applies the identity schema, the local `auth` compatibility layer, and all reviewed business migrations under the migration ledger. Better Auth users are transactionally projected into `auth.users`, which creates their business profile through the existing trigger.

After deployment:

```bash
curl -fsS https://admin.staging.jyotisha.chat/login >/dev/null
curl -fsS https://admin.staging.jyotisha.chat/api/auth/get-session
test "$(curl -sS -o /dev/null -w '%{http_code}' https://staging.jyotisha.chat/admin/codes)" = 404
```

The admin root redirects to `/admin/codes`; the public host rejects `/admin` and `/api/admin` paths. An unknown or unpromoted email cannot create an admin session. Promote an imported staging user only through a reviewed database/admin operation; the persisted `identity.users.role` value must include `admin` before the admin OTP flow can issue a cookie.

## Optional import rehearsal

Export Supabase Auth users to a JSON array in the supported fixture shape, then run a redacted dry-run first:

```bash
cd /opt/jyotisha-staging/frontend
node scripts/import-supabase-auth-users.mjs /secure/path/auth-users.json
```

The summary contains only counts. It preserves UUID, normalized email, verification timestamps, display metadata, and created/updated timestamps. It intentionally ignores passwords, sessions, JWTs, provider secrets, and Supabase platform fields.

Apply only after reviewing the dry-run and taking a local encrypted staging backup:

```bash
set -a
. ../.env.staging
set +a
node scripts/import-supabase-auth-users.mjs /secure/path/auth-users.json --apply
unset IDENTITY_DATABASE_URL
```

Reruns are idempotent by UUID and the whole import is transactional. Duplicate canonical emails abort before database writes.

## Rollback and rotation

An application rollback must use a previously validated staging image and does not reverse database migrations. Existing self-hosted sessions and data remain in PostgreSQL; do not delete identity or business rows during application rollback. Returning staging to Supabase would require a separate reviewed data-reconciliation and provider-switch change, not an environment-only toggle.

Rotating either Better Auth secret invalidates only that surface's existing sessions. Rotate user and admin secrets separately, restart the web service, and verify the corresponding host. Rotate a leaked Resend key in Resend first, replace the server value, then restart. Never print the old or new values.

Production `AUTH_PROVIDER=self-hosted` remains blocked until data reconciliation passes, production backups and restore drills exist, operational monitoring is ready, and a separate reviewed production cutover plan is approved.
