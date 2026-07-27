import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";

import { createLocalPostgresDataClient } from "../src/lib/db/local-postgres-client-core.ts";
import { startPostgresFixture } from "./helpers/postgres-fixture.ts";

const runnerPath = fileURLToPath(new URL("../scripts/db-migrate.mjs", import.meta.url));
const actorId = "11111111-1111-4111-8111-111111111111";
const codeId = "22222222-2222-4222-8222-222222222222";

function rpcArgs(requestId: string) {
  return {
    p_actor_user_id: actorId,
    p_actor_email: "admin@example.com",
    p_actor_role: "admin",
    p_request_id: requestId,
  };
}

test("admin code functions reject immutable codes, revoked redemption, and roll back on audit failure", async () => {
  const fixture = startPostgresFixture();
  try {
    const migration = spawnSync(process.execPath, [runnerPath], {
      encoding: "utf8",
      env: {
        ...process.env,
        SCHEMA_DATABASE_URL: fixture.connectionUrl("schema_owner", "schema-owner-test-password"),
      },
    });
    assert.equal(migration.status, 0, migration.stderr);
    assert.match(migration.stdout, /20260727010000_refine_admin_redemption_audit\.sql/);

    fixture.psqlAs("identity_runtime", "identity-runtime-test-password", `
      insert into identity.users (id, name, email, email_verified, email_verified_at, role)
      values ('${actorId}', 'Admin', 'admin@example.com', true, now(), 'admin')
    `);
    const userId = fixture.psql(`select id from identity.users where email = 'admin@example.com'`);
    const admin = createLocalPostgresDataClient(
      fixture.connectionUrl("admin_runtime", "admin-runtime-test-password"),
      null,
      "service_role",
    );

    const created = await admin.rpc("admin_create_redemption_codes", {
      ...rpcArgs("create-1"),
      p_codes: [{
        codeHash: "a".repeat(64),
        codeMask: "JYOTISH-****-AUD1",
        credits: 5,
        expiresAt: null,
        note: "initial",
      }],
    });
    assert.equal(created.error, null);
    assert.equal((created.data as Array<{ code_mask: string }>)[0]?.code_mask, "JYOTISH-****-AUD1");
    assert.equal(fixture.psql("select count(*) from audit.admin_audit_logs"), "1");
    assert.doesNotMatch(fixture.psql("select after_value::text from audit.admin_audit_logs"), /[a-f0-9]{64}/);

    const createdId = fixture.psql("select id from public.redemption_codes where code_mask = 'JYOTISH-****-AUD1'");
    const revoked = await admin.rpc("admin_revoke_redemption_code", {
      ...rpcArgs("revoke-1"),
      p_code_id: createdId,
    });
    assert.equal(revoked.error, null);

    const app = createLocalPostgresDataClient(
      fixture.connectionUrl("app_runtime", "app-runtime-test-password"),
      { id: userId, email: "admin@example.com" },
    );
    const redeemRevoked = await app.rpc("redeem_code", { p_code_hash: "a".repeat(64) });
    assert.deepEqual(redeemRevoked.data, [{ success: false, credits: null, error_code: "revoked_code" }]);

    fixture.psql(`
      insert into public.redemption_codes (id, code_hash, code_mask, credits, redeemed_by, redeemed_email, redeemed_at)
      values ('${codeId}', '${"b".repeat(64)}', 'JYOTISH-****-USED', 3, '${userId}', 'admin@example.com', now())
    `);
    const immutable = await admin.rpc("admin_update_redemption_code", {
      ...rpcArgs("update-used"),
      p_code_id: codeId,
      p_set_note: true,
      p_note: "changed",
      p_set_expires_at: false,
      p_expires_at: null,
    });
    assert.ok(immutable.error);
    assert.equal(fixture.psql(`select note is null from public.redemption_codes where id = '${codeId}'`), "t");

    fixture.psql(`
      create or replace function audit.test_fail_admin_audit()
      returns trigger language plpgsql as $$
      begin
        raise exception 'forced audit failure';
      end;
      $$;
      create trigger test_fail_admin_audit
        before insert on audit.admin_audit_logs
        for each row execute function audit.test_fail_admin_audit()
    `);
    const auditFailure = await admin.rpc("admin_create_redemption_codes", {
      ...rpcArgs("create-audit-failure"),
      p_codes: [{
        codeHash: "c".repeat(64),
        codeMask: "JYOTISH-****-FAIL",
        credits: 7,
        expiresAt: null,
        note: "must rollback",
      }],
    });
    assert.ok(auditFailure.error);
    assert.equal(
      fixture.psql("select count(*) from public.redemption_codes where code_mask = 'JYOTISH-****-FAIL'"),
      "0",
      "audit failure must leave the redemption code unchanged",
    );
    fixture.psql("drop trigger test_fail_admin_audit on audit.admin_audit_logs");
  } finally {
    fixture.stop();
  }
});
