# Jyotisha Staging Deployment Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing Compose deployment environment-selectable and automatically deploy tested `staging` revisions to `https://staging.jyotisha.chat` without changing production defaults.

**Architecture:** Production and staging share one Compose topology, with explicit variables selecting the runtime env file and Caddyfile. A dedicated GitHub workflow consumes only `staging` Environment credentials, syncs the tested revision, builds it on the staging VPS, and verifies public and private health contracts. Manual dispatch accepts a known Git SHA for rollback.

**Tech Stack:** GitHub Actions, Docker Compose, Caddy, rsync, SSH, Next.js node:test contract tests.

## Global Constraints

- Complete `2026-07-20-staging-infrastructure-bootstrap.md` before running the deployment workflow.
- Preserve production defaults: `.env.production`, `deploy/Caddyfile`, `https://jyotisha.chat`, and production workflow behavior.
- Staging runtime file remains `/opt/jyotisha-staging/.env.staging` and is never committed or synced.
- Staging workflow must use GitHub Environment `staging`, not repository production secrets.
- Staging host, port, user, path, URL, and known-hosts entry come from Environment variables.
- Staging deploys only after a successful `Jyotish Skill CI` push run on branch `staging`, or an explicit manual dispatch.
- Database migrations remain a separate operation and are never automatically run by the application deployment workflow.
- Do not expose host ports 3000 or 5200.
- Use TDD for repository changes and commit only task-owned files at each task boundary.

---

## File Structure

- Modify `deploy/docker-compose.server.yml`: environment-specific env file and Caddyfile selection while retaining production defaults.
- Create `deploy/Caddyfile.staging`: staging-only public reverse proxy with no production `www` redirect.
- Modify `frontend/tests/health-deployment.test.ts`: Compose, Caddy, CI-trigger, and staging-workflow contracts.
- Modify `.github/workflows/ci.yml`: run the existing CI on pushes to `staging`; do not add a `main` push trigger in this task.
- Create `.github/workflows/deploy-staging.yml`: tested-revision staging deployment and smoke checks.
- Modify `deploy/README.md`: operator-facing staging setup, first deploy, verification, and rollback.

### Task 1: Parameterize Compose Without Changing Production Defaults

**Files:**
- Modify: `frontend/tests/health-deployment.test.ts`
- Modify: `deploy/docker-compose.server.yml`
- Create: `deploy/Caddyfile.staging`

**Interfaces:**
- Consumes: `APP_ENV_FILE` and `CADDYFILE_PATH` from Compose interpolation.
- Produces: production defaults `../.env.production` and `./Caddyfile`; staging selections `../.env.staging` and `./Caddyfile.staging`.

- [ ] **Step 1: Add failing deployment configuration tests**

Append these tests to `frontend/tests/health-deployment.test.ts`:

```ts
test("server compose accepts staging paths while preserving production defaults", () => {
  const compose = readFileSync(new URL("../../deploy/docker-compose.server.yml", import.meta.url), "utf8");

  assert.match(compose, /env_file:\s*\n\s*- \$\{APP_ENV_FILE:-\.\.\/\.env\.production\}/);
  assert.match(compose, /\$\{CADDYFILE_PATH:-\.\/Caddyfile\}:\/etc\/caddy\/Caddyfile:ro/);
  assert.match(compose, /SITE_ADDRESS: \$\{SITE_ADDRESS:-https:\/\/jyotisha\.chat\}/);
});

test("staging Caddy configuration serves only the configured staging address", () => {
  const caddy = readFileSync(new URL("../../deploy/Caddyfile.staging", import.meta.url), "utf8");

  assert.match(caddy, /\{\$SITE_ADDRESS:https:\/\/staging\.jyotisha\.chat\}/);
  assert.match(caddy, /reverse_proxy web:3000/);
  assert.doesNotMatch(caddy, /www\.jyotisha\.chat/);
});
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```bash
cd /Users/jesse/Downloads/Copse/astrology/yinduzhanxing/frontend
npx tsx --test tests/health-deployment.test.ts
```

Expected: FAIL because `deploy/Caddyfile.staging` does not exist and Compose does not contain the environment-specific paths.

- [ ] **Step 3: Parameterize both service env files and the Caddy volume**

In `deploy/docker-compose.server.yml`, replace each current scalar env file:

```yaml
    env_file: ../.env.production
```

with this list form for both `api` and `web`:

```yaml
    env_file:
      - ${APP_ENV_FILE:-../.env.production}
```

Replace the Caddyfile volume:

```yaml
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
```

with:

```yaml
      - ${CADDYFILE_PATH:-./Caddyfile}:/etc/caddy/Caddyfile:ro
```

Do not change ports, health checks, `SITE_ADDRESS` default, volumes, or service dependencies.

- [ ] **Step 4: Create the staging-only Caddyfile**

Create `deploy/Caddyfile.staging` with exactly:

```caddyfile
{$SITE_ADDRESS:https://staging.jyotisha.chat} {
    encode zstd gzip
    reverse_proxy web:3000
}
```

This avoids the production Caddyfile's `www.jyotisha.chat` redirect and certificate request on the staging host.

- [ ] **Step 5: Re-run the focused tests**

Run:

```bash
cd /Users/jesse/Downloads/Copse/astrology/yinduzhanxing/frontend
npx tsx --test tests/health-deployment.test.ts
```

Expected: all tests in `health-deployment.test.ts` PASS.

- [ ] **Step 6: Validate production and staging Compose interpolation**

From the repository root, create one non-secret runtime env file and one Compose interpolation file:

```bash
cd /Users/jesse/Downloads/Copse/astrology/yinduzhanxing
RUNTIME_ENV_TMP=$(mktemp)
COMPOSE_ENV_TMP=$(mktemp)
printf '%s\n' \
  'NEXT_PUBLIC_SUPABASE_URL=https://ci-placeholder.supabase.co' \
  'NEXT_PUBLIC_SUPABASE_ANON_KEY=ci-placeholder' \
  > "$RUNTIME_ENV_TMP"
printf '%s\n' \
  "APP_ENV_FILE=$RUNTIME_ENV_TMP" \
  'CADDYFILE_PATH=./Caddyfile.staging' \
  'SITE_ADDRESS=https://staging.jyotisha.chat' \
  'NEXT_PUBLIC_SUPABASE_URL=https://ci-placeholder.supabase.co' \
  'NEXT_PUBLIC_SUPABASE_ANON_KEY=ci-placeholder' \
  > "$COMPOSE_ENV_TMP"
docker compose --env-file "$COMPOSE_ENV_TMP" -f deploy/docker-compose.server.yml config >/dev/null
rm "$RUNTIME_ENV_TMP" "$COMPOSE_ENV_TMP"
```

Expected: both `docker compose config` commands exit `0` without revealing a real secret.

- [ ] **Step 7: Commit Task 1**

```bash
git add frontend/tests/health-deployment.test.ts deploy/docker-compose.server.yml deploy/Caddyfile.staging
git commit -m "feat: parameterize staging compose configuration"
```

### Task 2: Add a Tested-Revision Staging Deployment Workflow

**Files:**
- Modify: `frontend/tests/health-deployment.test.ts`
- Modify: `.github/workflows/ci.yml`
- Create: `.github/workflows/deploy-staging.yml`

**Interfaces:**
- Consumes: successful `Jyotish Skill CI` runs for push events on branch `staging`; GitHub Environment variables and `STAGING_SSH_PRIVATE_KEY`.
- Produces: deployment of the exact tested SHA and verified staging health at `vars.STAGING_URL`.

- [ ] **Step 1: Add a failing staging workflow contract test**

Append this test to `frontend/tests/health-deployment.test.ts`:

```ts
test("staging deploy consumes only the isolated staging environment and tested revision", () => {
  const ci = readFileSync(new URL("../../.github/workflows/ci.yml", import.meta.url), "utf8");
  const workflow = readFileSync(new URL("../../.github/workflows/deploy-staging.yml", import.meta.url), "utf8");

  assert.match(ci, /push:\s*\n\s*branches: \[staging\]/);
  assert.match(workflow, /workflows: \["Jyotish Skill CI"\]/);
  assert.match(workflow, /github\.event\.workflow_run\.head_branch == 'staging'/);
  assert.match(workflow, /actions: read/);
  assert.match(workflow, /environment:\s*\n\s*name: staging/);
  assert.match(workflow, /git_sha:/);
  assert.doesNotMatch(workflow, /default: staging/);
  assert.match(workflow, /test "\$\{#REQUESTED_SHA\}" -eq 40/);
  assert.match(workflow, /actions\/workflows\/ci\.yml\/runs\?head_sha=/);
  assert.match(workflow, /STAGING_SSH_PRIVATE_KEY/);
  assert.match(workflow, /vars\.STAGING_HOST/);
  assert.match(workflow, /vars\.STAGING_KNOWN_HOSTS/);
  assert.match(workflow, /--exclude='\.env\*'/);
  assert.match(workflow, /docker compose --env-file \.env\.staging/);
  assert.match(workflow, /deployment\.gitCommit/);
  assert.doesNotMatch(workflow, /PRODUCTION_SSH_PRIVATE_KEY/);
  assert.doesNotMatch(workflow, /103\.117\.123\.53/);
});
```

- [ ] **Step 2: Run the test and verify it fails**

```bash
cd /Users/jesse/Downloads/Copse/astrology/yinduzhanxing/frontend
npx tsx --test tests/health-deployment.test.ts
```

Expected: FAIL because `.github/workflows/deploy-staging.yml` does not exist and CI has no staging push trigger.

- [ ] **Step 3: Add the staging push trigger to the existing CI**

Change only the `on` block in `.github/workflows/ci.yml` to:

```yaml
on:
  push:
    branches: [staging]
  workflow_dispatch:
```

Do not add `main` in this task. This prevents an unintended change to the current production deployment trigger while enabling a tested staging revision.

- [ ] **Step 4: Create the staging deployment workflow**

Create `.github/workflows/deploy-staging.yml` with exactly:

```yaml
name: Deploy staging

on:
  workflow_run:
    workflows: ["Jyotish Skill CI"]
    types: [completed]
  workflow_dispatch:
    inputs:
      git_sha:
        description: Exact 40-character commit SHA from a successful CI run
        required: true

permissions:
  contents: read
  actions: read

concurrency:
  group: staging
  cancel-in-progress: false

jobs:
  deploy:
    if: >-
      github.event_name == 'workflow_dispatch' ||
      (github.event.workflow_run.conclusion == 'success' &&
       github.event.workflow_run.event == 'push' &&
       github.event.workflow_run.head_branch == 'staging')
    runs-on: ubuntu-latest
    timeout-minutes: 30
    environment:
      name: staging
      url: ${{ vars.STAGING_URL }}
    env:
      DEPLOY_HOST: ${{ vars.STAGING_HOST }}
      DEPLOY_PORT: ${{ vars.STAGING_PORT }}
      DEPLOY_USER: ${{ vars.STAGING_USER }}
      DEPLOY_PATH: ${{ vars.STAGING_PATH }}
      STAGING_URL: ${{ vars.STAGING_URL }}
      STAGING_KNOWN_HOSTS: ${{ vars.STAGING_KNOWN_HOSTS }}

    steps:
      - name: Validate tested revision
        id: revision
        env:
          REQUESTED_SHA: ${{ github.event.workflow_run.head_sha || inputs.git_sha }}
          GH_TOKEN: ${{ github.token }}
        run: |
          test "${#REQUESTED_SHA}" -eq 40
          case "$REQUESTED_SHA" in
            *[!0-9a-fA-F]*) echo "git_sha must be a full hexadecimal commit SHA" >&2; exit 1 ;;
          esac
          DEPLOY_GIT_SHA="$(printf '%s' "$REQUESTED_SHA" | tr '[:upper:]' '[:lower:]')"
          if [ "$GITHUB_EVENT_NAME" = "workflow_dispatch" ]; then
            TESTED_RUNS="$(curl --fail --silent --show-error \
              --header "Authorization: Bearer $GH_TOKEN" \
              --header "Accept: application/vnd.github+json" \
              --header "X-GitHub-Api-Version: 2022-11-28" \
              "$GITHUB_API_URL/repos/$GITHUB_REPOSITORY/actions/workflows/ci.yml/runs?head_sha=$DEPLOY_GIT_SHA&status=success&per_page=1")"
            test "$(printf '%s' "$TESTED_RUNS" | jq -r '.total_count')" -ge 1 || {
              echo "No successful Jyotish Skill CI run found for $DEPLOY_GIT_SHA" >&2
              exit 1
            }
          fi
          echo "sha=$DEPLOY_GIT_SHA" >> "$GITHUB_OUTPUT"

      - name: Checkout tested revision
        uses: actions/checkout@v4
        with:
          ref: ${{ steps.revision.outputs.sha }}

      - name: Verify checked-out revision
        env:
          DEPLOY_GIT_SHA: ${{ steps.revision.outputs.sha }}
        run: test "$(git rev-parse HEAD)" = "$DEPLOY_GIT_SHA"

      - name: Validate staging target configuration
        run: |
          test "$DEPLOY_HOST" = "118.26.111.127"
          test "$DEPLOY_PORT" = "22"
          test "$DEPLOY_USER" = "deploy"
          test "$DEPLOY_PATH" = "/opt/jyotisha-staging"
          test "$STAGING_URL" = "https://staging.jyotisha.chat"
          test -n "$STAGING_KNOWN_HOSTS"

      - name: Configure pinned staging SSH
        env:
          SSH_PRIVATE_KEY: ${{ secrets.STAGING_SSH_PRIVATE_KEY }}
        run: |
          test -n "$SSH_PRIVATE_KEY"
          install -m 700 -d ~/.ssh
          printf '%s\n' "$SSH_PRIVATE_KEY" > ~/.ssh/jyotisha-staging
          chmod 600 ~/.ssh/jyotisha-staging
          printf '%s\n' "$STAGING_KNOWN_HOSTS" > ~/.ssh/known_hosts
          chmod 600 ~/.ssh/known_hosts

      - name: Sync and rebuild staging
        env:
          DEPLOY_GIT_SHA: ${{ steps.revision.outputs.sha }}
        run: |
          SSH_OPTIONS="-i $HOME/.ssh/jyotisha-staging -p $DEPLOY_PORT -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=20"
          RSYNC_SSH="ssh $SSH_OPTIONS"
          ssh $SSH_OPTIONS "$DEPLOY_USER@$DEPLOY_HOST" "install -d -m 755 '$DEPLOY_PATH'"
          rsync -az --delete \
            --exclude='.git/' \
            --exclude='.env*' \
            --exclude='frontend/node_modules/' \
            --exclude='frontend/.next/' \
            -e "$RSYNC_SSH" \
            ./ "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/"
          ssh $SSH_OPTIONS "$DEPLOY_USER@$DEPLOY_HOST" \
            "cd '$DEPLOY_PATH' && test -f .env.staging && GITHUB_SHA='$DEPLOY_GIT_SHA' docker compose --env-file .env.staging -f deploy/docker-compose.server.yml up -d --build --remove-orphans"

      - name: Verify staging
        env:
          DEPLOY_GIT_SHA: ${{ steps.revision.outputs.sha }}
        run: |
          curl --fail --silent --show-error --retry 12 --retry-delay 5 "$STAGING_URL/login" >/dev/null
          test "$(curl --silent --output /dev/null --write-out '%{http_code}' "$STAGING_URL/api/account")" = "401"
          test "$(curl --fail --silent --show-error "$STAGING_URL/api/health" | jq -r '.deployment.gitCommit')" = "$DEPLOY_GIT_SHA"
          ssh -i ~/.ssh/jyotisha-staging -p "$DEPLOY_PORT" \
            -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
            "$DEPLOY_USER@$DEPLOY_HOST" \
            "cd '$DEPLOY_PATH' && docker compose --env-file .env.staging -f deploy/docker-compose.server.yml exec -T web node -e 'fetch(\"http://api:5200/api/health\").then(async r => { const body = await r.json(); if (!r.ok || body.status !== \"ok\" || body.swisseph_available !== true) process.exit(1); console.log(JSON.stringify(body)); })'"
```

- [ ] **Step 5: Re-run the focused test**

```bash
cd /Users/jesse/Downloads/Copse/astrology/yinduzhanxing/frontend
npx tsx --test tests/health-deployment.test.ts
```

Expected: all focused tests PASS.

- [ ] **Step 6: Review the workflow for secret and target isolation**

Run from repository root:

```bash
rg -n 'PRODUCTION_SSH_PRIVATE_KEY|103\.117\.123\.53' .github/workflows/deploy-staging.yml
rg -n 'STAGING_SSH_PRIVATE_KEY|vars\.STAGING_|\.env\.staging|head_branch == '\''staging'\''' .github/workflows/deploy-staging.yml
```

Expected: the first command returns no matches. The second command shows the staging secret, variables, env file, and branch guard. The workflow may safely mention `.env.production` only in an rsync exclusion so that a stray local file can never be copied.

- [ ] **Step 7: Commit Task 2**

```bash
git add frontend/tests/health-deployment.test.ts .github/workflows/ci.yml .github/workflows/deploy-staging.yml
git commit -m "ci: deploy tested revisions to staging"
```

### Task 3: Document First Deployment, Verification, and Rollback

**Files:**
- Modify: `deploy/README.md`

**Interfaces:**
- Consumes: infrastructure and workflow from earlier tasks.
- Produces: an operator runbook that does not require reading workflow internals.

- [ ] **Step 1: Add the staging section to the deployment README**

Append this section immediately before the existing `## Manual deployment fallback` heading in `deploy/README.md`:

````markdown
## Staging deployment

Staging is isolated from production:

| Item | Value |
| --- | --- |
| URL | `https://staging.jyotisha.chat` |
| Host | `118.26.111.127` |
| Path | `/opt/jyotisha-staging` |
| Runtime env | `/opt/jyotisha-staging/.env.staging` (`0600`) |
| Supabase | separate `jyotisha-staging` project |
| GitHub Environment | `staging` |

The GitHub Environment contains `STAGING_SSH_PRIVATE_KEY` and the variables `STAGING_HOST`, `STAGING_PORT`, `STAGING_USER`, `STAGING_PATH`, `STAGING_URL`, and `STAGING_KNOWN_HOSTS`. Its deployment policy allows the `main` controller branch; the workflow separately requires an upstream successful CI push from branch `staging`. The staging key, database, Supabase keys, and model-provider keys must not be shared with production.

A push to branch `staging` runs `Jyotish Skill CI`. A successful push run triggers `.github/workflows/deploy-staging.yml`, which deploys the tested SHA and verifies the login route, logged-out account response, deployment SHA, and private Python health endpoint.

The first deployment should be manual, after `.env.staging` is verified to contain `APP_ENV_FILE=../.env.staging`, `CADDYFILE_PATH=./Caddyfile.staging`, and `SITE_ADDRESS=https://staging.jyotisha.chat`:

1. Confirm `/opt/jyotisha-staging/.env.staging` exists and has mode `0600`.
2. Run `Jyotish Skill CI` manually using workflow from `main` and wait for success.
3. Open GitHub Actions -> Deploy staging -> Run workflow, using workflow from `main`.
4. Enter that successful CI run's exact 40-character commit SHA in `git_sha`.
5. Confirm `https://staging.jyotisha.chat/api/health` reports that SHA.
6. Only after the manual deployment passes, push a reviewed revision to branch `staging` to validate automatic deployment.

Application rollback uses the same workflow: manually dispatch `Deploy staging` with the previous known-good commit SHA. Database migrations are separate and are not rolled back by an application deployment. Restore a staging database backup before running any destructive migration rehearsal.

Inspect staging without printing secrets:

```bash
ssh -i ~/.ssh/jyotisha-staging deploy@118.26.111.127
cd /opt/jyotisha-staging
docker compose --env-file .env.staging -f deploy/docker-compose.server.yml ps
docker compose --env-file .env.staging -f deploy/docker-compose.server.yml logs --tail=100 api web caddy
curl -fsS https://staging.jyotisha.chat/api/health
```

The normal application deployment workflow never runs database migrations. Apply migrations to the separate staging project first, verify them, and only then deploy application code that depends on them.
````

- [ ] **Step 2: Check the README for production/staging ambiguity**

Run:

```bash
rg -n 'Staging deployment|118\.26\.111\.127|\.env\.staging|STAGING_SSH_PRIVATE_KEY|Database migrations' deploy/README.md
```

Expected: all five staging concepts appear in the new section, and the existing production section remains unchanged.

- [ ] **Step 3: Commit Task 3**

```bash
git add deploy/README.md
git commit -m "docs: add staging deployment runbook"
```

### Task 4: Repository Verification and Controlled First Deployment

**Files:**
- Verify only; no new repository files expected.

**Interfaces:**
- Consumes: all previous tasks and completed infrastructure plan.
- Produces: a tested repository revision, then a verified first staging deployment.

- [ ] **Step 1: Run whitespace and focused contract checks**

From repository root:

```bash
git diff --check HEAD~3..HEAD
cd frontend
npx tsx --test tests/health-deployment.test.ts
```

Expected: no whitespace errors and all deployment contract tests PASS.

- [ ] **Step 2: Run the complete frontend checks**

```bash
cd /Users/jesse/Downloads/Copse/astrology/yinduzhanxing/frontend
npm test
npm run lint
NEXT_PUBLIC_SUPABASE_URL=https://ci-placeholder.supabase.co \
NEXT_PUBLIC_SUPABASE_ANON_KEY=ci-placeholder \
npm run build
```

Expected: tests, lint, and production build all exit `0`.

- [ ] **Step 3: Re-run project pre-work checks with the repository virtualenv**

```bash
cd /Users/jesse/Downloads/Copse/astrology/yinduzhanxing
.venv/bin/python scripts/pre_work_check.py --remote-timeout 8 --command-timeout 45
```

Expected: record the exact result. Do not claim a green project gate if the existing fragment-governance failure remains; staging-specific focused tests must still be green.

- [ ] **Step 4: Push the implementation revision for review without altering production**

Use an isolated implementation branch and open a pull request. Do not push the dirty local `main` directly. After review and merge, record the merge SHA:

```bash
git rev-parse HEAD
```

Expected: one 40-character commit SHA used for the first manual staging deployment.

- [ ] **Step 5: Manually deploy the tested SHA**

In GitHub:

```text
Actions -> Deploy staging -> Run workflow
Use workflow from -> main
git_sha -> exact 40-character SHA from a successful Jyotish Skill CI run
```

Expected: `Configure pinned staging SSH`, `Sync and rebuild staging`, and `Verify staging` all pass. GitHub Environment shows the deployment URL.

- [ ] **Step 6: Verify the live deployment independently**

Run locally:

```bash
curl -fsS https://staging.jyotisha.chat/login >/dev/null
test "$(curl -sS -o /dev/null -w '%{http_code}' https://staging.jyotisha.chat/api/account)" = "401"
curl -fsS https://staging.jyotisha.chat/api/health | jq '{status, deployment, checks}'
ssh -i "$HOME/.ssh/jyotisha-staging" -o IdentitiesOnly=yes deploy@118.26.111.127 \
  'cd /opt/jyotisha-staging && docker compose --env-file .env.staging -f deploy/docker-compose.server.yml ps'
```

Expected: login succeeds, account returns 401, health is `ok` with the deployed SHA, and `api`, `web`, and `caddy` are running/healthy.

- [ ] **Step 7: Validate Auth, cookies, and database isolation manually**

Use a new disposable email address in a private browser window:

```text
1. Open https://staging.jyotisha.chat/login.
2. Complete OTP login using the staging Supabase email.
3. Complete onboarding and save one profile.
4. Create one chat session and send one low-cost test prompt.
5. Open browser developer tools -> Application -> Cookies.
6. Confirm staging session cookies are scoped to staging.jyotisha.chat and are not Domain=.jyotisha.chat cookies.
7. Open https://jyotisha.chat in a separate normal window and confirm its login state did not change.
```

In the staging Supabase Dashboard, confirm the disposable UUID appears in staging Auth and its profile/chat/credit rows exist only in the staging project. Search the production Auth dashboard for the disposable email and confirm it is absent. Do not copy production rows into staging.

Expected: staging OTP, profile, chat, and credit behavior work; no staging identity or row appears in production; production cookies and session remain unchanged.

- [ ] **Step 8: Rehearse a failed health check and recovery**

On the staging VPS, back up the staging env file and deliberately remove only the staging service-role value:

```bash
ssh -i "$HOME/.ssh/jyotisha-staging" -o IdentitiesOnly=yes deploy@118.26.111.127
cd /opt/jyotisha-staging
cp -p .env.staging /home/deploy/.env.staging.health-rehearsal
sed -i 's/^SUPABASE_SERVICE_ROLE_KEY=.*/SUPABASE_SERVICE_ROLE_KEY=/' .env.staging
```

Manually dispatch `Deploy staging` from `main` using the current full SHA that already has a successful `Jyotish Skill CI` run.

Expected: deployment reaches `Verify staging`, `/api/health` is not `ok`, and GitHub marks the workflow failed rather than successful.

Restore the untouched staging secret file and redeploy the same tested SHA:

```bash
mv /home/deploy/.env.staging.health-rehearsal .env.staging
chmod 600 .env.staging
exit
```

Expected: the second workflow passes and `/api/health` returns `ok`. If the backup file is missing, stop and recover the staging service-role value from the password manager; never use the production key.

- [ ] **Step 9: Validate automatic staging deployment**

After the manual deployment succeeds, update branch `staging` to the same reviewed SHA without force-pushing:

```bash
cd /Users/jesse/Downloads/Copse/astrology/yinduzhanxing
read -r -p 'Reviewed commit SHA: ' REVIEWED_SHA
git fetch origin
git push origin "$REVIEWED_SHA:refs/heads/staging"
unset REVIEWED_SHA
```

Expected sequence in GitHub Actions:

```text
Jyotish Skill CI: success, event push, branch staging
Deploy staging: automatically started
Deploy staging: success, same tested SHA
```

- [ ] **Step 10: Rehearse application rollback with a known-good SHA**

After a second harmless staging revision has deployed successfully, manually dispatch `Deploy staging` with the first known-good SHA.

Expected: workflow passes and `/api/health` reports the first SHA. Then redeploy the latest tested staging SHA. Do not combine this rehearsal with a database migration.
