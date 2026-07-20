import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import {
  chmodSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  realpathSync,
  rmSync,
  statSync,
  symlinkSync,
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
const databaseEnvironment = `POSTGRES_DB=jyotisha
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres-test-password
SCHEMA_OWNER_PASSWORD=schema-owner-test-password
IDENTITY_RUNTIME_PASSWORD=identity-runtime-test-password
APP_RUNTIME_PASSWORD=app-runtime-test-password
ADMIN_RUNTIME_PASSWORD=admin-runtime-test-password
MIGRATION_RUNNER_PASSWORD=migration-runner-test-password
BACKUP_READER_PASSWORD=backup-reader-test-password
STAGING_BACKUP_ENCRYPTION_KEY=staging-backup-test-password
SCHEMA_DATABASE_URL=postgresql://schema_owner:schema-owner-test-password@postgres:5432/jyotisha
`;

function listBackups(directory: string): string[] {
  return readdirSync(directory)
    .filter((name) => /^jyotisha-staging-\d{8}T\d{6}Z\.dump\.enc$/.test(name))
    .sort();
}

function canonicalTemporaryDirectory(prefix: string): string {
  return realpathSync(mkdtempSync(join(tmpdir(), prefix)));
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

function createDatabaseEnvironment(): { directory: string; file: string } {
  const directory = mkdtempSync(join(tmpdir(), "jyotisha-backup-env-"));
  const file = join(directory, "database.env");
  writeFileSync(file, databaseEnvironment, { mode: 0o600 });
  chmodSync(file, 0o600);
  return { directory, file };
}

function writeCommand(directory: string, name: string, script: string): void {
  const path = join(directory, name);
  writeFileSync(path, `#!/usr/bin/env bash\nset -eu\n${script}\n`, { mode: 0o700 });
  chmodSync(path, 0o700);
}

function safeDiskCommand(directory: string, usage = 10): void {
  writeCommand(
    directory,
    "df",
    `printf '%s\\n' 'Filesystem 1024-blocks Used Available Capacity Mounted on'\nprintf '%s\\n' '/dev/test 1000 100 900 ${usage}% /tmp'`,
  );
}

function backupEnvironment(commandDirectory: string, extra: NodeJS.ProcessEnv = {}): NodeJS.ProcessEnv {
  return {
    ...process.env,
    ...extra,
    PATH: `${commandDirectory}:${process.env.PATH ?? ""}`,
  };
}

function runBackup(
  databaseEnvFile: string,
  backupDirectory: string,
  environment: NodeJS.ProcessEnv,
  cwd = repositoryRoot,
) {
  return spawnSync("bash", [backupScript, databaseEnvFile, backupDirectory], {
    cwd,
    encoding: "utf8",
    env: environment,
  });
}

function runBackupAsync(
  databaseEnvFile: string,
  backupDirectory: string,
  environment: NodeJS.ProcessEnv,
): Promise<{ status: number | null; stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    const child = spawn("bash", [backupScript, databaseEnvFile, backupDirectory], {
      cwd: repositoryRoot,
      env: environment,
    });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.once("error", reject);
    child.once("close", (status) => resolve({ status, stdout, stderr }));
  });
}

test("staging backups are encrypted, atomic, private, and retain the newest three", () => {
  const fixture = startPostgresFixture();
  const backupDirectory = canonicalTemporaryDirectory("jyotisha-staging-backup-");
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

test("rejects destructive backup directory aliases and symlink components before mutation", () => {
  const root = mkdtempSync(join(tmpdir(), "jyotisha-backup-boundary-"));
  const environmentFile = createDatabaseEnvironment();
  const target = join(root, "target");
  const sentinel = join(target, "sentinel.txt");
  const originalMode = 0o755;

  try {
    mkdirSync(target, { mode: originalMode });
    chmodSync(target, originalMode);
    writeFileSync(sentinel, "must remain untouched");
    symlinkSync(target, join(root, "backup-link"));

    for (const directory of [
      "/",
      "/tmp/..",
      "/tmp//canonical-alias",
      "relative-backup",
      `${target}/../attempt`,
      `${target}/`,
      join(root, "backup-link"),
      join(root, "backup-link", "nested"),
    ]) {
      const result = runBackup(
        environmentFile.file,
        directory,
        process.env,
        root,
      );
      assert.notEqual(result.status, 0);
      assert.match(
        result.stderr,
        /backup directory must be an absolute path without traversal, aliases, or symlinks/,
      );
    }

    assert.equal(statSync(target).mode & 0o777, originalMode);
    assert.equal(readFileSync(sentinel, "utf8"), "must remain untouched");
    assert.deepEqual(readdirSync(target), ["sentinel.txt"]);
  } finally {
    rmSync(root, { force: true, recursive: true });
    rmSync(environmentFile.directory, { force: true, recursive: true });
  }
});

test("same-second backups publish once without overwriting the completed archive", async () => {
  const environmentFile = createDatabaseEnvironment();
  const backupDirectory = canonicalTemporaryDirectory("jyotisha-backup-collision-");
  const commandDirectory = mkdtempSync(join(tmpdir(), "jyotisha-backup-collision-command-"));
  const timestamp = "20260720T020202Z";

  try {
    safeDiskCommand(commandDirectory);
    writeCommand(
      commandDirectory,
      "docker",
      "sleep 0.5\nprintf '%s' 'same-second dump payload'",
    );
    const environment = backupEnvironment(commandDirectory, {
      BACKUP_TIMESTAMP: timestamp,
    });
    const results = await Promise.all([
      runBackupAsync(environmentFile.file, backupDirectory, environment),
      runBackupAsync(environmentFile.file, backupDirectory, environment),
    ]);

    assert.equal(results.filter((result) => result.status === 0).length, 1);
    assert.equal(results.filter((result) => result.status !== 0).length, 1);
    assert.equal(listBackups(backupDirectory).length, 1);
    assert.deepEqual(readdirSync(backupDirectory).filter((name) => name.endsWith(".partial")), []);
    assert.deepEqual(readdirSync(backupDirectory).filter((name) => name.endsWith(".lock")), []);
    assert.doesNotMatch(
      results.map((result) => `${result.stdout}${result.stderr}`).join("\n"),
      new RegExp(fixtureSecrets.join("|")),
    );

    const encrypted = readFileSync(
      join(backupDirectory, `jyotisha-staging-${timestamp}.dump.enc`),
    );
    const decrypted = spawnSync(
      "openssl",
      ["enc", "-d", "-aes-256-cbc", "-pbkdf2", "-pass", "env:STAGING_BACKUP_ENCRYPTION_KEY"],
      {
        input: encrypted,
        env: { ...process.env, STAGING_BACKUP_ENCRYPTION_KEY: "staging-backup-test-password" },
      },
    );
    assert.equal(decrypted.status, 0, decrypted.stderr.toString());
    assert.equal(decrypted.stdout.toString(), "same-second dump payload");
  } finally {
    rmSync(environmentFile.directory, { force: true, recursive: true });
    rmSync(backupDirectory, { force: true, recursive: true });
    rmSync(commandDirectory, { force: true, recursive: true });
  }
});

test("find enumeration failures preserve existing backups and do not report completion", () => {
  const environmentFile = createDatabaseEnvironment();
  const backupDirectory = canonicalTemporaryDirectory("jyotisha-backup-enumeration-");
  const commandDirectory = mkdtempSync(join(tmpdir(), "jyotisha-backup-enumeration-command-"));
  const existingBackups = [
    "jyotisha-staging-20260720T030101Z.dump.enc",
    "jyotisha-staging-20260720T030102Z.dump.enc",
    "jyotisha-staging-20260720T030103Z.dump.enc",
  ];

  try {
    for (const backup of existingBackups) {
      writeFileSync(join(backupDirectory, backup), backup, { mode: 0o600 });
    }
    writeFileSync(join(backupDirectory, "unrelated.txt"), "retain me");
    safeDiskCommand(commandDirectory);
    writeCommand(commandDirectory, "docker", "printf '%s' 'enumeration dump payload'");
    writeCommand(commandDirectory, "find", "exit 91");
    const result = runBackup(
      environmentFile.file,
      backupDirectory,
      backupEnvironment(commandDirectory, {
        BACKUP_TIMESTAMP: "20260720T030104Z",
      }),
    );

    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /failed to enumerate completed backups/);
    assert.doesNotMatch(result.stdout, /path=/);
    for (const backup of existingBackups) {
      assert.equal(readFileSync(join(backupDirectory, backup), "utf8"), backup);
    }
    assert.equal(readFileSync(join(backupDirectory, "unrelated.txt"), "utf8"), "retain me");
  } finally {
    rmSync(environmentFile.directory, { force: true, recursive: true });
    rmSync(backupDirectory, { force: true, recursive: true });
    rmSync(commandDirectory, { force: true, recursive: true });
  }
});

test("refuses full disks and removes a failed-pipeline partial file", () => {
  const environmentFile = createDatabaseEnvironment();
  const backupDirectory = canonicalTemporaryDirectory("jyotisha-backup-failure-");
  const fullDiskCommands = mkdtempSync(join(tmpdir(), "jyotisha-backup-full-disk-command-"));
  const pipelineCommands = mkdtempSync(join(tmpdir(), "jyotisha-backup-pipeline-command-"));

  try {
    safeDiskCommand(fullDiskCommands, 70);
    const fullDisk = runBackup(
      environmentFile.file,
      backupDirectory,
      backupEnvironment(fullDiskCommands, { BACKUP_TIMESTAMP: "20260720T040101Z" }),
    );
    assert.notEqual(fullDisk.status, 0);
    assert.match(fullDisk.stderr, /disk usage must be below 70 percent/);
    assert.deepEqual(listBackups(backupDirectory), []);

    safeDiskCommand(pipelineCommands);
    writeCommand(pipelineCommands, "docker", "exit 92");
    const failedPipeline = runBackup(
      environmentFile.file,
      backupDirectory,
      backupEnvironment(pipelineCommands, { BACKUP_TIMESTAMP: "20260720T040102Z" }),
    );
    assert.notEqual(failedPipeline.status, 0);
    assert.deepEqual(listBackups(backupDirectory), []);
    assert.deepEqual(readdirSync(backupDirectory).filter((name) => name.endsWith(".partial")), []);
    assert.deepEqual(readdirSync(backupDirectory).filter((name) => name.endsWith(".lock")), []);
  } finally {
    rmSync(environmentFile.directory, { force: true, recursive: true });
    rmSync(backupDirectory, { force: true, recursive: true });
    rmSync(fullDiskCommands, { force: true, recursive: true });
    rmSync(pipelineCommands, { force: true, recursive: true });
  }
});
