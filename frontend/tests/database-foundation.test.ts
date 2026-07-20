import assert from "node:assert/strict";
import { spawnSync, type SpawnSyncReturns } from "node:child_process";
import {
  appendFileSync,
  copyFileSync,
  mkdtempSync,
  mkdirSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { readDatabaseUrl } from "../src/lib/db/config";
import { startPostgresFixture } from "./helpers/postgres-fixture";

const migrationFilename = "20260720000100_backend_foundation.sql";
const pendingFilename = "20260720000200_pending_check.sql";
const runnerPath = fileURLToPath(
  new URL("../scripts/db-migrate.mjs", import.meta.url),
);
const migrationPath = fileURLToPath(
  new URL(`../db/migrations/${migrationFilename}`, import.meta.url),
);
const fixturePasswords = [
  "schema-owner-test-password",
  "identity-runtime-test-password",
  "app-runtime-test-password",
  "admin-runtime-test-password",
  "migration-runner-test-password",
  "backup-reader-test-password",
  "postgres-test-password",
];

function runMigration(
  connectionString: string,
  options: { check?: boolean; migrationsDirectory?: string } = {},
): SpawnSyncReturns<string> {
  return spawnSync(
    process.execPath,
    [runnerPath, ...(options.check ? ["--check"] : [])],
    {
      encoding: "utf8",
      env: {
        SCHEMA_DATABASE_URL: connectionString,
        ...(options.migrationsDirectory
          ? { MIGRATIONS_DIRECTORY: options.migrationsDirectory }
          : {}),
      } as NodeJS.ProcessEnv,
    },
  );
}

function assertSafeOutput(result: SpawnSyncReturns<string>): void {
  const output = `${result.stdout}${result.stderr}`;
  for (const password of fixturePasswords) {
    assert.doesNotMatch(output, new RegExp(password));
  }
}

test("readDatabaseUrl requires APP_DATABASE_URL", () => {
  assert.throws(
    () => readDatabaseUrl({} as NodeJS.ProcessEnv, "APP_DATABASE_URL"),
    new Error("APP_DATABASE_URL is required"),
  );
});

test("migration runner applies once, detects drift, and checks read-only", () => {
  const fixture = startPostgresFixture();
  const temporaryDirectory = mkdtempSync(join(tmpdir(), "jyotisha-migrations-"));
  const copiedMigration = join(temporaryDirectory, migrationFilename);
  const schemaUrl = fixture.connectionUrl(
    "schema_owner",
    "schema-owner-test-password",
  );
  const results: SpawnSyncReturns<string>[] = [];

  try {
    copyFileSync(migrationPath, copiedMigration);

    const missingLedgerCheck = runMigration(schemaUrl, {
      check: true,
      migrationsDirectory: temporaryDirectory,
    });
    results.push(missingLedgerCheck);
    assert.equal(missingLedgerCheck.status, 3);
    assert.equal(missingLedgerCheck.stdout.trim(), migrationFilename);
    assert.equal(
      fixture.psql(
        "select exists (select from pg_namespace where nspname = 'migration')",
      ),
      "f",
    );

    const firstRun = runMigration(schemaUrl);
    results.push(firstRun);
    assert.equal(firstRun.status, 0, firstRun.stderr);
    assert.match(firstRun.stdout, new RegExp(`applied ${migrationFilename}`));

    const ledgerRow = fixture.psql(`
      select filename || ':' || checksum || ':' || applied_at
      from migration.schema_migrations
    `);
    const [filename, checksum] = ledgerRow.split(":");
    assert.equal(filename, migrationFilename);
    assert.equal(checksum.length, 64);

    const secondRun = runMigration(schemaUrl);
    results.push(secondRun);
    assert.equal(secondRun.status, 0, secondRun.stderr);
    assert.match(
      secondRun.stdout,
      new RegExp(`already applied ${migrationFilename}`),
    );
    assert.equal(
      fixture.psql(`
        select filename || ':' || checksum || ':' || applied_at
        from migration.schema_migrations
      `),
      ledgerRow,
    );

    const currentCheck = runMigration(schemaUrl, { check: true });
    results.push(currentCheck);
    assert.equal(currentCheck.status, 0, currentCheck.stderr);

    const emptyDirectory = join(temporaryDirectory, "empty");
    mkdirSync(emptyDirectory);
    const missingFileCheck = runMigration(schemaUrl, {
      check: true,
      migrationsDirectory: emptyDirectory,
    });
    results.push(missingFileCheck);
    assert.equal(missingFileCheck.status, 1);
    assert.match(
      missingFileCheck.stderr,
      new RegExp(`migration file missing: ${migrationFilename}`),
    );

    const pendingPath = join(temporaryDirectory, pendingFilename);
    mkdirSync(dirname(pendingPath), { recursive: true });
    writeFileSync(pendingPath, "create schema check_mode_side_effect;\n");
    const ledgerCountBeforeCheck = fixture.psql(
      "select count(*) from migration.schema_migrations",
    );
    const pendingCheck = runMigration(schemaUrl, {
      check: true,
      migrationsDirectory: temporaryDirectory,
    });
    results.push(pendingCheck);
    assert.equal(pendingCheck.status, 3, pendingCheck.stderr);
    assert.equal(pendingCheck.stdout.trim(), pendingFilename);
    assert.equal(
      fixture.psql("select count(*) from migration.schema_migrations"),
      ledgerCountBeforeCheck,
    );
    assert.equal(
      fixture.psql(
        "select exists (select from pg_namespace where nspname = 'check_mode_side_effect')",
      ),
      "f",
    );

    appendFileSync(copiedMigration, " ");
    const driftCheck = runMigration(schemaUrl, {
      check: true,
      migrationsDirectory: temporaryDirectory,
    });
    results.push(driftCheck);
    assert.equal(driftCheck.status, 1);
    assert.match(
      driftCheck.stderr,
      new RegExp(`migration checksum mismatch: ${migrationFilename}`),
    );

    const driftRun = runMigration(schemaUrl, {
      migrationsDirectory: temporaryDirectory,
    });
    results.push(driftRun);
    assert.equal(driftRun.status, 1);
    assert.match(
      driftRun.stderr,
      new RegExp(`migration checksum mismatch: ${migrationFilename}`),
    );

    assert.equal(
      fixture.psql(
        "select has_database_privilege('app_runtime', current_database(), 'create')",
      ),
      "f",
    );
    assert.equal(
      fixture.psql(
        "select has_table_privilege('app_runtime', 'migration.schema_migrations', 'select')",
      ),
      "f",
    );

    for (const result of results) assertSafeOutput(result);
  } finally {
    fixture.stop();
    rmSync(temporaryDirectory, { force: true, recursive: true });
  }
});
