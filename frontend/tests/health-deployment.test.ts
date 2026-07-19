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

test("production deployment passes the tested revision into the web runtime", () => {
  const compose = readFileSync(new URL("../../deploy/docker-compose.server.yml", import.meta.url), "utf8");
  const workflow = readFileSync(new URL("../../.github/workflows/deploy-production.yml", import.meta.url), "utf8");

  assert.match(compose, /GITHUB_SHA: \$\{GITHUB_SHA\}/);
  assert.match(workflow, /DEPLOY_GIT_SHA: \$\{\{ github\.event\.workflow_run\.head_sha \|\| github\.sha \}\}/);
  assert.match(workflow, /GITHUB_SHA='\$DEPLOY_GIT_SHA'/);
  assert.match(workflow, /get\("deployment", \{\}\)\.get\("gitCommit"/);
  assert.match(workflow, /DEPLOY_GIT_SHA/);
  assert.match(workflow, /Production revision did not converge/);
});
