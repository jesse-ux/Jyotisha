import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

function serviceBlock(compose: string, service: string) {
  const match = compose.match(new RegExp(`^  ${service}:\\n([\\s\\S]*?)(?=^  [a-z][a-z0-9_-]*:|^volumes:)`, "m"));
  assert.ok(match, `expected ${service} service in compose file`);
  return match[1];
}

test("health endpoint exposes deployment identity for production verification", () => {
  const source = readFileSync(new URL("../src/app/api/health/route.ts", import.meta.url), "utf8");

  assert.match(source, /deployment:/);
  assert.match(source, /GITHUB_SHA/);
  assert.match(source, /VERCEL_GIT_COMMIT_SHA/);
  assert.match(source, /gitCommit/);
});

test("production traffic waits for a healthy web container and retries short replacement gaps", () => {
  const compose = readFileSync(new URL("../../deploy/docker-compose.server.yml", import.meta.url), "utf8");
  const caddyfile = readFileSync(new URL("../../deploy/Caddyfile", import.meta.url), "utf8");
  const web = serviceBlock(compose, "web");
  const caddy = serviceBlock(compose, "caddy");

  assert.match(web, /GITHUB_SHA: \$\{GITHUB_SHA\}/);
  assert.match(web, /healthcheck:\n\s+test: \["CMD", "node", "-e", "fetch\('http:\/\/127\.0\.0\.1:3000\/api\/health'\)\.then\(r=>\{if\(!r\.ok\)process\.exit\(1\)\}\)"\]/);
  assert.match(web, /start_period: 30s/);
  assert.match(web, /start_interval: 1s/);
  assert.match(caddy, /web:\n\s+condition: service_healthy/);
  assert.match(caddyfile, /reverse_proxy web:3000 \{\n\s+lb_try_duration 10s\n\s+lb_try_interval 250ms\n\s+\}/);
});

test("production verification accepts only the SHA exposed by the deployed health endpoint", () => {
  const workflow = readFileSync(new URL("../../.github/workflows/deploy-production.yml", import.meta.url), "utf8");

  assert.match(workflow, /DEPLOY_GIT_SHA: \$\{\{ github\.event\.workflow_run\.head_sha \|\| github\.sha \}\}/);
  assert.match(workflow, /GITHUB_SHA='\$DEPLOY_GIT_SHA'/);
  assert.match(workflow, /curl --fail --silent --show-error --retry 12 --retry-delay 5 https:\/\/jyotisha\.chat\/api\/health/);
  assert.match(workflow, /body\.deployment\?\.gitCommit !== process\.env\.DEPLOY_GIT_SHA/);
});
