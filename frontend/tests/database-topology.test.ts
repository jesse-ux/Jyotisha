import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { startPostgresFixture } from "./helpers/postgres-fixture";

test("staging postgres is private and CI binds loopback only", () => {
  const staging = readFileSync("../deploy/docker-compose.postgres.yml", "utf8");
  const ci = readFileSync("../deploy/docker-compose.postgres-ci.yml", "utf8");
  assert.match(staging, /image:\s*postgres:17-alpine/);
  assert.doesNotMatch(staging, /^\s+ports:/m);
  assert.match(ci, /127\.0\.0\.1:\$\{POSTGRES_HOST_PORT:-55432\}:5432/);
});

test("database roles have no cluster privileges", () => {
  const fixture = startPostgresFixture();
  try {
    assert.equal(
      fixture.psql(`
        select rolname || ':' || rolsuper || ':' || rolcreatedb || ':' ||
               rolcreaterole || ':' || rolbypassrls
        from pg_roles
        where rolname in ('schema_owner','identity_runtime','app_runtime',
          'admin_runtime','migration_runner','backup_reader')
        order by rolname
      `),
      [
        "admin_runtime:f:f:f:f",
        "app_runtime:f:f:f:f",
        "backup_reader:f:f:f:f",
        "identity_runtime:f:f:f:f",
        "migration_runner:f:f:f:f",
        "schema_owner:f:f:f:f",
      ].join("\n"),
    );
  } finally {
    fixture.stop();
  }
});
