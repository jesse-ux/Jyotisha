# Railway deployment

Create services named `web` and `api` from this repository. Leave both **Root Directory** and **Start Command** empty; the Dockerfiles bind `0.0.0.0` and read `$PORT`.

| Service | Required variable | Healthcheck Path |
| --- | --- | --- |
| `web` | `RAILWAY_DOCKERFILE_PATH=/deploy/railway-web.Dockerfile` | `/login` |
| `api` | `RAILWAY_DOCKERFILE_PATH=/deploy/railway-api.Dockerfile` | `/api/health` |

## `api` variables

```dotenv
PORT=5200
```

`PORT` is set explicitly so the web service can reference the private API port. Railway healthchecks and the container command use the same value. No public API domain or legacy `jyotish-app/` service is needed.

## `web` variables

Required:

```dotenv
JYOTISH_API_BASE=http://${{api.RAILWAY_PRIVATE_DOMAIN}}:${{api.PORT}}
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
```

For AI responses, configure either:

```dotenv
OPENAI_API_KEY=...
MASTRA_MODEL=openai/gpt-5-mini
```

or an OpenAI-compatible provider:

```dotenv
LLM_BASE_URL=...
LLM_API_KEY=...
LLM_MODEL=...
# LLM_PROVIDER_ID=third-party
```

`ADMIN_EMAILS=admin@example.com,ops@example.com` is required to use `/admin/codes`. Generate a public domain only for `web`.


## After the first deploy

1. Add the generated `web` domain to Supabase Auth **Site URL** and **Redirect URLs**.
2. Open `/login`, sign in with an address listed in `ADMIN_EMAILS`, then verify `/admin/codes`.
3. Keep `api` private; verify its `/api/health` from Railway logs or the `web` service.

## Small VPS deployment

For a single low-traffic server, keep Supabase managed and run only the Web and API services:

```bash
docker compose --env-file .env.production -f deploy/docker-compose.server.yml up -d --build
```

Set `SITE_ADDRESS=http://SERVER_IP` for initial HTTP testing. Replace it with the production domain after DNS resolves; Caddy will then provision HTTPS automatically.
