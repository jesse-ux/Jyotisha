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
               rolcreaterole || ':' || rolbypassrls || ':' ||
               rolreplication || ':' || rolinherit
        from pg_roles
        where rolname in ('schema_owner','identity_runtime','app_runtime',
          'admin_runtime','migration_runner','backup_reader')
        order by rolname
      `),
      [
        "admin_runtime:f:f:f:f:f:f",
        "app_runtime:f:f:f:f:f:f",
        "backup_reader:f:f:f:f:f:f",
        "identity_runtime:f:f:f:f:f:f",
        "migration_runner:f:f:f:f:f:f",
        "schema_owner:f:f:f:f:f:f",
      ].join("\n"),
    );
    assert.equal(
      fixture.psql(`
        select rolcanlogin || ':' || rolbypassrls
        from pg_roles
        where rolname = 'service_role'
      `),
      "f:true",
    );
    assert.equal(
      fixture.psql(
        "select nspowner::regrole::text from pg_namespace where nspname = 'public'",
      ),
      "schema_owner",
    );
    assert.equal(
      fixture.psql(`
        select has_schema_privilege('schema_owner', 'public', 'create')
          and has_schema_privilege('schema_owner', 'public', 'usage')
      `),
      "t",
    );
    assert.equal(
      fixture.psql(`
        select coalesce(string_agg(privilege_type, ',' order by privilege_type), '')
        from pg_namespace,
          aclexplode(coalesce(nspacl, acldefault('n', nspowner)))
        where nspname = 'public'
          and grantee = 0
          and privilege_type in ('CREATE', 'USAGE')
      `),
      "",
    );
    assert.equal(
      fixture.psql(`
        select pg_get_userbyid(datdba)
        from pg_database
        where datname = current_database()
      `),
      "postgres",
    );
  } finally {
    fixture.stop();
  }
});
