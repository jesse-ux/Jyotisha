import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { GET as healthGet } from "../src/app/api/health/route.ts";

function serviceBlock(compose: string, service: string) {
  const match = compose.match(new RegExp(`^  ${service}:\\n([\\s\\S]*?)(?=^  [a-z][a-z0-9_-]*:|^volumes:)`, "m"));
  assert.ok(match, `expected ${service} service in compose file`);
  return match[1];
}

function webHealthcheckBlock(web: string) {
  const match = web.match(/^    healthcheck:\n((?:      .*\n?)*)/m);
  assert.ok(match, "expected a web healthcheck in compose file");
  return match[1];
}

function workflowStepBlock(workflow: string, stepName: string) {
  const match = workflow.match(new RegExp(`^      - name: ${stepName}\\n([\\s\\S]*?)(?=^      - name:|(?![\\s\\S]))`, "m"));
  assert.ok(match, `expected ${stepName} workflow step`);
  return match[1];
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

const testedShaExpression = "${{ github.event.workflow_run.head_sha || github.sha }}";

function assertWorkflowUsesTestedSha(workflow: string) {
  const checkout = workflowStepBlock(workflow, "Checkout tested revision");
  const sync = workflowStepBlock(workflow, "Sync and rebuild");
  const verification = workflowStepBlock(workflow, "Verify production");
  const shaExpression = escapeRegExp(testedShaExpression);

  assert.match(checkout, new RegExp(`ref: ${shaExpression}`), "Checkout tested revision must check out the tested SHA");
  assert.match(sync, new RegExp(`DEPLOY_GIT_SHA: ${shaExpression}`), "Sync and rebuild must use the tested SHA");
  assert.match(sync, /GITHUB_SHA='\$DEPLOY_GIT_SHA'/, "Sync and rebuild must inject its SHA into the web runtime");
  assert.match(verification, new RegExp(`DEPLOY_GIT_SHA: ${shaExpression}`), "Verify production must use the tested SHA");
  assert.match(verification, /curl --fail --silent --show-error --retry 12 --retry-delay 5 https:\/\/jyotisha\.chat\/api\/health/);
  assert.match(verification, /body\.deployment\?\.gitCommit !== process\.env\.DEPLOY_GIT_SHA/);
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
  const healthcheck = webHealthcheckBlock(web);

  assert.match(web, /GITHUB_SHA: \$\{GITHUB_SHA\}/);
  assert.match(web, /healthcheck:\n\s+test: \["CMD", "node", "-e", "fetch\('http:\/\/127\.0\.0\.1:3000\/api\/health'\)\.then\(r=>\{if\(!r\.ok\)process\.exit\(1\)\}\)"\]/);
  assert.match(healthcheck, /^      interval: 30s$/m);
  assert.match(healthcheck, /^      timeout: 5s$/m);
  assert.match(healthcheck, /^      retries: 5$/m);
  assert.match(healthcheck, /^      start_period: 30s$/m);
  assert.match(healthcheck, /^      start_interval: 1s$/m);
  assert.match(caddy, /web:\n\s+condition: service_healthy/);
  assert.match(caddyfile, /reverse_proxy web:3000 \{\n\s+lb_try_duration 10s\n\s+lb_try_interval 250ms\n\s+\}/);
});

test("production workflow consistently uses its tested revision from checkout through verification", () => {
  const workflow = readFileSync(new URL("../../.github/workflows/deploy-production.yml", import.meta.url), "utf8");

  assertWorkflowUsesTestedSha(workflow);
});

test("production workflow rejects a SHA mismatch in verification", () => {
  const workflow = readFileSync(new URL("../../.github/workflows/deploy-production.yml", import.meta.url), "utf8");
  const verification = workflowStepBlock(workflow, "Verify production");
  const mismatchedVerification = verification.replace(testedShaExpression, "${{ github.sha }}");

  assert.throws(
    () => assertWorkflowUsesTestedSha(workflow.replace(verification, mismatchedVerification)),
    /Verify production must use the tested SHA/,
  );
});

test("v3 readiness requires healthy dependencies and smoke proof for the exact full deployment SHA", async () => {
  const keys = [
    "GITHUB_SHA", "NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY", "OPENAI_API_KEY",
    "RECTIFICATION_V3_CREATE_ENABLED", "RECTIFICATION_V3_MIGRATIONS_READY",
    "RECTIFICATION_V3_SYNTHETIC_SMOKE_SHA",
  ] as const;
  const prior = Object.fromEntries(keys.map((key) => [key, process.env[key]]));
  const originalFetch = globalThis.fetch;
  const currentSha = "0123456789abcdef0123456789abcdef01234567";
  const oldSha = "89abcdef0123456789abcdef0123456789abcdef";
  Object.assign(process.env, {
    GITHUB_SHA: currentSha,
    NEXT_PUBLIC_SUPABASE_URL: "https://example.invalid",
    NEXT_PUBLIC_SUPABASE_ANON_KEY: "synthetic-public-key",
    SUPABASE_SERVICE_ROLE_KEY: "synthetic-service-key",
    OPENAI_API_KEY: "synthetic-model-key",
    RECTIFICATION_V3_CREATE_ENABLED: "true",
    RECTIFICATION_V3_MIGRATIONS_READY: "true",
  });
  globalThis.fetch = async () => Response.json({ status: "ok" });

  async function readiness() {
    const response = await healthGet();
    const body = await response.json() as {
      status: string;
      rollout: { conversationalRectificationV3: {
        syntheticSmoke: string;
        readyForNewCases: boolean;
      } };
    };
    return body;
  }

  try {
    delete process.env.RECTIFICATION_V3_SYNTHETIC_SMOKE_SHA;
    assert.deepEqual((await readiness()).rollout.conversationalRectificationV3, {
      protocol: "conversational-evidence-v3",
      newCaseCreation: "enabled",
      migrations: "ready",
      syntheticSmoke: "pending",
      readyForNewCases: false,
    });

    process.env.GITHUB_SHA = "deadbee";
    process.env.RECTIFICATION_V3_SYNTHETIC_SMOKE_SHA = "deadbee";
    assert.equal((await readiness()).rollout.conversationalRectificationV3.readyForNewCases, false);

    process.env.GITHUB_SHA = currentSha;
    process.env.RECTIFICATION_V3_SYNTHETIC_SMOKE_SHA = oldSha;
    assert.equal((await readiness()).rollout.conversationalRectificationV3.syntheticSmoke, "pending");

    process.env.RECTIFICATION_V3_SYNTHETIC_SMOKE_SHA = currentSha;
    const ready = await readiness();
    assert.equal(ready.status, "ok");
    assert.deepEqual(ready.rollout.conversationalRectificationV3, {
      protocol: "conversational-evidence-v3",
      newCaseCreation: "enabled",
      migrations: "ready",
      syntheticSmoke: "matched",
      readyForNewCases: true,
    });

    delete process.env.SUPABASE_SERVICE_ROLE_KEY;
    const blocked = await readiness();
    assert.equal(blocked.status, "blocked");
    assert.equal(blocked.rollout.conversationalRectificationV3.syntheticSmoke, "matched");
    assert.equal(blocked.rollout.conversationalRectificationV3.readyForNewCases, false);
  } finally {
    globalThis.fetch = originalFetch;
    for (const key of keys) {
      const value = prior[key];
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
  }
});
