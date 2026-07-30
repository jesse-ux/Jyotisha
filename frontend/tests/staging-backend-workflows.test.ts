import assert from "node:assert/strict";
import { chmodSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const qualityWorkflow = new URL(
  "../../.github/workflows/backend-quality-gate.yml",
  import.meta.url,
);
const deployWorkflow = new URL(
  "../../.github/workflows/deploy-staging.yml",
  import.meta.url,
);
const migrationWorkflow = new URL(
  "../../.github/workflows/migrate-staging-database.yml",
  import.meta.url,
);
const rolloutWorkflow = new URL(
  "../../.github/workflows/configure-staging-rectification-rollout.yml",
  import.meta.url,
);
const deployScript = new URL(
  "../../deploy/run-staging-deploy.sh",
  import.meta.url,
);
const migrationScript = new URL(
  "../../deploy/run-staging-migration.sh",
  import.meta.url,
);
const rolloutScript = new URL(
  "../../deploy/configure-staging-rectification-rollout.sh",
  import.meta.url,
);
const syncScript = new URL(
  "../../deploy/sync-staging-tree.sh",
  import.meta.url,
);
const stagingCompose = new URL(
  "../../deploy/docker-compose.staging.yml",
  import.meta.url,
);

function read(url: URL): string {
  return readFileSync(url, "utf8");
}

function assertOrder(text: string, labels: string[]): void {
  let previous = -1;
  for (const label of labels) {
    const index = text.indexOf(label);
    assert.ok(index > previous, `${label} is missing or out of order`);
    previous = index;
  }
}

test("changed staging workflows are syntactically valid YAML", () => {
  for (const workflow of [qualityWorkflow, deployWorkflow, migrationWorkflow, rolloutWorkflow]) {
    const result = spawnSync(
      "ruby",
      ["-e", "require 'yaml'; YAML.parse_file(ARGV.fetch(0))", fileURLToPath(workflow)],
      { encoding: "utf8" },
    );
    assert.equal(result.status, 0, result.stderr);
  }
});

test("quality gate validates relevant changes once and publishes a digest manifest", () => {
  const workflow = read(qualityWorkflow);

  assert.match(workflow, /pull_request:\n\s+paths:/);
  for (const path of ["frontend/**", "deploy/**", "scripts/**", "tests/**"]) {
    assert.match(workflow, new RegExp(`'${path.replaceAll("*", "\\*")}'`));
  }
  assert.match(workflow, /push:\n\s+branches: \[staging\]/);
  assert.match(workflow, /workflow_dispatch:/);
  assert.equal((workflow.match(/npm test --prefix frontend/g) ?? []).length, 1);
  assert.match(workflow, /python -m pip install playwright/);
  assert.match(workflow, /python -m playwright install --with-deps chrome/);
  assert.doesNotMatch(workflow, /npm run test:db --prefix frontend/);
  assert.match(workflow, /id: api_build[\s\S]*steps\.api_build\.outputs\.digest/);
  assert.match(workflow, /id: web_build[\s\S]*steps\.web_build\.outputs\.digest/);
  assert.match(workflow, /\^sha256:\[0-9a-f\]\{64\}\$/);
  assert.match(workflow, /node frontend\/scripts\/staging-image-manifest\.mjs/);
  assert.match(workflow, /name: staging-image-manifest-\$\{\{ github\.sha \}\}/);
  assert.match(workflow, /uses: actions\/upload-artifact@v4/);
  assert.doesNotMatch(workflow, /STAGING_SUPABASE|NEXT_PUBLIC_SUPABASE/);
  assert.doesNotMatch(workflow, /(?:^|:)latest$/m);
});

test("quality gate builds the Python package with its declared backend dependencies", () => {
  const workflow = read(qualityWorkflow);

  assert.match(workflow, /^\s+python -m build$/m);
  assert.doesNotMatch(workflow, /python -m build --no-isolation/);
});

test("deployment test command includes manifest behavior coverage", () => {
  const packageJson = JSON.parse(
    readFileSync(new URL("../package.json", import.meta.url), "utf8"),
  ) as { scripts: Record<string, string> };
  const command = packageJson.scripts["test:deployment"];
  assert.match(command, /health-deployment\.test\.ts/);
  assert.match(command, /staging-backend-workflows\.test\.ts/);
  assert.match(command, /staging-image-manifest\.test\.ts/);
});

test("live staging sync preserves env, state, incoming files, and encrypted backups", () => {
  const root = mkdtempSync(join(tmpdir(), "jyotisha-live-sync-"));
  const source = join(root, "source");
  const destination = join(root, "destination");
  mkdirSync(source);
  mkdirSync(destination);
  writeFileSync(join(source, "revision.txt"), "new\n");
  mkdirSync(join(source, ".docker"));
  writeFileSync(join(source, ".docker", "config.json"), "temporary-token\n");
  writeFileSync(join(destination, "stale.txt"), "old\n");
  for (const relative of [
    ".env.staging",
    ".env.staging.database",
    ".state/deployed-revision",
    ".incoming/other-run/payload",
    "backups/staging-db/20260720.dump.gz.gpg",
  ]) {
    const target = join(destination, relative);
    mkdirSync(join(target, ".."), { recursive: true });
    writeFileSync(target, "preserve\n");
  }

  try {
    const result = spawnSync(
      "bash",
      [fileURLToPath(syncScript), source, destination],
      { encoding: "utf8" },
    );
    assert.equal(result.status, 0, result.stderr);
    assert.equal(existsSync(join(destination, "stale.txt")), false);
    assert.equal(readFileSync(join(destination, "revision.txt"), "utf8"), "new\n");
    assert.equal(existsSync(join(destination, ".docker")), false);
    for (const relative of [
      ".env.staging",
      ".env.staging.database",
      ".state/deployed-revision",
      ".incoming/other-run/payload",
      "backups/staging-db/20260720.dump.gz.gpg",
    ]) {
      assert.equal(existsSync(join(destination, relative)), true, relative);
    }
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("live staging sync repairs a non-writable deploy tree without preserving foreign ownership", () => {
  const root = mkdtempSync(join(tmpdir(), "jyotisha-live-sync-permissions-"));
  const source = join(root, "source");
  const destination = join(root, "destination");
  const destinationDeploy = join(destination, "deploy");
  const mockBin = join(root, "bin");
  const dockerLog = join(root, "docker.log");
  mkdirSync(join(source, "deploy"), { recursive: true });
  mkdirSync(destinationDeploy, { recursive: true });
  mkdirSync(mockBin);
  writeFileSync(join(source, "deploy", "current.txt"), "new\n");
  writeFileSync(join(destinationDeploy, "stale.txt"), "old\n");
  writeFileSync(
    join(mockBin, "docker"),
    [
      "#!/usr/bin/env bash",
      "set -euo pipefail",
      "printf '%s\\n' \"$*\" >\"$DOCKER_LOG\"",
      'chmod -R u+rwX "$REPAIR_DESTINATION"',
      "",
    ].join("\n"),
  );
  chmodSync(join(mockBin, "docker"), 0o755);
  chmodSync(destinationDeploy, 0o555);

  try {
    const result = spawnSync(
      "bash",
      [fileURLToPath(syncScript), source, destination],
      {
        encoding: "utf8",
        env: {
          ...process.env,
          PATH: `${mockBin}:${process.env.PATH ?? ""}`,
          DOCKER_LOG: dockerLog,
          REPAIR_DESTINATION: destinationDeploy,
        },
      },
    );
    assert.equal(result.status, 0, result.stderr);
    assert.equal(existsSync(join(destinationDeploy, "stale.txt")), false);
    assert.equal(
      readFileSync(join(destinationDeploy, "current.txt"), "utf8"),
      "new\n",
    );
    const invocation = readFileSync(dockerLog, "utf8");
    assert.match(invocation, /--network none --read-only --user 0:0/);
    assert.match(invocation, /--cap-drop ALL --cap-add CHOWN/);
    assert.match(invocation, /postgres:17-alpine chown -R/);
    assert.match(read(syncScript), /--no-owner --no-group/);
  } finally {
    if (existsSync(destinationDeploy)) chmodSync(destinationDeploy, 0o755);
    rmSync(root, { recursive: true, force: true });
  }
});

test("all staging mutations share Actions serialization and one host lock", () => {
  const deployment = read(deployWorkflow);
  const migration = read(migrationWorkflow);
  const deployRunner = read(deployScript);
  const migrationRunner = read(migrationScript);

  const rollout = read(rolloutWorkflow);
  const rolloutRunner = read(rolloutScript);

  for (const workflow of [deployment, migration, rollout]) {
    assert.match(workflow, /concurrency:\n\s+group: staging-mutation\n\s+cancel-in-progress: false/);
  }
  for (const runner of [deployRunner, migrationRunner, rolloutRunner]) {
    assert.match(runner, /state_directory="\$DEPLOY_PATH\/\.state"/);
    assert.match(runner, /state_directory\/mutation\.lock/);
    assert.match(runner, /flock -n 9/);
    assert.ok(runner.indexOf("flock -n 9") < runner.indexOf("docker"));
  }
  for (const runner of [deployRunner, migrationRunner]) {
    assert.ok(runner.indexOf("flock -n 9") < runner.indexOf("sync-staging-tree.sh"));
  }
});

test("deploy and migration consume the exact successful gate artifact", () => {
  const deployment = read(deployWorkflow);
  const migration = read(migrationWorkflow);

  for (const workflow of [deployment, migration]) {
    assert.match(workflow, /backend-quality-gate\.yml\/runs\?head_sha=/);
    assert.match(workflow, /\.head_branch == "staging"/);
    assert.match(workflow, /\.event == "push"/);
    assert.match(workflow, /\.conclusion == "success"/);
    assert.match(workflow, /sort_by\(\.id\) \| reverse \| first/);
    assert.match(workflow, /uses: actions\/download-artifact@v4/);
    assert.match(workflow, /run-id: \$\{\{ steps\.revision\.outputs\.gate_run_id \}\}/);
    assert.match(workflow, /node frontend\/scripts\/staging-image-manifest\.mjs/);
    assert.doesNotMatch(workflow, /jyotisha-(?:api|web):\$[A-Z_]*SHA/);
  }
});

test("main owns the deployment control plane and target revisions are data only", () => {
  for (const workflow of [read(deployWorkflow), read(migrationWorkflow)]) {
    assert.match(workflow, /name: Checkout trusted main controller[\s\S]*ref: main/);
    assert.match(workflow, /fetch-depth: 0/);
    assert.match(workflow, /git merge-base --is-ancestor "\$DEPLOY_SHA" HEAD/);
    assert.match(workflow, /--include='\/deploy\/' --include='\/deploy\/\*\*\*' --exclude='\*'/);
    assert.doesNotMatch(workflow, /ref: \$\{\{ steps\.revision\.outputs\.sha \}\}/);
  }
});

test("staging mutations retain every pending deployment and migration", () => {
  for (const workflow of [read(deployWorkflow), read(migrationWorkflow)]) {
    assert.match(
      workflow,
      /concurrency:\n  group: staging-mutation\n  cancel-in-progress: false\n  queue: max/,
    );
  }
});

test("automatic staging paths reject stale and divergent revisions", () => {
  const deployment = read(deployWorkflow);
  const migration = read(migrationWorkflow);

  assert.match(deployment, /allow_rollback:/);
  assert.match(deployment, /rollback authorization is manual-only/);
  assert.match(deployment, /stale staging revision refused/);
  assert.match(deployment, /compare\/\$previous_sha\.\.\.\$DEPLOY_SHA/);
  assert.match(deployment, /\.status == "ahead" and \.merge_base_commit\.sha == \$base/);
  assert.match(migration, /stale staging migration refused/);
  assert.match(migration, /staging advanced during migration; refusing stale deployment dispatch/);
  assert.match(migration, /\{ref:"main",inputs:\{deploy_sha:\$deploy_sha,allow_rollback:"false"\}\}/);
});

test("remote deployment verifies running image IDs, RepoDigests, and application SHA", () => {
  const runner = read(deployScript);

  assert.match(runner, /docker inspect --format '\{\{\.Image\}\}'/);
  assert.match(runner, /docker image inspect --format '\{\{\.Id\}\}' "\$expected_ref"/);
  assert.match(runner, /RepoDigests/);
  assert.match(runner, /grep -Fqx "\$expected_ref"/);
  assert.match(runner, /publicBody\.deployment\?\.gitCommit !== process\.env\.EXPECTED_SHA/);
  assert.match(runner, /mv -f "\$revision_file" "\$state_directory\/deployed-revision"/);
  assert.match(runner, /restoring prior application images/);
  assert.match(
    runner,
    /switched=true\n"\$\{compose\[@\]\}" up -d --no-build --remove-orphans\n/,
  );
  assert.doesNotMatch(runner, /jyotisha-(?:api|web):\$DEPLOY_SHA/);
});

test("first immutable deployment rolls back to validated local image IDs", () => {
  const root = mkdtempSync(join(tmpdir(), "jyotisha-local-image-rollback-"));
  const deploymentPath = join(root, "live");
  const incomingPath = join(deploymentPath, ".incoming", "run-1");
  const incomingDeploy = join(incomingPath, "deploy");
  const liveDeploy = join(deploymentPath, "deploy");
  const mockBin = join(root, "bin");
  const rollbackLog = join(root, "rollback.log");
  const previousSha = "1".repeat(40);
  const previousApiId = `sha256:${"a".repeat(64)}`;
  const previousWebId = `sha256:${"b".repeat(64)}`;
  const nextSha = "2".repeat(40);

  mkdirSync(incomingDeploy, { recursive: true });
  mkdirSync(liveDeploy, { recursive: true });
  mkdirSync(join(deploymentPath, ".state"), { recursive: true });
  mkdirSync(mockBin);
  writeFileSync(join(deploymentPath, ".state", "deployed-revision"), `${previousSha}\n`);
  for (const script of [
    join(incomingDeploy, "sync-staging-tree.sh"),
    join(liveDeploy, "validate-staging-env.sh"),
    join(liveDeploy, "validate-staging-database-env.sh"),
  ]) {
    writeFileSync(script, "#!/usr/bin/env bash\nexit 0\n");
    chmodSync(script, 0o755);
  }
  writeFileSync(
    join(mockBin, "docker"),
    [
      "#!/usr/bin/env bash",
      "set -euo pipefail",
      "if [ \"$1\" = ps ]; then",
      "  case \"$*\" in",
      "    *service=api*) echo container-api ;;",
      "    *service=web*) echo container-web ;;",
      "  esac",
      "  exit 0",
      "fi",
      "if [ \"$1\" = inspect ]; then",
      `  if [ \"\${!#}\" = container-api ]; then echo '${previousApiId}'; else echo '${previousWebId}'; fi`,
      "  exit 0",
      "fi",
      "if [ \"$1\" = image ]; then exit 0; fi",
      "if [ \"$1\" = compose ]; then",
      "  if [[ \" $* \" == *\" up -d --no-build --remove-orphans \"* ]]; then",
      `    printf '%s|%s|%s|%s\\n' \"\${API_IMAGE:-}\" \"\${WEB_IMAGE:-}\" \"\${GITHUB_SHA:-}\" \"$*\" >>'${rollbackLog}'`,
      "    [[ \"$*\" == *\" api web rectification-v4-worker caddy\" ]] && exit 0",
      "    exit 42",
      "  fi",
      "  exit 0",
      "fi",
      "exit 1",
      "",
    ].join("\n"),
  );
  chmodSync(join(mockBin, "docker"), 0o755);
  writeFileSync(join(mockBin, "flock"), "#!/usr/bin/env bash\nexit 0\n");
  chmodSync(join(mockBin, "flock"), 0o755);

  try {
    const result = spawnSync("bash", [fileURLToPath(deployScript)], {
      encoding: "utf8",
      env: {
        ...process.env,
        PATH: `${mockBin}:${process.env.PATH ?? ""}`,
        INCOMING_PATH: incomingPath,
        DEPLOY_PATH: deploymentPath,
        API_IMAGE: `ghcr.io/jesse-ux/jyotisha-api@sha256:${"c".repeat(64)}`,
        WEB_IMAGE: `ghcr.io/jesse-ux/jyotisha-web@sha256:${"d".repeat(64)}`,
        DEPLOY_SHA: nextSha,
        EXPECTED_PREVIOUS_SHA: previousSha,
        ALLOW_ROLLBACK: "false",
        FORWARD_REVISION_VERIFIED: "true",
        DOCKER_CONFIG: join(incomingPath, ".docker"),
        STAGING_URL: "https://staging.jyotisha.chat",
      },
    });
    assert.equal(result.status, 42, result.stderr);
    const attempts = readFileSync(rollbackLog, "utf8").trim().split("\n");
    assert.equal(attempts.length, 2);
    assert.match(
      attempts[1],
      new RegExp(`^${previousApiId}\\|${previousWebId}\\|${previousSha}\\|`),
    );
    assert.match(attempts[1], /api web rectification-v4-worker caddy$/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("normal deployment checks migrations but never applies them", () => {
  const runner = read(deployScript);
  assert.match(runner, /-f deploy\/docker-compose\.staging\.yml/);
  assertOrder(runner, [
    "pull api web",
    "up -d --no-build --pull never --wait postgres",
    "--profile migration-check run --rm migration-checker",
    "up -d --no-build --remove-orphans",
  ]);
  assert.match(runner, /pending migrations: run Migrate Staging Database/);
  assert.match(runner, /exit 3/);
  assert.doesNotMatch(runner, /--profile migration run --rm migrator/);
  assert.doesNotMatch(runner, /npm\s+run\s+db:migrate(?!:check)/);
  assert.doesNotMatch(runner, /pull api web postgres/);
  assert.match(runner, /verify_container_image rectification-v4-worker \"\$WEB_IMAGE\"/);
  assert.match(runner, /adminRoot\.status !== 302/);
  assert.match(runner, /adminRoot\.headers\.get\("location"\) !== "\/admin\/codes"/);
});

test("staging runs the rectification V4 worker from the immutable web image", () => {
  const compose = read(stagingCompose);
  assert.match(compose, /rectification-v4-worker:/);
  assert.match(compose, /image: \$\{WEB_IMAGE:-jyotisha-web:local\}/);
  assert.match(compose, /command: \["npm", "run", "worker:rectification-v4"\]/);
  assert.ok(compose.includes("JYOTISH_API_BASE: http://api:5200"));
});

test("manual migration uses only PostgreSQL and the digest-pinned migrator", () => {
  const workflow = read(migrationWorkflow);
  const runner = read(migrationScript);

  assert.match(workflow, /^on:\n\s+workflow_dispatch:/m);
  assert.doesNotMatch(workflow, /workflow_run:|\n\s+push:/);
  assert.match(runner, /docker pull "\$WEB_IMAGE"/);
  assert.match(runner, /up -d --no-build --pull never --wait postgres/);
  assert.match(runner, /-f deploy\/docker-compose\.postgres\.yml/);
  assertOrder(runner, [
    "up -d --no-build --pull never --wait postgres",
    "002-ensure-business-compatibility-roles.sql",
    "--profile migration run --rm migrator",
  ]);
  assert.match(runner, /--profile migration run --rm migrator/);
  assert.match(runner, /select filename from migration\.schema_migrations order by filename/);
  assert.doesNotMatch(runner, /docker-compose\.server\.yml/);
  assert.doesNotMatch(runner, /\bup\b[^\n]*(?:api|web|caddy)/);
});

test("run-local registry state and incoming trees are always cleaned up", () => {
  for (const workflow of [read(deployWorkflow), read(migrationWorkflow)]) {
    assert.match(workflow, /DOCKER_CONFIG='\$INCOMING_PATH\/\.docker'/);
    assert.match(workflow, /if: always\(\) && steps\.incoming\.outputs\.path != ''/);
    assert.match(workflow, /docker logout ghcr\.io/);
    assert.match(workflow, /rm -rf -- '\$INCOMING_PATH'/);
    assert.match(
      workflow,
      /install -d -m 700 [^\n]*\$incoming[^\n]*\n\s+echo "path=\$incoming" >>"\$GITHUB_OUTPUT"\n\s+rsync/,
    );
    assert.doesNotMatch(workflow, /--password(?:\s|=)/);
  }
});

test("production remains manual-only and separate from staging database automation", () => {
  const production = readFileSync(
    new URL("../../.github/workflows/deploy-production.yml", import.meta.url),
    "utf8",
  );
  assert.match(production, /^on:\n\s+workflow_dispatch:/m);
  assert.doesNotMatch(production, /workflow_run:|\n\s+push:/);
  assert.doesNotMatch(production, /docker-compose\.postgres\.yml|db:migrate/);
});


test("public rectification rollout enables the semantic agent and recreates web runtimes", () => {
  const root = mkdtempSync(join(tmpdir(), "jyotisha-rollout-"));
  const deploymentPath = join(root, "app");
  const statePath = join(deploymentPath, ".state");
  const deployPath = join(deploymentPath, "deploy");
  const mockBin = join(root, "bin");
  const sha = "8".repeat(40);
  mkdirSync(statePath, { recursive: true });
  mkdirSync(deployPath, { recursive: true });
  mkdirSync(mockBin, { recursive: true });
  writeFileSync(join(statePath, "deployed-revision"), sha);
  writeFileSync(
    join(deploymentPath, ".env.staging"),
    [
      "APP_ENV_FILE=../.env.staging",
      "CADDYFILE_PATH=./Caddyfile.staging",
      "SITE_ADDRESS=https://staging.jyotisha.chat",
      "ADMIN_SITE_ADDRESS=https://admin.staging.jyotisha.chat",
      "AUTH_PROVIDER=self-hosted",
      "SELF_HOSTED_IDENTITY_ENABLED=true",
      "AUTH_USER_ORIGIN=https://staging.jyotisha.chat",
      "AUTH_ADMIN_ORIGIN=https://admin.staging.jyotisha.chat",
      `IDENTITY_DATABASE_URL=postgresql://identity_runtime:${"i".repeat(40)}@postgres:5432/jyotisha`,
      `APP_DATABASE_URL=postgresql://app_runtime:${"a".repeat(40)}@postgres:5432/jyotisha`,
      `ADMIN_DATABASE_URL=postgresql://admin_runtime:${"d".repeat(40)}@postgres:5432/jyotisha`,
      `BETTER_AUTH_USER_SECRET=${"u".repeat(32)}`,
      `BETTER_AUTH_ADMIN_SECRET=${"v".repeat(32)}`,
      "RESEND_API_KEY=re_test_key",
      "RESEND_FROM_EMAIL=test@example.com",
      "ADMIN_EMAILS=admin@example.com",
      `JYOTISH_DYNAMIC_RECTIFICATION_TOKEN=${"t".repeat(32)}`,
      "KEEP_ME=unchanged",
      "RECTIFICATION_V3_CREATE_ENABLED=false",
      "RECTIFICATION_V3_MIGRATIONS_READY=false",
      "RECTIFICATION_V3_SYNTHETIC_SMOKE_SHA=old",
      "RECTIFICATION_V3_SYNTHETIC_SMOKE_USER_IDS=00000000-0000-4000-8000-000000009001",
      "RECTIFICATION_AGENT_V5_ENABLED=false",
      "RECTIFICATION_AGENT_V5_SHADOW=true",
      "RECTIFICATION_AGENT_V5_CANARY_PERCENT=0",
      "",
    ].join("\n"),
    { mode: 0o600 },
  );
  writeFileSync(
    join(deployPath, "validate-staging-env.sh"),
    readFileSync(new URL("../../deploy/validate-staging-env.sh", import.meta.url), "utf8"),
  );
  writeFileSync(join(mockBin, "flock"), "#!/usr/bin/env bash\nexit 0\n");
  writeFileSync(
    join(mockBin, "docker"),
    [
      "#!/usr/bin/env bash",
      'if [ "$1" = ps ]; then echo web-container; exit 0; fi',
      `if [ "$1" = inspect ] && [[ "$*" == *Config.Image* ]]; then echo ghcr.io/jesse-ux/jyotisha-web@sha256:${"b".repeat(64)}; exit 0; fi`,
      'if [ "$1" = inspect ] && [[ "$*" == *Config.Env* ]]; then printf "%s\n" RECTIFICATION_AGENT_V5_ENABLED=true RECTIFICATION_AGENT_V5_SHADOW=false RECTIFICATION_AGENT_V5_CANARY_PERCENT=100; exit 0; fi',
      `printf '%s\n' "$*" >>${join(root, "docker.log")}`,
    ].join("\n"),
  );
  writeFileSync(
    join(mockBin, "curl"),
    `#!/usr/bin/env bash\nprintf '%s' '{"deployment":{"gitCommit":"${sha}"},"rollout":{"conversationalRectificationV3":{"creationAudience":"public","readyForNewCases":true}}}'\n`,
  );
  for (const command of ["flock", "docker", "curl"]) {
    chmodSync(join(mockBin, command), 0o755);
  }

  try {
    const result = spawnSync("bash", [fileURLToPath(rolloutScript)], {
      encoding: "utf8",
      env: {
        ...process.env,
        PATH: `${mockBin}:${process.env.PATH ?? ""}`,
        DEPLOY_PATH: deploymentPath,
        EXPECTED_DEPLOY_SHA: sha,
        ROLLOUT_AUDIENCE: "public",
        SYNTHETIC_SMOKE_USER_IDS: "",
        STAGING_URL: "https://staging.jyotisha.chat",
      },
    });
    assert.equal(result.status, 0, result.stderr);
    const env = readFileSync(join(deploymentPath, ".env.staging"), "utf8");
    assert.match(env, /^KEEP_ME=unchanged$/m);
    assert.match(env, /^RECTIFICATION_V3_CREATE_ENABLED=true$/m);
    assert.match(env, /^RECTIFICATION_V3_MIGRATIONS_READY=true$/m);
    assert.match(env, new RegExp(`^RECTIFICATION_V3_SYNTHETIC_SMOKE_SHA=${sha}$`, "m"));
    assert.match(env, /^RECTIFICATION_V3_SYNTHETIC_SMOKE_USER_IDS=$/m);
    assert.match(env, /^RECTIFICATION_AGENT_V5_ENABLED=true$/m);
    assert.match(env, /^RECTIFICATION_AGENT_V5_SHADOW=false$/m);
    assert.match(env, /^RECTIFICATION_AGENT_V5_CANARY_PERCENT=100$/m);
    assert.equal((env.match(/^RECTIFICATION_V3_CREATE_ENABLED=/gm) ?? []).length, 1);
    assert.equal((env.match(/^RECTIFICATION_AGENT_V5_ENABLED=/gm) ?? []).length, 1);
    assert.equal((env.match(/^RECTIFICATION_AGENT_V5_SHADOW=/gm) ?? []).length, 1);
    assert.equal((env.match(/^RECTIFICATION_AGENT_V5_CANARY_PERCENT=/gm) ?? []).length, 1);
    assert.match(readFileSync(join(root, "docker.log"), "utf8"), /force-recreate --no-deps web rectification-v4-worker/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("staging scripts pass shell syntax validation", () => {
  for (const script of [deployScript, migrationScript, rolloutScript, syncScript]) {
    const path = fileURLToPath(script);
    chmodSync(path, 0o755);
    const result = spawnSync("bash", ["-n", path], { encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr);
  }
});
