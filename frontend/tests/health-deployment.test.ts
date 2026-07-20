import assert from "node:assert/strict";
import {
  chmodSync,
  existsSync,
  mkdirSync,
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
});

test("staging Caddy configuration serves only the configured staging address", () => {
  const caddy = readFileSync(
    new URL("../../deploy/Caddyfile.staging", import.meta.url),
    "utf8",
  );

  assert.match(caddy, /\{\$SITE_ADDRESS:https:\/\/staging\.jyotisha\.chat\}/);
  assert.match(caddy, /reverse_proxy web:3000/);
  assert.doesNotMatch(caddy, /www\.jyotisha\.chat/);
});

test("staging deploy consumes only the isolated staging environment and tested revision", () => {
  const ci = readFileSync(
    new URL("../../.github/workflows/ci.yml", import.meta.url),
    "utf8",
  );
  const workflow = readFileSync(
    new URL("../../.github/workflows/deploy-staging.yml", import.meta.url),
    "utf8",
  );

  assert.match(ci, /push:\s*\n\s*branches: \[staging\]/);
  assert.match(workflow, /workflows: \["Jyotish Skill CI"\]/);
  assert.match(
    workflow,
    /github\.event\.workflow_run\.head_branch == 'staging'/,
  );
  assert.match(workflow, /actions: read/);
  assert.match(workflow, /environment:\s*\n\s*name: staging/);
  assert.match(workflow, /git_sha:/);
  assert.doesNotMatch(workflow, /default: staging/);
  assert.match(workflow, /test "\$\{#REQUESTED_SHA\}" -eq 40/);
  assert.match(workflow, /actions\/workflows\/ci\.yml\/runs\?head_sha=/);
  assert.match(workflow, /STAGING_SSH_PRIVATE_KEY/);
  assert.match(workflow, /vars\.STAGING_HOST/);
  assert.match(workflow, /vars\.STAGING_KNOWN_HOSTS/);
  assert.match(workflow, /test "\$DEPLOY_HOST" = "118\.26\.111\.127"/);
  assert.match(workflow, /test "\$DEPLOY_USER" = "deploy"/);
  assert.match(workflow, /test "\$DEPLOY_PATH" = "\/opt\/jyotisha-staging"/);
  assert.match(workflow, /--exclude='\.env\*'/);
  assert.match(workflow, /docker compose --env-file \.env\.staging/);
  assert.match(
    workflow,
    /bash deploy\/validate-staging-env\.sh \.env\.staging/,
  );
  assert.match(
    workflow,
    /docker compose --env-file \.env\.staging -f deploy\/docker-compose\.server\.yml config --quiet/,
  );
  assert.match(workflow, /deployment\.gitCommit/);
  assert.doesNotMatch(workflow, /PRODUCTION_SSH_PRIVATE_KEY/);
  assert.doesNotMatch(workflow, /103\.117\.123\.53/);
});

test("staging rsync preserves every destination env variant during delete", () => {
  const workflow = readFileSync(
    new URL("../../.github/workflows/deploy-staging.yml", import.meta.url),
    "utf8",
  );
  const envExclusion = workflow.match(/--exclude='([^']*\.env[^']*)'/)?.[1];

  assert.equal(envExclusion, ".env*");

  const root = mkdtempSync(join(tmpdir(), "jyotisha-staging-rsync-"));
  const source = join(root, "source");
  const destination = join(root, "destination");
  mkdirSync(source);
  mkdirSync(destination);
  writeFileSync(join(source, "app.txt"), "new revision\n");
  for (const name of [
    ".env",
    ".env.local",
    ".env.staging",
    ".env.staging.backup",
  ]) {
    writeFileSync(join(destination, name), "preserve\n");
  }

  try {
    const result = spawnSync(
      "rsync",
      [
        "-a",
        "--delete",
        `--exclude=${envExclusion}`,
        `${source}/`,
        `${destination}/`,
      ],
      { encoding: "utf8" },
    );
    assert.equal(result.status, 0, result.stderr);
    for (const name of [
      ".env",
      ".env.local",
      ".env.staging",
      ".env.staging.backup",
    ]) {
      assert.equal(
        existsSync(join(destination, name)),
        true,
        `${name} was deleted`,
      );
    }
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("staging env validator rejects selector drift, duplicates, and unsafe permissions", () => {
  const validator = fileURLToPath(
    new URL("../../deploy/validate-staging-env.sh", import.meta.url),
  );
  const root = mkdtempSync(join(tmpdir(), "jyotisha-staging-env-"));
  const envFile = join(root, ".env.staging");
  const validSelectors = [
    "APP_ENV_FILE=../.env.staging",
    "CADDYFILE_PATH=./Caddyfile.staging",
    "SITE_ADDRESS=https://staging.jyotisha.chat",
  ];
  const run = () =>
    spawnSync("bash", [validator, envFile], { encoding: "utf8" });
  const writeEnv = (lines: string[], mode = 0o600) => {
    writeFileSync(envFile, `${lines.join("\n")}\n`);
    chmodSync(envFile, mode);
  };

  try {
    writeEnv(validSelectors);
    assert.equal(run().status, 0);

    writeEnv(["APP_ENV_FILE=../.env.production", ...validSelectors.slice(1)]);
    assert.notEqual(run().status, 0);

    writeEnv([...validSelectors, "SITE_ADDRESS=https://example.invalid"]);
    assert.notEqual(run().status, 0);

    writeEnv(validSelectors, 0o644);
    assert.notEqual(run().status, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
