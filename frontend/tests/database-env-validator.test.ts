import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  chmodSync,
  mkdtempSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { test } from "node:test";

const repositoryRoot = fileURLToPath(new URL("../..", import.meta.url));
const validator = join(repositoryRoot, "deploy/validate-staging-database-env.sh");
const validEnvironment = [
  "POSTGRES_DB=jyotisha",
  "POSTGRES_USER=postgres",
  "POSTGRES_PASSWORD=postgres-test-password",
  "SCHEMA_OWNER_PASSWORD=schema-owner-test-password",
  "IDENTITY_RUNTIME_PASSWORD=identity-runtime-test-password",
  "APP_RUNTIME_PASSWORD=app-runtime-test-password",
  "ADMIN_RUNTIME_PASSWORD=admin-runtime-test-password",
  "MIGRATION_RUNNER_PASSWORD=migration-runner-test-password",
  "BACKUP_READER_PASSWORD=backup-reader-test-password",
  "STAGING_BACKUP_ENCRYPTION_KEY=staging-backup-test-password",
  "SCHEMA_DATABASE_URL=postgresql://schema_owner:schema-owner%2Dtest-password@postgres:5432/jyotisha",
];

test("database env validator rejects Compose-compatible duplicate selectors without printing values", () => {
  const root = mkdtempSync(join(tmpdir(), "jyotisha-database-env-"));
  const envFile = join(root, ".env.staging.database");
  const composeFile = join(root, "compose.yml");

  try {
    writeFileSync(
      composeFile,
      [
        "services:",
        "  probe:",
        "    image: alpine",
        "    environment:",
        "      SELECTED: ${POSTGRES_DB}",
        "",
      ].join("\n"),
    );
    writeFileSync(
      envFile,
      `${[...validEnvironment, " POSTGRES_DB = evil"].join("\n")}\n`,
      { mode: 0o600 },
    );
    chmodSync(envFile, 0o600);

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
      "evil",
    );

    const result = spawnSync("bash", [validator, envFile], { encoding: "utf8" });
    assert.notEqual(result.status, 0);
    assert.doesNotMatch(
      `${result.stdout}${result.stderr}`,
      /postgres-test-password|schema-owner-test-password|staging-backup-test-password/,
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("database env validator rejects bare Compose-compatible duplicate definitions", () => {
  const root = mkdtempSync(join(tmpdir(), "jyotisha-database-env-"));
  const envFile = join(root, ".env.staging.database");

  try {
    writeFileSync(
      envFile,
      `${[...validEnvironment, " POSTGRES_DB"].join("\n")}\n`,
      { mode: 0o600 },
    );
    chmodSync(envFile, 0o600);

    const result = spawnSync("bash", [validator, envFile], { encoding: "utf8" });
    assert.notEqual(result.status, 0);
    assert.doesNotMatch(
      `${result.stdout}${result.stderr}`,
      /postgres-test-password|schema-owner-test-password|staging-backup-test-password/,
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("database env validator rejects quoted and interpolated required secrets", () => {
  const root = mkdtempSync(join(tmpdir(), "jyotisha-database-env-"));
  const envFile = join(root, ".env.staging.database");

  try {
    for (const password of ['""', "''", "${UNSET}"]) {
      writeFileSync(
        envFile,
        `${validEnvironment
          .map((line) =>
            line.startsWith("POSTGRES_PASSWORD=")
              ? `POSTGRES_PASSWORD=${password}`
              : line,
          )
          .join("\n")}\n`,
        { mode: 0o600 },
      );
      chmodSync(envFile, 0o600);

      const result = spawnSync("bash", [validator, envFile], { encoding: "utf8" });
      assert.notEqual(result.status, 0, password);
      assert.doesNotMatch(
        `${result.stdout}${result.stderr}`,
        /postgres-test-password|schema-owner-test-password|staging-backup-test-password/,
      );
    }
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("database env validator accepts punctuated literal required secrets", () => {
  const root = mkdtempSync(join(tmpdir(), "jyotisha-database-env-"));
  const envFile = join(root, ".env.staging.database");

  try {
    for (const password of ["c2VjcmV0IT0=", '"secret!=value"']) {
      writeFileSync(
        envFile,
        `${validEnvironment
          .map((line) =>
            line.startsWith("POSTGRES_PASSWORD=")
              ? `POSTGRES_PASSWORD=${password}`
              : line,
          )
          .join("\n")}\n`,
        { mode: 0o600 },
      );
      chmodSync(envFile, 0o600);

      const result = spawnSync("bash", [validator, envFile], { encoding: "utf8" });
      assert.equal(result.status, 0, result.stderr);
      assert.equal(result.stdout, "staging database environment validated\n");
      assert.doesNotMatch(`${result.stdout}${result.stderr}`, /secret!=value|c2VjcmV0IT0=/);
    }
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("database env validator rejects symlinks and unsafe modes", () => {
  const root = mkdtempSync(join(tmpdir(), "jyotisha-database-env-"));
  const envFile = join(root, ".env.staging.database");
  const target = join(root, "database-target.env");

  try {
    writeFileSync(target, `${validEnvironment.join("\n")}\n`, { mode: 0o600 });
    chmodSync(target, 0o600);
    symlinkSync(target, envFile);
    assert.notEqual(
      spawnSync("bash", [validator, envFile], { encoding: "utf8" }).status,
      0,
    );

    rmSync(envFile);
    writeFileSync(envFile, `${validEnvironment.join("\n")}\n`, { mode: 0o644 });
    chmodSync(envFile, 0o644);
    assert.notEqual(
      spawnSync("bash", [validator, envFile], { encoding: "utf8" }).status,
      0,
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("database env validator accepts a private valid file without printing values", () => {
  const root = mkdtempSync(join(tmpdir(), "jyotisha-database-env-"));
  const envFile = join(root, ".env.staging.database");

  try {
    writeFileSync(envFile, `${validEnvironment.join("\n")}\n`, { mode: 0o600 });
    chmodSync(envFile, 0o600);

    const result = spawnSync("bash", [validator, envFile], { encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stdout, "staging database environment validated\n");
    assert.doesNotMatch(
      `${result.stdout}${result.stderr}`,
      /postgres-test-password|schema-owner-test-password|staging-backup-test-password/,
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("staging database environment file is ignored", () => {
  const result = spawnSync("git", ["check-ignore", ".env.staging.database"], {
    cwd: repositoryRoot,
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout, ".env.staging.database\n");
});
