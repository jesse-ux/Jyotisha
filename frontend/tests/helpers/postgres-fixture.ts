import { execFileSync, spawnSync } from "node:child_process";
import {
  chmodSync,
  mkdirSync,
  mkdtempSync,
  rmSync,
  writeFileSync,
} from "node:fs";
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

type PortReservation = { port: number; directory: string };

function reserveAvailablePort(): PortReservation {
  for (let port = 55432; port <= 55531; port += 1) {
    const directory = join(tmpdir(), `jyotisha-postgres-port-${port}.lock`);
    try {
      mkdirSync(directory);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "EEXIST") continue;
      throw error;
    }

    if (isPortAvailable(port)) {
      return { port, directory };
    }
    rmSync(directory, { force: true, recursive: true });
  }

  throw new Error("no available PostgreSQL test port in 55432..55531");
}

function releasePort(reservation: PortReservation): void {
  rmSync(reservation.directory, { force: true, recursive: true });
}

export function startPostgresFixture(): PostgresFixture {
  const projectName = `jyotisha-postgres-${process.pid}-${Date.now()}`;
  const temporaryDirectory = mkdtempSync(join(tmpdir(), "jyotisha-postgres-"));
  const databaseEnvFile = join(temporaryDirectory, "database.env");
  let portReservation: PortReservation;
  try {
    portReservation = reserveAvailablePort();
  } catch (error) {
    rmSync(temporaryDirectory, { force: true, recursive: true });
    throw error;
  }
  const hostPort = portReservation.port;
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

  try {
    writeFileSync(databaseEnvFile, databaseEnvironment, { mode: 0o600 });
    chmodSync(databaseEnvFile, 0o600);
    execFileSync(
      "docker",
      [...composeArguments, "up", "-d", "--wait", "postgres"],
      { env: environment, stdio: "inherit" },
    );
  } catch (error) {
    try {
      try {
        execFileSync(
          "docker",
          [...composeArguments, "down", "-v", "--remove-orphans"],
          { env: environment, stdio: "inherit" },
        );
      } catch {
        // Preserve the original startup failure.
      }
    } finally {
      releasePort(portReservation);
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
        releasePort(portReservation);
        rmSync(temporaryDirectory, { force: true, recursive: true });
      }
    },
  };
}
