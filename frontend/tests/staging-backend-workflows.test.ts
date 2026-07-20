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
const deployScript = new URL(
  "../../deploy/run-staging-deploy.sh",
  import.meta.url,
);
const migrationScript = new URL(
  "../../deploy/run-staging-migration.sh",
  import.meta.url,
);
const syncScript = new URL(
  "../../deploy/sync-staging-tree.sh",
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
  for (const workflow of [qualityWorkflow, deployWorkflow, migrationWorkflow]) {
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
  assert.doesNotMatch(workflow, /npm run test:db --prefix frontend/);
  assert.match(workflow, /id: api_build[\s\S]*steps\.api_build\.outputs\.digest/);
  assert.match(workflow, /id: web_build[\s\S]*steps\.web_build\.outputs\.digest/);
  assert.match(workflow, /\^sha256:\[0-9a-f\]\{64\}\$/);
  assert.match(workflow, /node frontend\/scripts\/staging-image-manifest\.mjs/);
  assert.match(workflow, /name: staging-image-manifest-\$\{\{ github\.sha \}\}/);
  assert.match(workflow, /uses: actions\/upload-artifact@v4/);
  assert.doesNotMatch(workflow, /(?:^|:)latest$/m);
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

test("all staging mutations share Actions serialization and one host lock", () => {
  const deployment = read(deployWorkflow);
  const migration = read(migrationWorkflow);
  const deployRunner = read(deployScript);
  const migrationRunner = read(migrationScript);

  for (const workflow of [deployment, migration]) {
    assert.match(workflow, /concurrency:\n\s+group: staging-mutation\n\s+cancel-in-progress: false/);
  }
  for (const runner of [deployRunner, migrationRunner]) {
    assert.match(runner, /state_directory="\$DEPLOY_PATH\/\.state"/);
    assert.match(runner, /state_directory\/mutation\.lock/);
    assert.match(runner, /flock -n 9/);
    assert.ok(runner.indexOf("flock -n 9") < runner.indexOf("sync-staging-tree.sh"));
    assert.ok(runner.indexOf("flock -n 9") < runner.indexOf("docker"));
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
  assert.match(runner, /restoring prior image digests/);
  assert.match(
    runner,
    /switched=true\n"\$\{compose\[@\]\}" up -d --no-build --remove-orphans\n/,
  );
  assert.doesNotMatch(runner, /jyotisha-(?:api|web):\$DEPLOY_SHA/);
});

test("normal deployment checks migrations but never applies them", () => {
  const runner = read(deployScript);
  assertOrder(runner, [
    "pull api web postgres",
    "up -d --no-build --wait postgres",
    "--profile migration-check run --rm migration-checker",
    "up -d --no-build --remove-orphans",
  ]);
  assert.match(runner, /pending migrations: run Migrate Staging Database/);
  assert.match(runner, /exit 3/);
  assert.doesNotMatch(runner, /--profile migration run --rm migrator/);
  assert.doesNotMatch(runner, /npm\s+run\s+db:migrate(?!:check)/);
});

test("manual migration uses only PostgreSQL and the digest-pinned migrator", () => {
  const workflow = read(migrationWorkflow);
  const runner = read(migrationScript);

  assert.match(workflow, /^on:\n\s+workflow_dispatch:/m);
  assert.doesNotMatch(workflow, /workflow_run:|\n\s+push:/);
  assert.match(runner, /docker pull "\$WEB_IMAGE"/);
  assert.match(runner, /-f deploy\/docker-compose\.postgres\.yml/);
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

test("staging scripts pass shell syntax validation", () => {
  for (const script of [deployScript, migrationScript, syncScript]) {
    const path = fileURLToPath(script);
    chmodSync(path, 0o755);
    const result = spawnSync("bash", ["-n", path], { encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr);
  }
});
