import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";

import { createLocalPostgresDataClient } from "../src/lib/db/local-postgres-client-core.ts";
import { loadLatestAgenticRectificationResult } from "../src/lib/rectification-agentic/session.ts";
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
    assert.match(migration.stdout, /applied 20260804010000_agentic_rectification_candidate_acceptance\.sql/);
    assert.match(migration.stdout, /applied 20260804020000_preserve_reported_birth_time_on_candidate_acceptance\.sql/);

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
        "agentic_rectification_results",
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

    const rectificationSessionId = "22222222-2222-4222-8222-222222222222";
    fixture.psql(`
      update public.profiles
      set birth_date = '1997-08-08',
          reported_birth_time = '05:00',
          birth_time_source = 'family_exact',
          uncertainty_before_minutes = 10,
          uncertainty_after_minutes = 10,
          latitude = 36.420487,
          longitude = 114.209936,
          timezone_offset = 8,
          birth_time_status = 'reported'
      where id = '${userId}';
      insert into public.chat_sessions (id, user_id, title, theme, model_id, messages, session_type, updated_at)
      values ('${rectificationSessionId}', '${userId}', 'Rectification', 'general', 'test-model', '[]', 'birth_time_rectification', now());
      insert into public.agentic_rectification_results (
        id, user_id, session_id, engine_result_id, canonical_input_hash, algorithm_version,
        candidate_range, candidates, overall_confidence, selection_allowed, confirmation_allowed,
        representative_time, baseline_birth_date, baseline_reported_birth_time, baseline_birth_time_source,
        baseline_uncertainty_before_minutes, baseline_uncertainty_after_minutes, baseline_latitude,
        baseline_longitude, baseline_timezone_offset
      ) values (
        '33333333-3333-4333-8333-333333333333', '${userId}', '${rectificationSessionId}',
        'engine-result-1', 'canonical-hash-1', 'test-v1', '{}',
        '[{"rank":1,"time":"04:55","relative_support":60,"tied_minute_count":1},{"rank":2,"time":"05:07","relative_support":40,"tied_minute_count":1}]',
        'medium', true, false, '04:55', '1997-08-08', '05:00', 'family_exact', 10, 10,
        36.420487, 114.209936, 8
      );
    `);
    const latestCandidate = await loadLatestAgenticRectificationResult(
      admin as never,
      userId,
      rectificationSessionId,
    );
    assert.equal(latestCandidate?.resultId, "33333333-3333-4333-8333-333333333333");
    assert.equal(latestCandidate?.selectionAllowed, true);
    assert.deepEqual(latestCandidate?.candidates.map(({ time, relative_support }) => ({ time, relative_support })), [
      { time: "04:55", relative_support: 60 },
      { time: "05:07", relative_support: 40 },
    ]);
    assert.equal(
      fixture.psqlAs(
        "admin_runtime",
        "admin-runtime-test-password",
        `set role service_role;
         select (result ->> 'saved_time') || ':' || (result ->> 'status') || ':' || (result ->> 'idempotent')
         from (
           select public.accept_agentic_rectification_candidate(
             '${userId}', '${rectificationSessionId}', '33333333-3333-4333-8333-333333333333', '04:55'
           ) as result
         ) accepted`,
      ),
      "SET\n04:55:accepted:false",
    );
    assert.equal(
      fixture.psql(`select to_char(active_birth_time, 'HH24:MI') || ':' || birth_time_status || ':' || to_char(reported_birth_time, 'HH24:MI') || ':' || coalesce(to_char(birth_time, 'HH24:MI'), 'null') from public.profiles where id = '${userId}'`),
      "04:55:accepted:05:00:null",
    );
    assert.equal(
      fixture.psqlAs(
        "admin_runtime",
        "admin-runtime-test-password",
        `set role service_role;
         select result ->> 'idempotent'
         from (
           select public.accept_agentic_rectification_candidate(
             '${userId}', '${rectificationSessionId}', '33333333-3333-4333-8333-333333333333', '04:55'
           ) as result
         ) accepted`,
      ),
      "SET\ntrue",
    );
    assert.equal(
      fixture.psqlAs(
        "admin_runtime",
        "admin-runtime-test-password",
        `set role service_role;
         select (result ->> 'saved_time') || ':' || (result ->> 'status') || ':' || (result ->> 'idempotent')
         from (
           select public.accept_agentic_rectification_candidate(
             '${userId}', '${rectificationSessionId}', '33333333-3333-4333-8333-333333333333', '05:07'
           ) as result
         ) accepted`,
      ),
      "SET\n05:07:accepted:false",
    );
    assert.equal(
      fixture.psql(`select to_char(active_birth_time, 'HH24:MI') || ':' || birth_time_status || ':' || to_char(reported_birth_time, 'HH24:MI') || ':' || coalesce(to_char(birth_time, 'HH24:MI'), 'null') from public.profiles where id = '${userId}'`),
      "05:07:accepted:05:00:null",
    );
    assert.equal(
      fixture.psql(`select invalidated_at is null from public.agentic_rectification_results where id = '33333333-3333-4333-8333-333333333333'`),
      "t",
    );
    fixture.psql(`update public.profiles set reported_birth_time = '05:01' where id = '${userId}'`);
    assert.equal(
      fixture.psql(`select invalidated_at is not null from public.agentic_rectification_results where id = '33333333-3333-4333-8333-333333333333'`),
      "t",
    );
    assert.throws(
      () => fixture.psqlAs(
        "admin_runtime",
        "admin-runtime-test-password",
        `set role service_role;
         select public.accept_agentic_rectification_candidate(
           '${userId}', '${rectificationSessionId}', '33333333-3333-4333-8333-333333333333', '04:55'
         )`,
      ),
      /agentic_rectification_candidate_expired/,
    );

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
