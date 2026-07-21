import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import {
  appendFileSync,
  copyFileSync,
  mkdtempSync,
  mkdirSync,
  rmSync,
  unlinkSync,
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
const concurrentFilename = "20260720000300_concurrent_lock.sql";
const failingFilename = "20260720000400_atomic_rollback.sql";
const malformedFilename = "20260720_malformed.sql";
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

type MigrationResult = {
  status: number | null;
  stdout: string;
  stderr: string;
};

function migrationInvocation(
  connectionString: string,
  options: { check?: boolean; migrationsDirectory?: string },
) {
  return {
    arguments: [runnerPath, ...(options.check ? ["--check"] : [])],
    environment: {
      NODE_ENV: process.env.NODE_ENV,
      SCHEMA_DATABASE_URL: connectionString,
      ...(options.migrationsDirectory
        ? { MIGRATIONS_DIRECTORY: options.migrationsDirectory }
        : {}),
    },
  };
}

function runMigration(
  connectionString: string,
  options: { check?: boolean; migrationsDirectory?: string } = {},
): MigrationResult {
  const invocation = migrationInvocation(connectionString, options);
  const result = spawnSync(
    process.execPath,
    invocation.arguments,
    {
      encoding: "utf8",
      env: invocation.environment,
    },
  );
  return { status: result.status, stdout: result.stdout, stderr: result.stderr };
}

function runMigrationAsync(
  connectionString: string,
  migrationsDirectory: string,
): Promise<MigrationResult> {
  const invocation = migrationInvocation(connectionString, {
    migrationsDirectory,
  });

  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, invocation.arguments, {
      env: invocation.environment,
      stdio: ["ignore", "pipe", "pipe"],
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

function assertSafeOutput(result: MigrationResult): void {
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

test("migration runner is serialized, atomic, drift-safe, and read-only in check mode", async () => {
  const fixture = startPostgresFixture();
  const temporaryDirectory = mkdtempSync(join(tmpdir(), "jyotisha-migrations-"));
  const copiedMigration = join(temporaryDirectory, migrationFilename);
  const schemaUrl = fixture.connectionUrl(
    "schema_owner",
    "schema-owner-test-password",
  );
  const results: MigrationResult[] = [];

  try {
    copyFileSync(migrationPath, copiedMigration);

    const malformedPath = join(temporaryDirectory, malformedFilename);
    writeFileSync(malformedPath, "select 1;\n");
    const malformedCheck = runMigration(schemaUrl, {
      check: true,
      migrationsDirectory: temporaryDirectory,
    });
    results.push(malformedCheck);
    assert.equal(malformedCheck.status, 1);
    assert.match(malformedCheck.stderr, /invalid migration filename/);
    unlinkSync(malformedPath);

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

    const firstRun = runMigration(schemaUrl, {
      migrationsDirectory: temporaryDirectory,
    });
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

    const secondRun = runMigration(schemaUrl, {
      migrationsDirectory: temporaryDirectory,
    });
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

    const currentCheck = runMigration(schemaUrl, {
      check: true,
      migrationsDirectory: temporaryDirectory,
    });
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
    const missingFileApply = runMigration(schemaUrl, {
      migrationsDirectory: emptyDirectory,
    });
    results.push(missingFileApply);
    assert.equal(missingFileApply.status, 1);
    assert.match(
      missingFileApply.stderr,
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
    unlinkSync(pendingPath);

    appendFileSync(copiedMigration, " ");
    const driftRun = runMigration(schemaUrl, {
      migrationsDirectory: temporaryDirectory,
    });
    results.push(driftRun);
    assert.equal(driftRun.status, 1);
    assert.match(
      driftRun.stderr,
      new RegExp(`migration checksum mismatch: ${migrationFilename}`),
    );

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
    copyFileSync(migrationPath, copiedMigration);

    writeFileSync(
      join(temporaryDirectory, concurrentFilename),
      "select pg_sleep(1);\ncreate schema concurrent_lock_probe;\n",
    );
    const concurrentResults = await Promise.all([
      runMigrationAsync(schemaUrl, temporaryDirectory),
      runMigrationAsync(schemaUrl, temporaryDirectory),
    ]);
    results.push(...concurrentResults);
    assert.deepEqual(
      concurrentResults.map((result) => result.status),
      [0, 0],
    );
    assert.deepEqual(
      concurrentResults
        .flatMap((result) => result.stdout.trim().split("\n"))
        .filter((line) => line.endsWith(concurrentFilename))
        .sort(),
      [
        `already applied ${concurrentFilename}`,
        `applied ${concurrentFilename}`,
      ].sort(),
    );
    assert.equal(
      fixture.psql(`
        select count(*)
        from migration.schema_migrations
        where filename = '${concurrentFilename}'
      `),
      "1",
    );

    writeFileSync(
      join(temporaryDirectory, failingFilename),
      `create schema atomic_rollback_probe authorization schema_owner;
create table atomic_rollback_probe.parent (id integer primary key);
create table atomic_rollback_probe.child (
  parent_id integer references atomic_rollback_probe.parent(id)
    deferrable initially deferred
);
insert into atomic_rollback_probe.child (parent_id) values (1);
`,
    );
    const failingRun = runMigration(schemaUrl, {
      migrationsDirectory: temporaryDirectory,
    });
    results.push(failingRun);
    assert.equal(failingRun.status, 1);
    assert.match(
      failingRun.stderr,
      new RegExp(`migration failed: ${failingFilename}`),
    );
    assert.equal(
      fixture.psql(`
        select exists (
          select from pg_namespace where nspname = 'atomic_rollback_probe'
        )
      `),
      "f",
    );
    assert.equal(
      fixture.psql(`
        select count(*)
        from migration.schema_migrations
        where filename = '${failingFilename}'
      `),
      "0",
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

test("foundation grants no direct runtime table DML and exposes only reviewed functions", () => {
  const fixture = startPostgresFixture();
  const temporaryDirectory = mkdtempSync(join(tmpdir(), "jyotisha-privileges-"));
  const schemaUrl = fixture.connectionUrl(
    "schema_owner",
    "schema-owner-test-password",
  );

  try {
    copyFileSync(migrationPath, join(temporaryDirectory, migrationFilename));
    const migration = runMigration(schemaUrl, {
      migrationsDirectory: temporaryDirectory,
    });
    assert.equal(migration.status, 0, migration.stderr);

    fixture.psqlAs(
      "schema_owner",
      "schema-owner-test-password",
      `
        create table public.runtime_boundary_probe (
          id integer primary key,
          value text not null
        );
        create table identity.runtime_boundary_probe (
          id integer primary key,
          value text not null
        );
        create table audit.admin_event_probe (
          value text not null
        );
        create function identity.unreviewed_identity_probe()
        returns text
        language sql
        as 'select ''not callable''::text';
        create function audit.record_admin_event_probe(event_value text)
        returns void
        language sql
        security definer
        set search_path = pg_catalog, audit
        as 'insert into audit.admin_event_probe(value) values (event_value)';
        grant execute on function audit.record_admin_event_probe(text) to admin_runtime;
      `,
    );

    assert.throws(() =>
      fixture.psqlAs(
        "app_runtime",
        "app-runtime-test-password",
        "insert into public.runtime_boundary_probe values (1, 'denied')",
      ),
    );
    assert.throws(() =>
      fixture.psqlAs(
        "admin_runtime",
        "admin-runtime-test-password",
        "insert into audit.admin_event_probe values ('denied')",
      ),
    );
    assert.throws(() =>
      fixture.psqlAs(
        "identity_runtime",
        "identity-runtime-test-password",
        "insert into identity.runtime_boundary_probe values (1, 'denied')",
      ),
    );
    assert.throws(() =>
      fixture.psqlAs(
        "admin_runtime",
        "admin-runtime-test-password",
        "update public.runtime_boundary_probe set value = 'denied'",
      ),
    );
    assert.equal(
      fixture.psql(
        "select has_function_privilege('identity_runtime', 'identity.unreviewed_identity_probe()', 'execute')",
      ),
      "f",
    );
    assert.throws(() =>
      fixture.psqlAs(
        "identity_runtime",
        "identity-runtime-test-password",
        "select identity.unreviewed_identity_probe()",
      ),
    );

    assert.equal(
      fixture.psqlAs(
        "admin_runtime",
        "admin-runtime-test-password",
        "select audit.record_admin_event_probe('approved')",
      ),
      "",
    );
    assert.equal(
      fixture.psql("select value from audit.admin_event_probe"),
      "approved",
    );
  } finally {
    fixture.stop();
    rmSync(temporaryDirectory, { force: true, recursive: true });
  }
});
