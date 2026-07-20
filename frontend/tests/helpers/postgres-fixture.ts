import { execFileSync, spawnSync } from "node:child_process";
import { chmodSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

export type PostgresFixture = {
  projectName: string;
  databaseEnvFile: string;
  hostPort: number;
  connectionUrl(role: string, password: string): string;
  psql(sql: string): string;
  stop(): void;
};

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

function isPortAvailable(port: number): boolean {
  return (
    spawnSync(
      process.execPath,
      [
        "-e",
        `const server = require("node:net").createServer();
server.once("error", () => process.exit(1));
server.listen({ host: "127.0.0.1", port: Number(process.argv[1]) }, () =>
  server.close(() => process.exit(0)),
);`,
        String(port),
      ],
      { stdio: "ignore" },
    ).status === 0
  );
}

function findAvailablePort(): number {
  for (let port = 55432; port <= 55531; port += 1) {
    if (isPortAvailable(port)) {
      return port;
    }
  }

  throw new Error("no available PostgreSQL test port in 55432..55531");
}

export function startPostgresFixture(): PostgresFixture {
  const projectName = `jyotisha-postgres-${process.pid}-${Date.now()}`;
  const temporaryDirectory = mkdtempSync(join(tmpdir(), "jyotisha-postgres-"));
  const databaseEnvFile = join(temporaryDirectory, "database.env");
  const hostPort = findAvailablePort();
  const composeArguments = [
    "compose",
    "--project-name",
    projectName,
    "--env-file",
    databaseEnvFile,
    "-f",
    "../deploy/docker-compose.postgres.yml",
    "-f",
    "../deploy/docker-compose.postgres-ci.yml",
  ];
  const environment = {
    ...process.env,
    DATABASE_ENV_FILE: databaseEnvFile,
    POSTGRES_HOST_PORT: String(hostPort),
  };

  writeFileSync(databaseEnvFile, databaseEnvironment, { mode: 0o600 });
  chmodSync(databaseEnvFile, 0o600);

  try {
    execFileSync(
      "docker",
      [...composeArguments, "up", "-d", "--wait", "postgres"],
      { env: environment, stdio: "inherit" },
    );
  } catch (error) {
    try {
      execFileSync(
        "docker",
        [...composeArguments, "down", "-v", "--remove-orphans"],
        { env: environment, stdio: "inherit" },
      );
    } finally {
      rmSync(temporaryDirectory, { force: true, recursive: true });
    }
    throw error;
  }

  return {
    projectName,
    databaseEnvFile,
    hostPort,
    connectionUrl(role, password) {
      return `postgresql://${role}:${password}@127.0.0.1:${hostPort}/jyotisha`;
    },
    psql(sql) {
      return execFileSync(
        "docker",
        [...composeArguments, "exec", "-T", "postgres", "psql", "-U", "postgres", "-d", "jyotisha", "-Atc", sql],
        { encoding: "utf8", env: environment },
      )
        .trim()
        .replace(/(^|:)false(?=:|$)/gm, "$1f");
    },
    stop() {
      try {
        execFileSync(
          "docker",
          [...composeArguments, "down", "-v", "--remove-orphans"],
          { env: environment, stdio: "inherit" },
        );
      } finally {
        rmSync(temporaryDirectory, { force: true, recursive: true });
      }
    },
  };
}
