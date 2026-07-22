import { createHash } from "node:crypto";
import { readFile, readdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import pg from "pg";

const { Client } = pg;
const migrationFilenamePattern = /^\d{14}_[a-z0-9_]+\.sql$/;

class SafeMigrationError extends Error {}

async function loadMigrationFiles(migrationsDirectories) {
  const directories = Array.isArray(migrationsDirectories)
    ? migrationsDirectories
    : [migrationsDirectories];
  const entriesByDirectory = [];
  for (const migrationsDirectory of directories) {
    try {
      entriesByDirectory.push({
        migrationsDirectory,
        entries: await readdir(migrationsDirectory, { withFileTypes: true }),
      });
    } catch {
      throw new SafeMigrationError("unable to read migrations directory");
    }
  }

  const malformedSqlEntry = entriesByDirectory
    .flatMap(({ entries }) => entries)
    .find(
      (entry) =>
        entry.isFile() &&
        entry.name.endsWith(".sql") &&
        !migrationFilenamePattern.test(entry.name),
    );
  if (malformedSqlEntry) {
    throw new SafeMigrationError(
      `invalid migration filename: ${malformedSqlEntry.name}`,
    );
  }

  const migrationEntries = entriesByDirectory.flatMap(
    ({ migrationsDirectory, entries }) =>
      entries
        .filter(
          (entry) => entry.isFile() && migrationFilenamePattern.test(entry.name),
        )
        .map((entry) => ({ migrationsDirectory, filename: entry.name })),
  );
  const duplicate = migrationEntries.find(
    (entry, index) =>
      migrationEntries.findIndex((candidate) => candidate.filename === entry.filename) !== index,
  );
  if (duplicate) {
    throw new SafeMigrationError(`duplicate migration filename: ${duplicate.filename}`);
  }

  return Promise.all(
    migrationEntries
      .sort((left, right) => left.filename.localeCompare(right.filename))
      .map(async ({ migrationsDirectory, filename }) => {
        const bytes = await readFile(resolve(migrationsDirectory, filename));
        return {
          filename,
          bytes,
          checksum: createHash("sha256").update(bytes).digest("hex"),
        };
      }),
  );
}

async function readLedger(client) {
  const ledgerResult = await client.query(
    "select to_regclass('migration.schema_migrations') as ledger",
  );
  if (ledgerResult.rows[0]?.ledger === null) return new Map();

  const result = await client.query(
    "select filename, checksum from migration.schema_migrations",
  );
  return new Map(result.rows.map((row) => [row.filename, row.checksum]));
}

function assertLedgerFilesPresent(ledger, files) {
  const reviewedFilenames = new Set(files.map((file) => file.filename));
  for (const filename of ledger.keys()) {
    if (!reviewedFilenames.has(filename)) {
      if (!migrationFilenamePattern.test(filename)) {
        throw new SafeMigrationError(
          "migration ledger contains an invalid filename",
        );
      }
      throw new SafeMigrationError(`migration file missing: ${filename}`);
    }
  }
}

export async function runMigrations({
  connectionString,
  migrationsDirectory,
  migrationsDirectories,
  logger = console,
  check = false,
}) {
  const files = await loadMigrationFiles(migrationsDirectories ?? migrationsDirectory);
  const client = new Client({ connectionString });
  let locked = false;

  try {
    await client.connect();
    await client.query(
      "select pg_advisory_lock(hashtext('jyotisha_schema_migrations'))",
    );
    locked = true;

    if (check) {
      const ledger = await readLedger(client);
      const pending = [];
      assertLedgerFilesPresent(ledger, files);

      for (const file of files) {
        const recordedChecksum = ledger.get(file.filename);
        if (recordedChecksum === undefined) {
          pending.push(file.filename);
        } else if (recordedChecksum !== file.checksum) {
          throw new SafeMigrationError(
            `migration checksum mismatch: ${file.filename}`,
          );
        }
      }

      for (const filename of pending) logger.log(filename);
      return pending.length === 0 ? 0 : 3;
    }

    await client.query(
      "create schema if not exists migration authorization schema_owner",
    );
    await client.query("revoke all on schema migration from public");
    await client.query(`
      create table if not exists migration.schema_migrations (
        filename text primary key,
        checksum text not null check (length(checksum) = 64),
        applied_at timestamptz not null default now()
      )
    `);
    await client.query(
      "revoke all on table migration.schema_migrations from public",
    );

    const ledger = await readLedger(client);
    assertLedgerFilesPresent(ledger, files);
    for (const file of files) {
      const recordedChecksum = ledger.get(file.filename);
      if (recordedChecksum !== undefined) {
        if (recordedChecksum !== file.checksum) {
          throw new SafeMigrationError(
            `migration checksum mismatch: ${file.filename}`,
          );
        }
        logger.log(`already applied ${file.filename}`);
        continue;
      }

      await client.query("begin");
      try {
        await client.query(file.bytes.toString("utf8"));
        await client.query(
          "insert into migration.schema_migrations (filename, checksum) values ($1, $2)",
          [file.filename, file.checksum],
        );
        await client.query("commit");
      } catch {
        await client.query("rollback");
        throw new SafeMigrationError(`migration failed: ${file.filename}`);
      }
      logger.log(`applied ${file.filename}`);
    }

    return 0;
  } finally {
    if (locked) {
      try {
        await client.query(
          "select pg_advisory_unlock(hashtext('jyotisha_schema_migrations'))",
        );
      } catch {
        // The connection may already be unusable; closing it still releases the lock.
      }
    }
    await client.end().catch(() => {});
  }
}

function requireSchemaDatabaseUrl(env) {
  const value = env.SCHEMA_DATABASE_URL?.trim();
  if (!value) throw new SafeMigrationError("SCHEMA_DATABASE_URL is required");
  if (!value.startsWith("postgresql://")) {
    throw new SafeMigrationError("SCHEMA_DATABASE_URL must be a PostgreSQL URL");
  }
  return value;
}

function safeErrorMessage(error) {
  return error instanceof SafeMigrationError
    ? error.message
    : "database migration failed";
}

const invokedPath = process.argv[1]
  ? pathToFileURL(resolve(process.argv[1])).href
  : undefined;

if (invokedPath === import.meta.url) {
  const defaultDirectory = resolve(
    dirname(fileURLToPath(import.meta.url)),
    "../db/migrations",
  );
  const supabaseCompatibilityDirectory = resolve(
    dirname(fileURLToPath(import.meta.url)),
    "../supabase/migrations",
  );
  try {
    const status = await runMigrations({
      connectionString: requireSchemaDatabaseUrl(process.env),
      ...(process.env.MIGRATIONS_DIRECTORY?.trim()
        ? { migrationsDirectory: process.env.MIGRATIONS_DIRECTORY.trim() }
        : {
            migrationsDirectories: [
              defaultDirectory,
              supabaseCompatibilityDirectory,
            ],
          }),
      check: process.argv.slice(2).includes("--check"),
    });
    process.exitCode = status;
  } catch (error) {
    console.error(safeErrorMessage(error));
    process.exitCode = 1;
  }
}
