import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("health endpoint exposes deployment identity for production verification", () => {
  const source = readFileSync(new URL("../src/app/api/health/route.ts", import.meta.url), "utf8");

  assert.match(source, /deployment:/);
  assert.match(source, /GITHUB_SHA/);
  assert.match(source, /VERCEL_GIT_COMMIT_SHA/);
  assert.match(source, /gitCommit/);
});

test("manual production deployment passes the selected revision into the web runtime", () => {
  const compose = readFileSync(new URL("../../deploy/docker-compose.server.yml", import.meta.url), "utf8");
  const workflow = readFileSync(new URL("../../.github/workflows/deploy-production.yml", import.meta.url), "utf8");

  assert.match(compose, /GITHUB_SHA: \$\{GITHUB_SHA\}/);
  assert.match(workflow, /workflow_dispatch:/);
  assert.doesNotMatch(workflow, /workflow_run:/);
  assert.match(workflow, /DEPLOY_GIT_SHA: \$\{\{ github\.sha \}\}/);
  assert.match(workflow, /GITHUB_SHA='\$DEPLOY_GIT_SHA'/);
  assert.match(workflow, /get\("deployment", \{\}\)\.get\("gitCommit"/);
  assert.match(workflow, /DEPLOY_GIT_SHA/);
  assert.match(workflow, /Production revision did not converge/);
  assert.match(workflow, /git ls-remote origin refs\/heads\/main/);
  assert.match(workflow, /steps\.revision\.outputs\.deploy == 'true'/);
});

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
