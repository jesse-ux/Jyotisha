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

Pushes and pull requests do not start GitHub Actions automatically. Run the required validation workflows from the Actions page, then manually start `.github/workflows/deploy-production.yml` for the tested branch. The deployment workflow syncs that revision with `rsync`, preserves `/opt/jyotisha-app/.env.production`, rebuilds both Docker services, and verifies the public login route, logged-out account response, and private Python health endpoint.

Required GitHub Actions secret:

```text
PRODUCTION_SSH_PRIVATE_KEY = dedicated production deploy private key
```

The workflow pins the VPS Ed25519 host key and serializes deployments with the `production` concurrency group.

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
`RECTIFICATION_V3_CREATE_ENABLED=true`, and deploy the tested Git revision.

Before declaring rollout successful, fetch `https://jyotisha.chat/api/health`
and verify all of the following against the revision that passed validation:

- `deployment.gitCommit` exactly equals the tested 40-character Git SHA;
- `rollout.conversationalRectificationV3.protocol` is
  `conversational-evidence-v3`;
- `newCaseCreation` and `migrations` are `enabled` and `ready`;
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
`RECTIFICATION_V3_CREATE_ENABLED=false` and redeploy a revision that can still
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
