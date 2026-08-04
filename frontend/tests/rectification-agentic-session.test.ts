import assert from "node:assert/strict";
import test from "node:test";

import {
  AgenticRectificationProfileError,
  acceptAgenticRectificationCandidate,
  createAgenticRectificationContext,
  loadAgenticRectificationProfile,
  loadLatestAgenticRectificationResult,
} from "../src/lib/rectification-agentic/session.ts";

const userId = "00000000-0000-4000-8000-000000000001";
const sessionId = "00000000-0000-4000-8000-000000000002";

function fakeProfileRow(overrides: Record<string, unknown> = {}) {
  return {
    birth_date: "1990-05-12",
    reported_birth_time: "14:30:00",
    active_birth_time: "14:30:00",
    birth_time_source: "family_vague",
    birth_time_period: null,
    uncertainty_before_minutes: null,
    uncertainty_after_minutes: null,
    latitude: 31.23,
    longitude: 121.47,
    timezone_offset: 8,
    ...overrides,
  };
}

function fakeAccounting(row: Record<string, unknown>) {
  const rpcCalls: Array<{ name: string; args: Record<string, unknown> }> = [];
  const client = {
    from: () => ({
      select: () => ({
        eq: () => ({
          single: async () => ({ data: row, error: null }),
        }),
      }),
    }),
    rpc: async (name: string, args: Record<string, unknown>) => {
      rpcCalls.push({ name, args });
      return { data: { success: true, saved_time: String(args.p_time ?? "") }, error: null };
    },
  };
  return { client, rpcCalls };
}

test("loadAgenticRectificationProfile derives birth fields, accuracy and baseline", async () => {
  const { client } = fakeAccounting(fakeProfileRow({
    active_birth_time: "14:31:00",
    uncertainty_before_minutes: 10,
    uncertainty_after_minutes: 10,
  }));
  const profile = await loadAgenticRectificationProfile(client as never, userId);
  assert.equal(profile.birth_date, "1990-05-12");
  assert.equal(profile.reported_time, "14:31");
  assert.deepEqual(profile.candidateRange, { start_time: "14:21", end_time: "14:41" });
  assert.equal(profile.lat, 31.23);
  assert.equal(profile.lon, 121.47);
  assert.equal(profile.tz, 8);
  assert.equal(profile.declaredAccuracy, "15min");
  assert.equal(profile.timeSource, "family_vague");
  assert.equal(profile.baselineActiveTime, "14:31");
  assert.equal(profile.baselineBirthTimePeriod, null);
});

test("loadAgenticRectificationProfile normalizes a persisted ISO birth date", async () => {
  const { client } = fakeAccounting(fakeProfileRow({ birth_date: "1997-08-08T00:00:00.000Z" }));
  const profile = await loadAgenticRectificationProfile(client as never, userId);
  assert.equal(profile.birth_date, "1997-08-08");
});

test("loadAgenticRectificationProfile normalizes a PostgreSQL Date birth date", async () => {
  const { client } = fakeAccounting(fakeProfileRow({ birth_date: new Date("1997-08-08T00:00:00.000Z") }));
  const profile = await loadAgenticRectificationProfile(client as never, userId);
  assert.equal(profile.birth_date, "1997-08-08");
});

test("loadAgenticRectificationProfile rejects an invalid persisted birth date", async () => {
  const { client } = fakeAccounting(fakeProfileRow({ birth_date: "1997-02-30T00:00:00.000Z" }));
  await assert.rejects(
    () => loadAgenticRectificationProfile(client as never, userId),
    (error) => error instanceof AgenticRectificationProfileError && error.code === "missing_birth_date",
  );
});

test("loadAgenticRectificationProfile treats hospital source as minute accuracy", async () => {
  const { client } = fakeAccounting(fakeProfileRow({
    birth_time_source: "hospital",
    active_birth_time: "09:05:00",
  }));
  const profile = await loadAgenticRectificationProfile(client as never, userId);
  assert.equal(profile.declaredAccuracy, "minute");
  assert.equal(profile.timeSource, "hospital");
  assert.deepEqual(profile.candidateRange, { start_time: "09:03", end_time: "09:07" });
});

test("loadAgenticRectificationProfile accepts a period-only declaration without a fake minute", async () => {
  const { client } = fakeAccounting(fakeProfileRow({
    reported_birth_time: null,
    active_birth_time: null,
    birth_time_source: "period_only",
    birth_time_period: "late_night",
  }));
  const profile = await loadAgenticRectificationProfile(client as never, userId);
  assert.equal(profile.reported_time, null);
  assert.deepEqual(profile.candidateRange, { start_time: "23:00", end_time: "03:59" });
  assert.equal(profile.declaredAccuracy, "unknown");
  assert.equal(profile.baselineBirthTimePeriod, "late_night");
});

test("loadAgenticRectificationProfile accepts an unknown time as the full day", async () => {
  const { client } = fakeAccounting(fakeProfileRow({
    reported_birth_time: null,
    active_birth_time: null,
    birth_time_source: "unknown",
  }));
  const profile = await loadAgenticRectificationProfile(client as never, userId);
  assert.equal(profile.reported_time, null);
  assert.deepEqual(profile.candidateRange, { start_time: "00:00", end_time: "23:59" });
});

test("loadAgenticRectificationProfile preserves a cross-midnight uncertainty range", async () => {
  const { client } = fakeAccounting(fakeProfileRow({
    reported_birth_time: "00:10:00",
    active_birth_time: null,
    birth_time_source: "approximate",
    uncertainty_before_minutes: 30,
    uncertainty_after_minutes: 30,
  }));
  const profile = await loadAgenticRectificationProfile(client as never, userId);
  assert.deepEqual(profile.candidateRange, { start_time: "23:40", end_time: "00:40" });
});

test("loadAgenticRectificationProfile rejects a missing birth date", async () => {
  const { client } = fakeAccounting(fakeProfileRow({ birth_date: null }));
  await assert.rejects(
    () => loadAgenticRectificationProfile(client as never, userId),
    (error) => error instanceof AgenticRectificationProfileError && error.code === "missing_birth_date",
  );
});

test("applyConfirmedBirthTime calls the service-role RPC with the confirmed minute", async () => {
  const { client, rpcCalls } = fakeAccounting(fakeProfileRow({ active_birth_time: "14:30:00" }));
  const profile = await loadAgenticRectificationProfile(client as never, userId);
  const ctx = createAgenticRectificationContext(client as never, userId, profile, sessionId);
  const result = await ctx.applyConfirmedBirthTime("14:30");
  assert.equal(result.ok, true);
  if (result.ok) assert.equal(result.saved_time, "14:30");
  assert.equal(rpcCalls.length, 1);
  assert.equal(rpcCalls[0]?.name, "apply_agentic_rectification_birth_time");
  assert.equal(rpcCalls[0]?.args.p_user_id, userId);
  assert.equal(rpcCalls[0]?.args.p_time, "14:30");
  assert.equal(rpcCalls[0]?.args.p_baseline_time, "14:30");
  assert.equal(rpcCalls[0]?.args.p_source, "agentic-rectification");
});

test("applyConfirmedBirthTime rejects a malformed time before calling the RPC", async () => {
  const { client, rpcCalls } = fakeAccounting(fakeProfileRow());
  const profile = await loadAgenticRectificationProfile(client as never, userId);
  const ctx = createAgenticRectificationContext(client as never, userId, profile, sessionId);
  const result = await ctx.applyConfirmedBirthTime("14:30:00");
  assert.equal(result.ok, false);
  assert.equal(rpcCalls.length, 0);
});

test("applyConfirmedBirthTime surfaces an RPC error as a failure", async () => {
  const rpcCalls: Array<{ name: string }> = [];
  const client = {
    from: () => ({
      select: () => ({
        eq: () => ({
          single: async () => ({ data: fakeProfileRow(), error: null }),
        }),
      }),
    }),
    rpc: async (name: string) => {
      rpcCalls.push({ name });
      return { data: null, error: { message: "agentic_rectification_baseline_changed" } };
    },
  };
  const profile = await loadAgenticRectificationProfile(client as never, userId);
  const ctx = createAgenticRectificationContext(client as never, userId, profile, sessionId);
  const result = await ctx.applyConfirmedBirthTime("14:30");
  assert.equal(result.ok, false);
  assert.match(String(result.reason), /baseline_changed/);
  assert.equal(rpcCalls.length, 1);
});

test("candidate persistence binds the engine result to user, session and profile baseline", async () => {
  const { client: profileClient } = fakeAccounting(fakeProfileRow({
    active_birth_time: "14:31:00",
    uncertainty_before_minutes: 10,
    uncertainty_after_minutes: 10,
  }));
  const profile = await loadAgenticRectificationProfile(profileClient as never, userId);
  const writes: Record<string, unknown>[] = [];
  let conflict = "";
  const client = {
    from: (table: string) => {
      assert.equal(table, "agentic_rectification_results");
      return {
        upsert(values: Record<string, unknown>, options: { onConflict: string }) {
          writes.push(values);
          conflict = options.onConflict;
          return {
            select: () => ({
              single: async () => ({ data: { id: "candidate-result-1" }, error: null }),
            }),
          };
        },
      };
    },
  };
  const ctx = createAgenticRectificationContext(client as never, userId, profile, sessionId);
  const result = await ctx.persistCandidateResult({
    engineResultId: "engine-result-1",
    canonicalInputHash: "fixture-hash",
    algorithmVersion: "fixture-v1",
    candidateRange: { start_time: "14:21", end_time: "14:41" },
    candidates: [{ rank: 1, time: "14:31", relative_support: 100, tied_minute_count: 1 }],
    overallConfidence: "medium",
    marginPercent: 20,
    selectionAllowed: true,
    confirmationAllowed: false,
    representativeTime: "14:31",
  });

  assert.deepEqual(result, { ok: true, result_id: "candidate-result-1" });
  assert.equal(conflict, "user_id,session_id,engine_result_id");
  assert.equal(writes[0]?.user_id, userId);
  assert.equal(writes[0]?.session_id, sessionId);
  assert.equal(writes[0]?.baseline_birth_date, "1990-05-12");
  assert.equal(writes[0]?.baseline_reported_birth_time, "14:30");
  assert.equal(writes[0]?.baseline_active_birth_time, "14:31");
  assert.equal(writes[0]?.baseline_birth_time_period, null);
  assert.equal(writes[0]?.baseline_uncertainty_before_minutes, 10);
  assert.equal(writes[0]?.baseline_latitude, 31.23);
});

test("candidate acceptance calls the service-role RPC with exact ownership and result identity", async () => {
  const calls: Array<{ name: string; args: Record<string, unknown> }> = [];
  const client = {
    rpc: async (name: string, args: Record<string, unknown>) => {
      calls.push({ name, args });
      return {
        data: {
          success: true,
          saved_time: "14:31",
          status: "accepted",
          result_id: "candidate-result-1",
        },
        error: null,
      };
    },
  };

  const result = await acceptAgenticRectificationCandidate(
    client as never,
    userId,
    sessionId,
    "14:31",
    "candidate-result-1",
  );

  assert.deepEqual(result, {
    ok: true,
    saved_time: "14:31",
    status: "accepted",
    result_id: "candidate-result-1",
  });
  assert.deepEqual(calls, [{
    name: "accept_agentic_rectification_candidate",
    args: {
      p_user_id: userId,
      p_session_id: sessionId,
      p_result_id: "candidate-result-1",
      p_time: "14:31",
    },
  }]);
});

test("latest candidate result maps persisted support and selection state for session recovery", async () => {
  const query = {
    select() { return this; },
    eq() { return this; },
    is() { return this; },
    gt() { return this; },
    order() { return this; },
    limit() { return this; },
    async maybeSingle() {
      return {
        data: {
          id: "candidate-result-1",
          candidates: [{ rank: 1, time: "14:31", relative_support: 64, tied_minute_count: 1 }],
          overall_confidence: "medium",
          margin_percent: 18,
          selection_allowed: true,
          confirmation_allowed: false,
          representative_time: "14:31:00",
          selected_time: "14:31:00",
          selection_kind: "user_accepted",
        },
        error: null,
      };
    },
  };
  const client = { from: () => query };

  const result = await loadLatestAgenticRectificationResult(client as never, userId, sessionId);
  assert.deepEqual(result, {
    resultId: "candidate-result-1",
    candidates: [{ rank: 1, time: "14:31", relative_support: 64, tied_minute_count: 1 }],
    overallConfidence: "medium",
    marginPercent: 18,
    selectionAllowed: true,
    confirmationAllowed: false,
    representativeTime: "14:31",
    selectedTime: "14:31",
    selectionStatus: "accepted",
  });
});
