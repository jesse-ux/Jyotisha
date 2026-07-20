import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  chmodSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { startPostgresFixture } from "./helpers/postgres-fixture";

const repositoryRoot = fileURLToPath(new URL("../..", import.meta.url));
const backupScript = join(repositoryRoot, "deploy/backup-staging-postgres.sh");
const fixtureSecrets = [
  "postgres-test-password",
  "schema-owner-test-password",
  "identity-runtime-test-password",
  "app-runtime-test-password",
  "admin-runtime-test-password",
  "migration-runner-test-password",
  "backup-reader-test-password",
  "staging-backup-test-password",
];

function listBackups(directory: string): string[] {
  return readdirSync(directory)
    .filter((name) => /^jyotisha-staging-\d{8}T\d{6}Z\.dump\.enc$/.test(name))
    .sort();
}

function listDumpArchive(fixture: ReturnType<typeof startPostgresFixture>, dump: Buffer): void {
  const hostRestore = spawnSync("pg_restore", ["--list"], {
    input: dump,
    encoding: "utf8",
  });
  if (hostRestore.status === 0) return;

  const result = spawnSync(
    "docker",
    [
      "compose",
      "--project-name",
      fixture.projectName,
      "--env-file",
      fixture.databaseEnvFile,
      "-f",
      "../deploy/docker-compose.postgres.yml",
      "-f",
      "../deploy/docker-compose.postgres-ci.yml",
      "exec",
      "-T",
      "postgres",
      "pg_restore",
      "--list",
    ],
    { cwd: join(repositoryRoot, "frontend"), input: dump, encoding: "utf8" },
  );
  assert.equal(result.status, 0, result.stderr);
}

test("staging backups are encrypted, atomic, private, and retain the newest three", () => {
  const fixture = startPostgresFixture();
  const backupDirectory = mkdtempSync(join(tmpdir(), "jyotisha-staging-backup-"));
  const commandDirectory = mkdtempSync(join(tmpdir(), "jyotisha-backup-command-"));
  const diskUsageCommand = join(commandDirectory, "df");
  const timestamps = [
    "20260720T010101Z",
    "20260720T010102Z",
    "20260720T010103Z",
    "20260720T010104Z",
  ];

  try {
    writeFileSync(
      diskUsageCommand,
      "#!/usr/bin/env bash\nprintf '%s\\n' 'Filesystem 1024-blocks Used Available Capacity Mounted on'\nprintf '%s\\n' '/dev/test 1000 100 900 10% /tmp'\n",
      { mode: 0o700 },
    );
    chmodSync(diskUsageCommand, 0o700);

    for (const timestamp of timestamps) {
      const result = spawnSync(
        "bash",
        [backupScript, fixture.databaseEnvFile, backupDirectory],
        {
          cwd: repositoryRoot,
          encoding: "utf8",
          env: {
            ...process.env,
            BACKUP_TIMESTAMP: timestamp,
            COMPOSE_PROJECT_NAME: fixture.projectName,
            PATH: `${commandDirectory}:${process.env.PATH}`,
          },
        },
      );
      assert.equal(result.status, 0, result.stderr);
      assert.doesNotMatch(`${result.stdout}${result.stderr}`, new RegExp(fixtureSecrets.join("|")));
    }

    const backups = listBackups(backupDirectory);
    assert.deepEqual(backups, [
      "jyotisha-staging-20260720T010102Z.dump.enc",
      "jyotisha-staging-20260720T010103Z.dump.enc",
      "jyotisha-staging-20260720T010104Z.dump.enc",
    ]);
    assert.deepEqual(
      readdirSync(backupDirectory).filter((name) => name.endsWith(".partial")),
      [],
    );
    assert.equal(statSync(backupDirectory).mode & 0o777, 0o700);
    for (const backup of backups) {
      assert.equal(statSync(join(backupDirectory, backup)).mode & 0o777, 0o600);
    }

    const encrypted = readFileSync(join(backupDirectory, backups[0]));
    const decrypted = spawnSync(
      "openssl",
      ["enc", "-d", "-aes-256-cbc", "-pbkdf2", "-pass", "env:STAGING_BACKUP_ENCRYPTION_KEY"],
      {
        input: encrypted,
        env: {
          ...process.env,
          STAGING_BACKUP_ENCRYPTION_KEY: "staging-backup-test-password",
        },
      },
    );
    assert.equal(decrypted.status, 0, decrypted.stderr.toString());
    listDumpArchive(fixture, decrypted.stdout);
  } finally {
    fixture.stop();
    rmSync(backupDirectory, { force: true, recursive: true });
    rmSync(commandDirectory, { force: true, recursive: true });
  }
});
