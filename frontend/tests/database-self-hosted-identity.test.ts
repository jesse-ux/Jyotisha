import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import test from "node:test";

import { startPostgresFixture } from "./helpers/postgres-fixture.ts";

const runnerPath = fileURLToPath(
  new URL("../scripts/db-migrate.mjs", import.meta.url),
);
const migrationsDirectory = fileURLToPath(
  new URL("../db/migrations", import.meta.url),
);
const identityMigration = fileURLToPath(
  new URL(
    "../db/migrations/20260721000100_self_hosted_identity.sql",
    import.meta.url,
  ),
);

test("self-hosted identity migration creates Better Auth tables with least privilege", () => {
  const migrationSource = readFileSync(identityMigration, "utf8");
  assert.doesNotMatch(migrationSource, /grant all/i);

  const fixture = startPostgresFixture();
  const schemaUrl = fixture.connectionUrl(
    "schema_owner",
    "schema-owner-test-password",
  );
  const migrate = () =>
    spawnSync(process.execPath, [runnerPath], {
      encoding: "utf8",
      env: {
        ...process.env,
        MIGRATIONS_DIRECTORY: migrationsDirectory,
        SCHEMA_DATABASE_URL: schemaUrl,
      },
    });

  try {
    const firstRun = migrate();
    assert.equal(firstRun.status, 0, firstRun.stderr);
    assert.match(
      firstRun.stdout,
      /applied 20260721000100_self_hosted_identity\.sql/,
    );

    const secondRun = migrate();
    assert.equal(secondRun.status, 0, secondRun.stderr);
    assert.match(
      secondRun.stdout,
      /already applied 20260721000100_self_hosted_identity\.sql/,
    );

    assert.equal(
      fixture.psql(`
        select string_agg(tablename, ',' order by tablename)
        from pg_tables
        where schemaname = 'identity'
      `),
      "accounts,otp_rate_limits,sessions,users,verifications",
    );
    assert.equal(
      fixture.psql(`
        select string_agg(tablename || ':' || tableowner, ',' order by tablename)
        from pg_tables
        where schemaname = 'identity'
      `),
      [
        "accounts:schema_owner",
        "otp_rate_limits:schema_owner",
        "sessions:schema_owner",
        "users:schema_owner",
        "verifications:schema_owner",
      ].join(","),
    );

    assert.equal(
      fixture.psql(`
        select data_type || ':' || coalesce(column_default, '')
        from information_schema.columns
        where table_schema = 'identity'
          and table_name = 'users'
          and column_name = 'id'
      `),
      "uuid:gen_random_uuid()",
    );
    assert.equal(
      fixture.psql(`
        select is_nullable || ':' || data_type
        from information_schema.columns
        where table_schema = 'identity'
          and table_name = 'users'
          and column_name = 'email_verified'
      `),
      "NO:boolean",
    );

    for (const table of [
      "users",
      "sessions",
      "accounts",
      "verifications",
      "otp_rate_limits",
    ]) {
      assert.equal(
        fixture.psql(
          `select has_table_privilege('identity_runtime', 'identity.${table}', 'select,insert,update,delete')`,
        ),
        "t",
      );
      assert.equal(
        fixture.psql(
          `select has_table_privilege('app_runtime', 'identity.${table}', 'select')`,
        ),
        "f",
      );
      assert.equal(
        fixture.psql(
          `select has_table_privilege('admin_runtime', 'identity.${table}', 'select')`,
        ),
        "t",
      );
    }

    fixture.psqlAs(
      "identity_runtime",
      "identity-runtime-test-password",
      `
        insert into identity.users (name, email)
        values ('Migration User', 'migration@example.com')
      `,
    );
    const userId = fixture.psql(
      "select id from identity.users where email = 'migration@example.com'",
    );
    assert.match(userId, /^[0-9a-f-]{36}$/);

    fixture.psqlAs(
      "identity_runtime",
      "identity-runtime-test-password",
      `
        insert into identity.sessions (token, user_id, expires_at)
        values ('opaque-session-token', '${userId}', now() + interval '1 hour')
      `,
    );
    fixture.psqlAs(
      "identity_runtime",
      "identity-runtime-test-password",
      `delete from identity.users where id = '${userId}'`,
    );
    assert.equal(fixture.psql("select count(*) from identity.sessions"), "0");

    fixture.psqlAs(
      "identity_runtime",
      "identity-runtime-test-password",
      "insert into identity.users (name, email) values ('One', 'Case@Example.com')",
    );
    assert.throws(() =>
      fixture.psqlAs(
        "identity_runtime",
        "identity-runtime-test-password",
        "insert into identity.users (name, email) values ('Two', 'case@example.com')",
      ),
    );
    assert.throws(() =>
      fixture.psqlAs(
        "app_runtime",
        "app-runtime-test-password",
        "select count(*) from identity.users",
      ),
    );
    assert.equal(
      fixture.psqlAs(
        "admin_runtime",
        "admin-runtime-test-password",
        "select count(*) from identity.users",
      ),
      "1",
    );
  } finally {
    fixture.stop();
  }
});
