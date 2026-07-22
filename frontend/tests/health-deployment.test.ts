import assert from "node:assert/strict";
import {
  chmodSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";
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

const testedShaExpression = "${{ github.sha }}";

function assertWorkflowUsesTestedSha(workflow: string) {
  const checkout = workflowStepBlock(workflow, "Checkout tested revision");
  const sync = workflowStepBlock(workflow, "Sync and rebuild");
  const verification = workflowStepBlock(workflow, "Verify production");
  const shaExpression = escapeRegExp(testedShaExpression);

  assert.match(checkout, new RegExp(`ref: ${shaExpression}`), "Checkout tested revision must check out the tested SHA");
  assert.match(sync, new RegExp(`DEPLOY_GIT_SHA: ${shaExpression}`), "Sync and rebuild must use the tested SHA");
  assert.match(sync, /GITHUB_SHA='\$DEPLOY_GIT_SHA'/, "Sync and rebuild must inject its SHA into the web runtime");
  assert.match(verification, new RegExp(`DEPLOY_GIT_SHA: ${shaExpression}`), "Verify production must use the tested SHA");
  assert.match(verification, /curl --fail --silent --show-error https:\/\/jyotisha\.chat\/api\/health/);
  assert.match(verification, /get\("deployment", \{\}\)\.get\("gitCommit"/);
  assert.match(verification, /Production revision did not converge/);
}

test("health endpoint exposes deployment identity for production verification", () => {
  const source = [
    readFileSync(new URL("../src/app/api/health/route.ts", import.meta.url), "utf8"),
    readFileSync(new URL("../src/lib/conversational-rectification/creation-policy.ts", import.meta.url), "utf8"),
  ].join("\n");

  assert.match(source, /deployment:/);
  assert.match(source, /GITHUB_SHA/);
  assert.match(source, /VERCEL_GIT_COMMIT_SHA/);
  assert.match(source, /gitCommit/);
});

test("manual production deployment passes the selected revision into the web runtime", () => {
  const compose = readFileSync(
    new URL("../../deploy/docker-compose.server.yml", import.meta.url),
    "utf8",
  );
  const workflow = readFileSync(
    new URL("../../.github/workflows/deploy-production.yml", import.meta.url),
    "utf8",
  );

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
  const compose = readFileSync(
    new URL("../../deploy/docker-compose.server.yml", import.meta.url),
    "utf8",
  );

  assert.match(
    compose,
    /env_file:\s*\n\s*- \$\{APP_ENV_FILE:-\.\.\/\.env\.production\}/,
  );
  assert.match(
    compose,
    /\$\{CADDYFILE_PATH:-\.\/Caddyfile\}:\/etc\/caddy\/Caddyfile:ro/,
  );
  assert.match(
    compose,
    /SITE_ADDRESS: \$\{SITE_ADDRESS:-https:\/\/jyotisha\.chat\}/,
  );
  assert.match(
    compose,
    /ADMIN_SITE_ADDRESS: \$\{ADMIN_SITE_ADDRESS:-https:\/\/admin\.staging\.jyotisha\.chat\}/,
  );
});

test("server compose defaults to local images without removing either build", () => {
  const composeFile = fileURLToPath(
    new URL("../../deploy/docker-compose.server.yml", import.meta.url),
  );
  const compose = readFileSync(composeFile, "utf8");

  assert.match(compose, /^\s+image: \$\{API_IMAGE:-jyotisha-api:local\}$/m);
  assert.match(compose, /^\s+image: \$\{WEB_IMAGE:-jyotisha-web:local\}$/m);

  const root = mkdtempSync(join(tmpdir(), "jyotisha-server-compose-"));
  const appEnvFile = join(root, ".env.production");
  writeFileSync(appEnvFile, "RUNTIME_FIXTURE=1\n");
  chmodSync(appEnvFile, 0o600);

  const env: NodeJS.ProcessEnv = {
    ...process.env,
    APP_ENV_FILE: appEnvFile,
    CADDYFILE_PATH: fileURLToPath(
      new URL("../../deploy/Caddyfile", import.meta.url),
    ),
    GITHUB_SHA: "0000000000000000000000000000000000000000",
    NEXT_PUBLIC_SUPABASE_URL: "https://placeholder.supabase.co",
    NEXT_PUBLIC_SUPABASE_ANON_KEY: "placeholder",
  };
  delete env.API_IMAGE;
  delete env.WEB_IMAGE;

  try {
    const result = spawnSync(
      "docker",
      ["compose", "-f", composeFile, "config", "--format", "json"],
      { encoding: "utf8", env },
    );
    assert.equal(result.status, 0, result.stderr);
    const rendered = JSON.parse(result.stdout) as {
      services: Record<string, { build?: unknown; image?: string }>;
    };
    assert.equal(rendered.services.api.image, "jyotisha-api:local");
    assert.equal(rendered.services.web.image, "jyotisha-web:local");
    assert.ok(rendered.services.api.build, "api build definition was removed");
    assert.ok(rendered.services.web.build, "web build definition was removed");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("staging Caddy isolates the business admin surface from the public host", () => {
  const caddy = readFileSync(
    new URL("../../deploy/Caddyfile.staging", import.meta.url),
    "utf8",
  );

  assert.match(caddy, /\{\$SITE_ADDRESS:https:\/\/staging\.jyotisha\.chat\}/);
  assert.match(
    caddy,
    /\{\$ADMIN_SITE_ADDRESS:https:\/\/admin\.staging\.jyotisha\.chat\}/,
  );
  assert.match(caddy, /reverse_proxy web:3000/);
  assert.match(caddy, /@adminPaths path \/admin \/admin\/\* \/api\/admin\/\*/);
  assert.match(caddy, /redir @adminRoot \/admin\/codes 302/);
  assert.match(caddy, /@adminSurface path \/login \/admin \/admin\/\* \/api\/admin\/\* \/api\/auth\/\*/);
  assert.match(caddy, /respond "Not found" 404/);
  assert.doesNotMatch(caddy, /www\.jyotisha\.chat/);
});

test("staging deploy consumes only the isolated staging environment and tested revision", () => {
  const qualityGate = readFileSync(
    new URL("../../.github/workflows/backend-quality-gate.yml", import.meta.url),
    "utf8",
  );
  const workflow = readFileSync(
    new URL("../../.github/workflows/deploy-staging.yml", import.meta.url),
    "utf8",
  );
  const syncController = readFileSync(
    new URL("../../deploy/sync-staging-tree.sh", import.meta.url),
    "utf8",
  );

  assert.match(qualityGate, /push:\s*\n\s*branches: \[staging\]/);
  assert.match(workflow, /workflows: \["Staging Backend Quality Gate"\]/);
  assert.match(
    workflow,
    /github\.event\.workflow_run\.head_branch == 'staging'/,
  );
  assert.match(workflow, /actions: read/);
  assert.match(workflow, /packages: read/);
  assert.match(workflow, /environment:\s*\n\s*name: staging/);
  assert.match(workflow, /deploy_sha:/);
  assert.match(workflow, /\^\[0-9a-f\]\{40\}\$/);
  assert.match(
    workflow,
    /actions\/workflows\/backend-quality-gate\.yml\/runs\?head_sha=/,
  );
  assert.match(workflow, /STAGING_SSH_PRIVATE_KEY/);
  assert.match(workflow, /vars\.STAGING_HOST/);
  assert.match(workflow, /vars\.STAGING_KNOWN_HOSTS/);
  assert.match(workflow, /test "\$DEPLOY_HOST" = "118\.26\.111\.127"/);
  assert.match(workflow, /test "\$DEPLOY_USER" = "deploy"/);
  assert.match(workflow, /test "\$DEPLOY_PATH" = "\/opt\/jyotisha-staging"/);
  assert.match(
    workflow,
    /--include='\/deploy\/' --include='\/deploy\/\*\*\*' --exclude='\*'/,
  );
  assert.match(workflow, /run-staging-deploy\.sh/);
  assert.match(workflow, /steps\.images\.outputs\.api_image/);
  assert.match(workflow, /steps\.images\.outputs\.web_image/);
  assert.doesNotMatch(workflow, /PRODUCTION_SSH_PRIVATE_KEY/);
  assert.doesNotMatch(workflow, /103\.117\.123\.53/);
  assert.match(syncController, /--exclude='\/\.env\*'/);
  assert.match(syncController, /--exclude='\/\.docker\/'/);
  assert.match(syncController, /--exclude='\/backups\/'/);
});

test("staging env validator rejects selector drift, duplicates, and unsafe permissions", () => {
  const validator = fileURLToPath(
    new URL("../../deploy/validate-staging-env.sh", import.meta.url),
  );
  const root = mkdtempSync(join(tmpdir(), "jyotisha-staging-env-"));
  const envFile = join(root, ".env.staging");
  const composeFile = join(root, "compose.yml");
  const validSelectors = [
    "APP_ENV_FILE=../.env.staging",
    "CADDYFILE_PATH=./Caddyfile.staging",
    "SITE_ADDRESS=https://staging.jyotisha.chat",
    "ADMIN_SITE_ADDRESS=https://admin.staging.jyotisha.chat",
    "AUTH_PROVIDER=self-hosted",
    "SELF_HOSTED_IDENTITY_ENABLED=true",
    "AUTH_USER_ORIGIN=https://staging.jyotisha.chat",
    "AUTH_ADMIN_ORIGIN=https://admin.staging.jyotisha.chat",
    "IDENTITY_DATABASE_URL=postgresql://identity_runtime:identity-runtime-test-password@postgres:5432/jyotisha",
    "APP_DATABASE_URL=postgresql://app_runtime:app-runtime-test-password@postgres:5432/jyotisha",
    "ADMIN_DATABASE_URL=postgresql://admin_runtime:admin-runtime-test-password@postgres:5432/jyotisha",
    "BETTER_AUTH_USER_SECRET=user-secret-that-is-at-least-32-bytes-long",
    "BETTER_AUTH_ADMIN_SECRET=admin-secret-that-is-at-least-32-bytes-long",
    "RESEND_API_KEY=re_test_key_that_must_not_be_printed",
    "RESEND_FROM_EMAIL=Jyotisha Staging <login@staging.jyotisha.chat>",
    "ADMIN_EMAILS=admin@example.com",
    "JYOTISH_DYNAMIC_RECTIFICATION_TOKEN=dynamic-token-that-is-at-least-32-bytes",
  ];
  const run = () =>
    spawnSync("bash", [validator, envFile], { encoding: "utf8" });
  const writeEnv = (lines: string[], mode = 0o600) => {
    writeFileSync(envFile, `${lines.join("\n")}\n`);
    chmodSync(envFile, mode);
  };

  try {
    writeFileSync(
      composeFile,
      [
        "services:",
        "  probe:",
        "    image: alpine",
        "    environment:",
        "      SELECTED: ${APP_ENV_FILE}",
        "",
      ].join("\n"),
    );
    writeEnv(validSelectors);
    assert.equal(run().status, 0);
    const shellOverride = spawnSync(
      "docker",
      [
        "compose",
        "--env-file",
        envFile,
        "-f",
        composeFile,
        "config",
        "--format",
        "json",
      ],
      {
        encoding: "utf8",
        env: { ...process.env, APP_ENV_FILE: "../.env.production" },
      },
    );
    assert.equal(shellOverride.status, 0, shellOverride.stderr);
    assert.equal(
      JSON.parse(shellOverride.stdout).services.probe.environment.SELECTED,
      "../.env.production",
    );

    writeEnv(["APP_ENV_FILE=../.env.production", ...validSelectors.slice(1)]);
    assert.notEqual(run().status, 0);

    writeEnv([...validSelectors, "SITE_ADDRESS=https://example.invalid"]);
    assert.notEqual(run().status, 0);

    writeEnv([...validSelectors, "APP_ENV_FILE = ../.env.production"]);
    assert.notEqual(run().status, 0);
    const rendered = spawnSync(
      "docker",
      [
        "compose",
        "--env-file",
        envFile,
        "-f",
        composeFile,
        "config",
        "--format",
        "json",
      ],
      { encoding: "utf8" },
    );
    assert.equal(rendered.status, 0, rendered.stderr);
    assert.equal(
      JSON.parse(rendered.stdout).services.probe.environment.SELECTED,
      "../.env.production",
    );

    writeEnv([...validSelectors, "export CADDYFILE_PATH=./Caddyfile"]);
    assert.notEqual(run().status, 0);

    writeEnv([...validSelectors, "SITE_ADDRESS"]);
    assert.notEqual(run().status, 0);

    writeEnv(
      validSelectors.map((line) =>
        line.startsWith("AUTH_PROVIDER=")
          ? "AUTH_PROVIDER=supabase"
          : line,
      ),
    );
    assert.notEqual(run().status, 0);

    writeEnv([
      ...validSelectors,
      "BETTER_AUTH_USER_SECRET=duplicate-secret-that-must-not-be-printed",
    ]);
    const duplicateSecret = run();
    assert.notEqual(duplicateSecret.status, 0);
    assert.doesNotMatch(
      `${duplicateSecret.stdout}${duplicateSecret.stderr}`,
      /duplicate-secret-that-must-not-be-printed|re_test_key_that_must_not_be_printed/,
    );

    writeEnv(validSelectors, 0o644);
    assert.notEqual(run().status, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
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
  const mismatchedVerification = verification.replace(
    testedShaExpression,
    "${{ github.event.workflow_run.head_sha || github.sha }}",
  );

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
    "RECTIFICATION_V3_SYNTHETIC_SMOKE_SHA", "RECTIFICATION_V3_SYNTHETIC_SMOKE_USER_IDS",
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
    RECTIFICATION_V3_SYNTHETIC_SMOKE_USER_IDS: "00000000-0000-4000-8000-000000009001",
  });
  globalThis.fetch = async () => Response.json({ status: "ok" });

  async function readiness() {
    const response = await healthGet();
    const body = await response.json() as {
      status: string;
      rollout: { conversationalRectificationV3: {
        syntheticSmoke: string;
        creationAudience: string;
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
      creationAudience: "smoke_only",
      migrations: "ready",
      syntheticSmoke: "pending",
      readyForNewCases: false,
    });

    process.env.GITHUB_SHA = "deadbee";
    process.env.RECTIFICATION_V3_SYNTHETIC_SMOKE_SHA = "deadbee";
    assert.deepEqual((await readiness()).rollout.conversationalRectificationV3, {
      protocol: "conversational-evidence-v3",
      newCaseCreation: "paused",
      creationAudience: "paused",
      migrations: "ready",
      syntheticSmoke: "pending",
      readyForNewCases: false,
    });

    process.env.GITHUB_SHA = currentSha;
    process.env.RECTIFICATION_V3_SYNTHETIC_SMOKE_SHA = oldSha;
    assert.equal((await readiness()).rollout.conversationalRectificationV3.creationAudience, "smoke_only");

    process.env.RECTIFICATION_V3_SYNTHETIC_SMOKE_SHA = currentSha;
    const ready = await readiness();
    assert.equal(ready.status, "ok");
    assert.deepEqual(ready.rollout.conversationalRectificationV3, {
      protocol: "conversational-evidence-v3",
      newCaseCreation: "enabled",
      creationAudience: "public",
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

test("production API probes health rapidly while a replacement container starts", () => {
  const compose = readFileSync(new URL("../../deploy/docker-compose.server.yml", import.meta.url), "utf8");

  assert.match(compose, /healthcheck:[\s\S]*start_period:\s*30s[\s\S]*start_interval:\s*1s/);
});
