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

## Automatic deployment

A successful `Jyotish Skill CI` run for a push to `main` triggers `.github/workflows/deploy-production.yml`. The workflow syncs the tested revision with `rsync`, preserves `/opt/jyotisha-app/.env.production`, rebuilds both Docker services, and verifies the public login route, logged-out account response, and private Python health endpoint.

Required GitHub Actions secret:

```text
PRODUCTION_SSH_PRIVATE_KEY = dedicated production deploy private key
```

The workflow pins the VPS Ed25519 host key and serializes deployments with the `production` concurrency group. It can also be run manually from GitHub Actions.

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
  --exclude='jyotish-app/node_modules/' \
  --exclude='jyotish-app/dist/' \
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
