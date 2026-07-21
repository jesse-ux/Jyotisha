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

test("health endpoint exposes deployment identity for production verification", () => {
  const source = readFileSync(
    new URL("../src/app/api/health/route.ts", import.meta.url),
    "utf8",
  );

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

  const env = {
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

test("staging Caddy isolates the public and identity-only admin hosts", () => {
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
  assert.match(caddy, /@identity path \/login \/api\/auth\/\*/);
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
    "AUTH_PROVIDER=supabase",
    "SELF_HOSTED_IDENTITY_ENABLED=true",
    "AUTH_USER_ORIGIN=https://staging.jyotisha.chat",
    "AUTH_ADMIN_ORIGIN=https://admin.staging.jyotisha.chat",
    "IDENTITY_DATABASE_URL=postgresql://identity_runtime:identity-runtime-test-password@postgres:5432/jyotisha",
    "BETTER_AUTH_USER_SECRET=user-secret-that-is-at-least-32-bytes-long",
    "BETTER_AUTH_ADMIN_SECRET=admin-secret-that-is-at-least-32-bytes-long",
    "RESEND_API_KEY=re_test_key_that_must_not_be_printed",
    "RESEND_FROM_EMAIL=Jyotisha Staging <login@staging.jyotisha.chat>",
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
          ? "AUTH_PROVIDER=self-hosted"
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
