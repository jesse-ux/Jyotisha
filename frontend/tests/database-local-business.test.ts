import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";

import { createLocalPostgresDataClient } from "../src/lib/db/local-postgres-client-core.ts";
import { startPostgresFixture } from "./helpers/postgres-fixture.ts";

const runnerPath = fileURLToPath(
  new URL("../scripts/db-migrate.mjs", import.meta.url),
);

test("local PostgreSQL applies the reviewed business schema and serves authenticated business calls", async () => {
  const fixture = startPostgresFixture();
  const schemaUrl = fixture.connectionUrl(
    "schema_owner",
    "schema-owner-test-password",
  );

  try {
    const migration = spawnSync(process.execPath, [runnerPath], {
      encoding: "utf8",
      env: {
        ...process.env,
        SCHEMA_DATABASE_URL: schemaUrl,
      },
    });
    assert.equal(migration.status, 0, migration.stderr);
    assert.match(migration.stdout, /applied 20260715000000_account_credits\.sql/);
    assert.match(migration.stdout, /applied 20260721150000_align_conversational_finance_domain\.sql/);
    assert.match(migration.stdout, /applied 20260723010000_restore_conversational_message_history\.sql/);
    assert.match(migration.stdout, /applied 20260723020000_mark_captured_conversational_messages\.sql/);
    assert.match(migration.stdout, /applied 20260728010000_conversational_event_semantics\.sql/);
    assert.match(migration.stdout, /applied 20260728020000_rectification_agent_v5\.sql/);

    assert.equal(
      fixture.psql(`
        select is_nullable || ':' || data_type
        from information_schema.columns
        where table_schema = 'public'
          and table_name = 'birth_time_rectification_turns'
          and column_name = 'user_message'
      `),
      "YES:text",
    );
    assert.equal(
      fixture.psql(`
        select is_nullable || ':' || data_type || ':' || column_default
        from information_schema.columns
        where table_schema = 'public'
          and table_name = 'birth_time_rectification_turns'
          and column_name = 'user_message_captured'
      `),
      "NO:boolean:f",
    );
    assert.equal(
      fixture.psql(`
        select
          has_function_privilege(
            'service_role',
            'public.load_conversational_rectification_case_with_history(uuid, uuid)',
            'execute'
          ) || ':' ||
          has_function_privilege(
            'authenticated',
            'public.load_conversational_rectification_case_with_history(uuid, uuid)',
            'execute'
          )
      `),
      "true:f",
    );

    assert.equal(
      fixture.psql(`
        select string_agg(tablename, ',' order by tablename)
        from pg_tables
        where schemaname = 'public'
      `),
      [
        "birth_time_rectification_action_receipts",
        "birth_time_rectification_agent_runs",
        "birth_time_rectification_billing",
        "birth_time_rectification_candidate_feature_snapshots",
        "birth_time_rectification_cases",
        "birth_time_rectification_diagnostics",
        "birth_time_rectification_dynamic_state",
        "birth_time_rectification_event_evidence",
        "birth_time_rectification_handoff_attach_receipts",
        "birth_time_rectification_handoff_settlements",
        "birth_time_rectification_pending_evidence",
        "birth_time_rectification_public_messages",
        "birth_time_rectification_question_handoffs",
        "birth_time_rectification_scoring_jobs",
        "birth_time_rectification_turns",
        "birth_time_rectification_v4_actions",
        "birth_time_rectification_v4_candidate_snapshots",
        "birth_time_rectification_v4_cases",
        "birth_time_rectification_v4_event_revisions",
        "birth_time_rectification_v4_events",
        "birth_time_rectification_v4_handoff_attach_receipts",
        "birth_time_rectification_v4_handoff_settlements",
        "birth_time_rectification_v4_handoffs",
        "birth_time_rectification_v4_jobs",
        "birth_time_rectification_v4_turns",
        "chart_profiles",
        "chat_sessions",
        "consultation_requests",
        "credit_request_cancellations",
        "credit_transactions",
        "profiles",
        "redemption_codes",
        "synastry_reports",
      ].join(","),
    );

    fixture.psqlAs(
      "identity_runtime",
      "identity-runtime-test-password",
      `
        insert into identity.users (name, email, email_verified, email_verified_at)
        values ('Local User', 'local-user@example.com', true, now())
      `,
    );
    const userId = fixture.psql(
      "select id from identity.users where email = 'local-user@example.com'",
    );
    assert.equal(
      fixture.psql(`select email from auth.users where id = '${userId}'`),
      "local-user@example.com",
    );
    assert.equal(
      fixture.psql(`select email || ':' || credits from public.profiles where id = '${userId}'`),
      "local-user@example.com:0",
    );
    assert.equal(
      fixture.psqlAs(
        "app_runtime",
        "app-runtime-test-password",
        `set role authenticated;
         select set_config('request.jwt.claim.sub', '${userId}', true);
         select email from public.profiles where id = '${userId}'`,
      ),
      `SET\n${userId}\nlocal-user@example.com`,
    );

    const local = createLocalPostgresDataClient(
      fixture.connectionUrl("app_runtime", "app-runtime-test-password"),
      { id: userId, email: "local-user@example.com" },
    );
    const profile = await local.from("profiles")
      .select("id,email,credits")
      .eq("id", userId)
      .single();
    assert.equal(profile.error, null);
    assert.deepEqual(profile.data, {
      id: userId,
      email: "local-user@example.com",
      credits: 0,
    });
    const nonAbandonedProfiles = await local.from("profiles")
      .select("id")
      .neq("email", "not-local-user@example.com")
      .single();
    assert.equal(nonAbandonedProfiles.error, null);
    assert.deepEqual(nonAbandonedProfiles.data, { id: userId });
    const admin = createLocalPostgresDataClient(
      fixture.connectionUrl("admin_runtime", "admin-runtime-test-password"),
      null,
      "service_role",
    );
    const adminProfile = await admin.from("profiles")
      .select("id")
      .eq("id", userId)
      .single();
    assert.equal(adminProfile.error, null);
    assert.deepEqual(adminProfile.data, { id: userId });

    const sessionId = "11111111-1111-4111-8111-111111111111";
    const inserted = await local.from("chat_sessions").insert({
      id: sessionId,
      user_id: userId,
      title: "Local conversation",
      theme: "general",
      model_id: "test-model",
      messages: [],
      session_type: "consultation",
      rectification_case_id: null,
      updated_at: new Date().toISOString(),
    }).select("id").single();
    assert.equal(inserted.error, null);
    assert.deepEqual(inserted.data, { id: sessionId });

    fixture.psql(`
      insert into public.redemption_codes (code_hash, code_mask, credits)
      values ('${"a".repeat(64)}', 'JYOTISH-****-TEST', 3)
    `);
    const redeemed = await local.rpc("redeem_code", {
      p_code_hash: "a".repeat(64),
    });
    assert.equal(redeemed.error, null);
    assert.deepEqual(redeemed.data, [{ success: true, credits: 3, error_code: null }]);
  } finally {
    fixture.stop();
  }
});
