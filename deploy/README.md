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

## Staging deployment

Staging is isolated from production:

| Item | Value |
| --- | --- |
| URL | `https://staging.jyotisha.chat` |
| Host | `118.26.111.127` |
| Path | `/opt/jyotisha-staging` |
| Runtime env | `/opt/jyotisha-staging/.env.staging` (`0600`) |
| Supabase | separate `Jyotisha Staging` project |
| GitHub Environment | `staging` |

The GitHub Environment contains `STAGING_SSH_PRIVATE_KEY` and the variables `STAGING_HOST`, `STAGING_PORT`, `STAGING_USER`, `STAGING_PATH`, `STAGING_URL`, and `STAGING_KNOWN_HOSTS`. Its deployment branch policy allows the `main` controller branch: GitHub's `workflow_run` event executes from the default branch while the workflow separately requires the successfully tested upstream branch to be `staging`. The staging key, database, Supabase keys, and model-provider keys must not be shared with production.

A push to branch `staging` runs `Jyotish Skill CI`. A successful push run triggers `.github/workflows/deploy-staging.yml`, which deploys the tested SHA and verifies the login route, logged-out account response, deployment SHA, and private Python health endpoint.

The staging env file must include these non-secret selectors so Compose cannot fall back to production paths:

```dotenv
APP_ENV_FILE=../.env.staging
CADDYFILE_PATH=./Caddyfile.staging
SITE_ADDRESS=https://staging.jyotisha.chat
```

After source sync and before `up`, the workflow validates `.env.staging` mode/selectors and runs `docker compose --env-file .env.staging -f deploy/docker-compose.server.yml config --quiet`. For later manual inspections, run the same checks only after the tracked deployment files exist on the server. The first deployment should be manual:

1. Confirm `/opt/jyotisha-staging/.env.staging` exists, has mode `0600`, and contains the three selectors above.
2. Open GitHub Actions -> Jyotish Skill CI -> Run workflow, using workflow from `main`.
3. Wait for success and copy that run's exact 40-character commit SHA.
4. Open GitHub Actions -> Deploy staging -> Run workflow, using workflow from `main`, and enter the SHA in `git_sha`.
5. Confirm `https://staging.jyotisha.chat/api/health` reports that SHA.
6. Only after the manual deployment passes, push a reviewed revision to branch `staging` to validate automatic deployment.

Application rollback uses the same workflow: manually dispatch `Deploy staging` from `main` with a previous known-good full SHA that has a successful CI run. Database migrations are separate and are not rolled back by an application deployment. Restore a staging database backup before running any destructive migration rehearsal.

Inspect staging without printing secrets:

```bash
ssh -i ~/.ssh/jyotisha-staging deploy@118.26.111.127
cd /opt/jyotisha-staging
docker compose --env-file .env.staging -f deploy/docker-compose.server.yml ps
docker compose --env-file .env.staging -f deploy/docker-compose.server.yml logs --tail=100 api web caddy
curl -fsS https://staging.jyotisha.chat/api/health
```

The normal application deployment workflow never runs database migrations. Apply migrations to the separate staging project first, verify them, and only then deploy application code that depends on them.

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
