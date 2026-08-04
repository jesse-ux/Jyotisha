import assert from "node:assert/strict";
import test from "node:test";

import {
  createAgenticRectificationTools,
  type AgenticRectificationContext,
  type AgenticRectificationTools,
} from "../src/mastra/rectification-tools.ts";

type EngineRoute = {
  path: string;
  respond: (body: unknown) => { status: number; body: unknown };
};

function installEngine(routes: readonly EngineRoute[]) {
  const calls: Array<{ path: string; body: unknown }> = [];
  const original = globalThis.fetch;
  (globalThis as { fetch: unknown }).fetch = async (
    input: RequestInfo | URL,
    init?: RequestInit,
  ) => {
    const path = new URL(String(input)).pathname;
    const body = init?.body ? JSON.parse(String(init.body)) : null;
    calls.push({ path, body });
    const route = routes.find((candidate) => candidate.path === path);
    const respond = route?.respond ?? (() => ({ status: 404, body: { error: "unexpected_route" } }));
    const { status, body: responseBody } = respond(body);
    return {
      ok: status >= 200 && status < 300,
      status,
      json: async () => responseBody,
    } as Response;
  };
  return {
    calls,
    restore: () => {
      (globalThis as { fetch: unknown }).fetch = original;
    },
  };
}

const birth = {
  birth_date: "1990-05-12",
  reported_time: "14:30",
  lat: 31.23,
  lon: 121.47,
  tz: 8,
};

function makeCtx(
  acceptCandidate?: AgenticRectificationContext["acceptCandidate"],
  persistCandidateResult?: AgenticRectificationContext["persistCandidateResult"],
): AgenticRectificationContext {
  return {
    userId: "user-1",
    sessionId: "session-1",
    engineBase: "http://engine.test",
    birth,
    candidateRange: { start_time: "14:00", end_time: "15:00" },
    declaredAccuracy: "15min",
    timeSource: "family_clear",
    persistCandidateResult: persistCandidateResult
      ?? (async () => ({ ok: true as const, result_id: "candidate-result-1" })),
    acceptCandidate: acceptCandidate ?? (async (time) => ({
      ok: true as const,
      saved_time: time,
      status: "confirmed" as const,
      result_id: "candidate-result-1",
    })),
    applyConfirmedBirthTime: async (time) => ({ ok: true as const, saved_time: time }),
  };
}

type AnyTool = { execute: (input: unknown) => Promise<unknown> };
async function runTool(
  tools: AgenticRectificationTools,
  key: keyof AgenticRectificationTools,
  input: unknown,
): Promise<Record<string, unknown>> {
  const tool = tools[key] as unknown as AnyTool;
  return (await tool.execute(input)) as Record<string, unknown>;
}

function requestBody(engine: ReturnType<typeof installEngine>): Record<string, unknown> {
  return (engine.calls[0]?.body ?? {}) as Record<string, unknown>;
}

const confirmedEngineResponse = () => ({
  status: 200,
  body: {
    success: true,
    endpoint: "active_rectification_events",
    result_id: "r1",
    algorithm_version: "fixture",
    canonical_input_hash: "fixture-hash",
    confidence: "high",
    event_count: 4,
    domain_count: 3,
    can_apply: true,
    winning_segment: { start_time: "14:28", end_time: "14:32", representative_time: "14:30", width_minutes: 4 },
    technique_contract: {
      confirmation_allowed: true,
      decision: "confirm_minute",
      external_engines: { status: "pass", validation: { reason: "validated" } },
    },
    reasons: [],
    missing_layers: [],
    candidate_ranking_summary: [
      { rank: 1, time: "14:30", score: 30, tied_minute_count: 1 },
      { rank: 2, time: "14:31", score: 20, tied_minute_count: 1 },
    ],
    boundary: "test",
  },
});

const sampleEvents = [
  { id: "e1", domain: "career" as const, date: "2015", precision: "year" as const },
  { id: "e2", domain: "relationship" as const, date: "2018-06", precision: "month" as const },
  { id: "e3", domain: "relocation" as const, date: "2020", precision: "year" as const },
  { id: "e4", domain: "finance" as const, date: "2012-03-05", precision: "day" as const },
];

test("gate tool posts the birth profile to /api/rectification_gate", async () => {
  const engine = installEngine([
    {
      path: "/api/rectification_gate",
      respond: () => ({
        status: 200,
        body: {
          success: true,
          endpoint: "rectification_gate",
          effective_accuracy: "15min",
          lagna_boundary: { is_sensitive: true, note: "test" },
          enabled_vargas: { D1: "enabled", D9: "enabled" },
          summary: {
            headline: "test",
            enabled: ["D1", "D9"],
            warned: [],
            disabled: [],
            confidence_floor: "medium",
            recommended_events: ["marriage", "relocation"],
            next_action: "collect dated events",
          },
        },
      }),
    },
  ]);
  const tools = createAgenticRectificationTools(makeCtx());
  const result = await runTool(tools, "rectification-gate", {});
  assert.equal(engine.calls[0]?.path, "/api/rectification_gate");
  const sent = requestBody(engine);
  assert.equal(sent.year, 1990);
  assert.equal(sent.month, 5);
  assert.equal(sent.day, 12);
  assert.equal(sent.hour, 14);
  assert.equal(sent.minute, 30);
  assert.equal(sent.lat, 31.23);
  assert.equal(sent.tz, 8);
  assert.equal(result.effective_accuracy, "15min");
  engine.restore();
});

test("score tool normalizes year-precision events into the V5 date range contract", async () => {
  const engine = installEngine([
    {
      path: "/api/rectification/v5/score",
      respond: () => ({
        status: 200,
        body: {
          success: true,
          endpoint: "rectification_v5_score",
          result_id: "r1",
          algorithm_version: "rectification-v5-matrix-scoring-1",
          calculation_spec_hash: "hash",
          candidate_scores: [{ time: "14:30", score: 1.2 }],
          robustness: {
            neighbor_support_minutes: 5,
            leave_one_out_retention_rate: 1,
            leave_one_domain_out_retention_rate: 1,
            date_sensitivity_retention_rate: 1,
          },
          diagnostics: { primary_cluster_retention_rate: 1 },
          missing_layers: [],
          can_confirm_exact_minute: false,
        },
      }),
    },
  ]);
  const tools = createAgenticRectificationTools(makeCtx());
  const result = await runTool(tools, "rectification-score", {
    candidate_range: { start_time: "14:00", end_time: "15:00" },
    events: [
      { id: "marriage-2015", domain: "relationship", date: "2015", precision: "year", summary: "结婚" },
      { id: "moved", domain: "relocation", date: "2015-06", precision: "month", summary: "搬家" },
    ],
  });

  const sent = requestBody(engine);
  const events = (sent.events ?? []) as Array<Record<string, unknown>>;
  assert.equal(sent.start_time, "14:00");
  assert.equal(sent.end_time, "15:00");
  assert.equal(events.length, 2);

  const marriage = events[0]!;
  assert.equal(marriage.date_start, "2015-01-01");
  assert.equal(marriage.date_end, "2015-12-31");
  assert.equal(marriage.event_kind, "relationship_change");
  assert.equal(marriage.precision, "year");
  assert.equal(String(marriage.id).length, 36, "event id is normalized to a stable UUID");

  const moved = events[1]!;
  assert.equal(moved.date_start, "2015-06-01");
  assert.equal(moved.date_end, "2015-06-30");

  assert.equal(result.candidate_count, 1);
  const top = (result.top_candidates as Array<{ time: string }>)[0];
  assert.equal(top?.time, "14:30");
  engine.restore();
});

test("scan tool derives its center and uncertainty from the server-owned range", async () => {
  const engine = installEngine([
    {
      path: "/api/rectification/sensitivity_scan",
      respond: () => ({
        status: 200,
        body: {
          scope: "candidate_time_sensitivity_scan",
          status: "local_computed",
          center_time: "1990-05-12 14:30",
          uncertainty_minutes: 30,
          step_minutes: 5,
          candidate_count: 13,
          rows: [
            { time: "1990-05-12 14:20", sensitive_layers: ["D9", "D10"] },
            { time: "1990-05-12 14:25", sensitive_layers: ["D9"] },
          ],
          supported_vargas: ["D4", "D9", "D10"],
          unavailable_vargas: [],
          pending_layers: ["KP_cusp"],
          transitions: [{ between: ["14:20", "14:25"], changed: ["d1_ascendant"] }],
          boundary: "test",
        },
      }),
    },
  ]);
  const tools = createAgenticRectificationTools(makeCtx());
  const result = await runTool(tools, "rectification-scan", {});
  const sent = requestBody(engine);
  assert.equal(sent.hour, 14);
  assert.equal(sent.minute, 30);
  assert.equal(sent.time_uncertainty_minutes, 30);
  assert.equal(result.candidate_count, 13);
  assert.deepEqual(result.supported_vargas, ["D4", "D9", "D10"]);
  engine.restore();
});

test("gate keeps period-only profiles on the server-owned range without inventing a minute", async () => {
  const engine = installEngine([]);
  const tools = createAgenticRectificationTools({
    ...makeCtx(),
    birth: { ...birth, reported_time: null },
    candidateRange: { start_time: "23:00", end_time: "03:59" },
    declaredAccuracy: "unknown",
  });
  const result = await runTool(tools, "rectification-gate", {});
  assert.equal(engine.calls.length, 0);
  assert.equal(result.endpoint, "server_owned_rectification_preflight");
  assert.deepEqual(result.candidate_range, { start_time: "23:00", end_time: "03:59" });
  engine.restore();
});

test("scan defers an unknown full-day range instead of using a fake noon birth time", async () => {
  const engine = installEngine([]);
  const tools = createAgenticRectificationTools({
    ...makeCtx(),
    birth: { ...birth, reported_time: null },
    candidateRange: { start_time: "00:00", end_time: "23:59" },
  });
  const result = await runTool(tools, "rectification-scan", {});
  assert.equal(engine.calls.length, 0);
  assert.equal(result.status, "deferred_wide_range");
  engine.restore();
});

test("score rejects an Agent-invented range", async () => {
  const engine = installEngine([]);
  const tools = createAgenticRectificationTools(makeCtx());
  await assert.rejects(
    () => runTool(tools, "rectification-score", {
      candidate_range: { start_time: "14:15", end_time: "14:45" },
      events: sampleEvents,
    }),
    /candidate_range_mismatch/,
  );
  assert.equal(engine.calls.length, 0);
  engine.restore();
});

test("save tool rejects before a confirmation gate exists", async () => {
  const engine = installEngine([]);
  const applied: string[] = [];
  const tools = createAgenticRectificationTools(makeCtx(async (time) => {
    applied.push(time);
    return { ok: true as const, saved_time: time, status: "confirmed" as const, result_id: "candidate-result-1" };
  }));
  const result = await runTool(tools, "rectification-save-birth-time", { time: "14:30" });
  assert.equal(result.ok, false);
  assert.match(String(result.reason), /no_confirmed_gate/);
  assert.equal(applied.length, 0);
  engine.restore();
});

test("save tool rejects a time that does not equal the confirmed minute", async () => {
  const engine = installEngine([
    { path: "/api/active_rectification_events", respond: confirmedEngineResponse },
  ]);
  const applied: string[] = [];
  const tools = createAgenticRectificationTools(makeCtx(async (time) => {
    applied.push(time);
    return { ok: true as const, saved_time: time, status: "confirmed" as const, result_id: "candidate-result-1" };
  }));
  await runTool(tools, "rectification-confirm", {
    candidate_range: { start_time: "14:00", end_time: "15:00" },
    events: sampleEvents,
  });
  const rejected = await runTool(tools, "rectification-save-birth-time", { time: "14:29" });
  assert.equal(rejected.ok, false);
  assert.match(String(rejected.reason), /time_mismatch/);
  assert.equal(applied.length, 0);
  engine.restore();
});

test("confirm then save with the matching minute applies the write", async () => {
  const engine = installEngine([
    { path: "/api/active_rectification_events", respond: confirmedEngineResponse },
  ]);
  const applied: string[] = [];
  const tools = createAgenticRectificationTools(makeCtx(async (time) => {
    applied.push(time);
    return { ok: true as const, saved_time: time, status: "confirmed" as const, result_id: "candidate-result-1" };
  }));
  const confirm = await runTool(tools, "rectification-confirm", {
    candidate_range: { start_time: "14:00", end_time: "15:00" },
    events: sampleEvents,
  });
  assert.equal(confirm.confirmation_allowed, true);
  assert.equal(confirm.representative_time, "14:30");

  const saved = await runTool(tools, "rectification-save-birth-time", { time: "14:30" });
  assert.equal(saved.ok, true);
  assert.equal(saved.saved_time, "14:30");
  assert.deepEqual(applied, ["14:30"]);
  engine.restore();
});

test("confirm persists ranked candidates with relative support totaling 100", async () => {
  const engine = installEngine([
    { path: "/api/active_rectification_events", respond: confirmedEngineResponse },
  ]);
  const persisted: unknown[] = [];
  const tools = createAgenticRectificationTools(makeCtx(undefined, async (result) => {
    persisted.push(result);
    return { ok: true as const, result_id: "candidate-result-1" };
  }));

  const result = await runTool(tools, "rectification-confirm", {
    candidate_range: { start_time: "14:00", end_time: "15:00" },
    events: sampleEvents,
  });

  assert.equal(result.selection_allowed, true);
  assert.deepEqual(result.candidates, [
    { rank: 1, time: "14:30", relative_support: 60, tied_minute_count: 1 },
    { rank: 2, time: "14:31", relative_support: 40, tied_minute_count: 1 },
  ]);
  assert.equal((result.candidates as Array<{ relative_support: number }>).reduce((sum, candidate) => sum + candidate.relative_support, 0), 100);
  assert.equal(persisted.length, 1);
  engine.restore();
});

test("confirm distinguishes skipped external validation from a failed VedAstro run", async () => {
  const engine = installEngine([{
    path: "/api/active_rectification_events",
    respond: () => {
      const response = confirmedEngineResponse();
      return {
        ...response,
        body: {
          ...response.body,
          can_apply: false,
          technique_contract: {
            confirmation_allowed: false,
            decision: "continue_rectification",
            external_engines: {
              status: "not_evaluated",
              validation: { reason: "local_candidate_not_ready_for_external_validation" },
            },
          },
        },
      };
    },
  }]);
  const tools = createAgenticRectificationTools(makeCtx());

  const result = await runTool(tools, "rectification-confirm", {
    candidate_range: { start_time: "14:00", end_time: "15:00" },
    events: sampleEvents,
  });

  assert.equal(result.selection_allowed, true);
  assert.equal(result.external_validation_status, "not_evaluated");
  assert.equal(result.external_validation_invoked, false);
  assert.equal(result.external_validation_reason, "local_candidate_not_ready_for_external_validation");
  engine.restore();
});

test("accept candidate tool delegates the exact persisted candidate and preserves accepted status", async () => {
  const calls: Array<{ time: string; resultId?: string }> = [];
  const tools = createAgenticRectificationTools(makeCtx(async (time, resultId) => {
    calls.push({ time, resultId });
    return {
      ok: true as const,
      saved_time: time,
      status: "accepted" as const,
      result_id: "candidate-result-1",
    };
  }));

  const result = await runTool(tools, "rectification-accept-candidate", { time: "14:31" });
  assert.deepEqual(calls, [{ time: "14:31", resultId: undefined }]);
  assert.deepEqual(result, {
    ok: true,
    saved_time: "14:31",
    status: "accepted",
    result_id: "candidate-result-1",
  });
});
