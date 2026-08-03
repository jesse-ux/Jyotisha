import assert from "node:assert/strict";
import test from "node:test";

import {
  AgenticRectificationProfileError,
  createAgenticRectificationContext,
  loadAgenticRectificationProfile,
} from "../src/lib/rectification-agentic/session.ts";

const userId = "00000000-0000-4000-8000-000000000001";

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
  const ctx = createAgenticRectificationContext(client as never, userId, profile);
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
  const ctx = createAgenticRectificationContext(client as never, userId, profile);
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
  const ctx = createAgenticRectificationContext(client as never, userId, profile);
  const result = await ctx.applyConfirmedBirthTime("14:30");
  assert.equal(result.ok, false);
  assert.match(String(result.reason), /baseline_changed/);
  assert.equal(rpcCalls.length, 1);
});
