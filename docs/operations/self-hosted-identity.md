# Self-hosted identity operations

This milestone deploys Better Auth beside the existing Supabase login. It does not authorize the final authentication cutover or removal of Supabase-backed business routes.

## Safe staging mode

Keep these two values exactly as shown while profile, consultation, credits, chat, and report routes still rely on Supabase JWT/RLS:

```dotenv
AUTH_PROVIDER=supabase
SELF_HOSTED_IDENTITY_ENABLED=true
```

This combination keeps `staging.jyotisha.chat/login` on Supabase, enables `/api/auth/**` for integration tests, and makes `admin.staging.jyotisha.chat/login` use the isolated Better Auth admin surface. The public and admin sessions have different secrets and host-only cookie prefixes. The staging validator deliberately rejects `AUTH_PROVIDER=self-hosted` in this milestone.

Use [the tracked staging identity example](../../deploy/.env.staging.identity.example) as a list of names only. Replace bracketed values directly on the server and keep `/opt/jyotisha-staging/.env.staging` owned by `deploy` with mode `0600`.

Generate separate secrets locally on the server:

```bash
openssl rand -base64 32
openssl rand -base64 32
```

Do not reuse either value as a PostgreSQL password. `IDENTITY_DATABASE_URL` uses the existing `IDENTITY_RUNTIME_PASSWORD` from `.env.staging.database`, percent-encoded only in the URL password component. It must point to the private Compose hostname `postgres:5432/jyotisha`; never publish PostgreSQL on a host port.

The Resend key must be staging-only. `RESEND_FROM_EMAIL` must use a sender/domain verified in Resend. CI never receives this key and uses an in-memory sender.

Validate without printing values:

```bash
cd /opt/jyotisha-staging
chmod 600 .env.staging
bash deploy/validate-staging-env.sh .env.staging
```

## Migration and smoke checks

Apply the reviewed PostgreSQL migrations through the existing `Migrate Staging Database` workflow before deploying the web image. The identity migration creates `identity.users`, `identity.sessions`, `identity.accounts`, `identity.verifications`, and `identity.otp_rate_limits` under least-privilege roles.

After deployment:

```bash
curl -fsS https://admin.staging.jyotisha.chat/login >/dev/null
curl -fsS https://admin.staging.jyotisha.chat/api/auth/get-session
test "$(curl -sS -o /dev/null -w '%{http_code}' https://admin.staging.jyotisha.chat/)" = 404
```

An unknown or unpromoted email cannot create an admin session. Promote an imported staging user only through a reviewed database/admin operation; the persisted `identity.users.role` value must include `admin` before the admin OTP flow can issue a cookie.

## Import rehearsal

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

To disable the new identity service without touching Supabase login, set `SELF_HOSTED_IDENTITY_ENABLED=false`, remove the identity-only smoke check for that separately reviewed rollback revision, and redeploy. Existing self-hosted sessions become unreachable; do not delete identity rows during application rollback.

Rotating either Better Auth secret invalidates only that surface's existing sessions. Rotate user and admin secrets separately, restart the web service, and verify the corresponding host. Rotate a leaked Resend key in Resend first, replace the server value, then restart. Never print the old or new values.

Final `AUTH_PROVIDER=self-hosted` cutover is blocked until all business modules authorize with the self-hosted session boundary, reconciliation passes, production backups and restore drills exist, and a separate reviewed cutover plan is approved.
