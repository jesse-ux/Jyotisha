import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";
import {
  BirthTimeJourneyEngineConfigurationError,
  createJourneyEngineMethods,
  createJourneyEngineWire,
  eventScorePayload,
} from "../src/lib/birth-time-journey-engine-model.ts";
import type { JourneyEngineFetch } from "../src/lib/birth-time-journey-engine-model.ts";
import { resolveDynamicRectificationToken } from "../src/lib/birth-time-dynamic-token.ts";

test("journey engine serializes only stored event-scoring inputs", () => {
  const payload = eventScorePayload({
    birthDate: "1993-04-17",
    startTime: "14:00",
    endTime: "15:00",
    lat: 31.2304,
    lon: 121.4737,
    tz: 8,
    events: [
      { id: "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5", domain: "career", date: "2019-07", precision: "month", summary: "晋升为团队负责人" },
      { id: "0790866c-ad5e-4a45-b2b4-a5c73f6be6ea", domain: "education", date: "2011", precision: "year" },
      { id: "0ef52e51-ab5f-453b-81e5-adb44a929224", domain: "relationship", date: "2021-05-01", precision: "day" },
    ],
  });

  assert.deepEqual(payload, {
    birth_date: "1993-04-17",
    start_time: "14:00",
    end_time: "15:00",
    lat: 31.2304,
    lon: 121.4737,
    tz: 8,
    events: [
      { id: "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5", domain: "career", date: "2019-07", precision: "month", summary: "晋升为团队负责人" },
      { id: "0790866c-ad5e-4a45-b2b4-a5c73f6be6ea", domain: "education", date: "2011", precision: "year" },
      { id: "0ef52e51-ab5f-453b-81e5-adb44a929224", domain: "relationship", date: "2021-05-01", precision: "day" },
    ],
  });
  assert.equal("confidence" in payload, false);
  assert.equal("can_apply" in payload, false);
});

const dynamicInput = {
  caseId: "case-1",
  asOfDate: "2026-07-18",
  birthDate: "1990-01-01",
  startTime: "05:30",
  endTime: "05:33",
  lat: 31.23,
  lon: 121.47,
  tz: 8,
  evidence: [{
    questionId: "question-1",
    opportunityId: "career-window",
    partitionId: "career-early",
    dimensionCode: "career",
    candidateScores: { "05:30": 0, "05:31": 1, "05:32": 1, "05:33": 0 },
    informationGain: 0.5,
  }],
  events: [{
    id: "11111111-1111-4111-8111-111111111111",
    domain: "career",
    date: "2020",
    precision: "year",
  }],
  dismissedOpportunityIds: ["dismissed-1"],
  questionFingerprints: ["question-fingerprint-1"],
  partitionFingerprints: ["partition-fingerprint-1"],
  recentRanges: [{ startTime: "05:30", endTime: "05:33" }],
  candidateModel: { version: "birth-time-choice-scoring-v2" },
} as const;

const expectedChoiceEvidence = [{
  question_id: "question-1",
  opportunity_id: "career-window",
  partition_id: "career-early",
  dimension_code: "career",
  candidate_scores: { "05:30": 0, "05:31": 1, "05:32": 1, "05:33": 0 },
  information_gain: 0.5,
}] as const;
const expectedOpportunityBody = {
  case_id: "case-1",
  as_of_date: "2026-07-18",
  birth_date: "1990-01-01",
  start_time: "05:30",
  end_time: "05:33",
  lat: 31.23,
  lon: 121.47,
  tz: 8,
  evidence: expectedChoiceEvidence,
  events: [{
    id: "11111111-1111-4111-8111-111111111111",
    domain: "career",
    date: "2020",
    precision: "year",
  }],
  dismissed_opportunity_ids: ["dismissed-1"],
  question_fingerprints: ["question-fingerprint-1"],
  partition_fingerprints: ["partition-fingerprint-1"],
  recent_ranges: [{ start_time: "05:30", end_time: "05:33" }],
  candidate_model: { version: "birth-time-choice-scoring-v2" },
} as const;
const expectedScoreBody = {
  birth_date: "1990-01-01",
  start_time: "05:30",
  end_time: "05:33",
  lat: 31.23,
  lon: 121.47,
  tz: 8,
  choice_evidence: expectedChoiceEvidence,
} as const;

const dynamicResponses: Readonly<Record<string, unknown>> = {
  "/api/dynamic_rectification_opportunities": {
    success: true,
    endpoint: "dynamic_rectification_opportunities",
    case_id: "case-1",
    scoring_version: "birth-time-choice-scoring-v2",
    current_range: { start_time: "05:30", end_time: "05:33" },
    opportunities: [],
    asked_question_fingerprints: [],
    candidate_partition_fingerprints: [],
    recent_range_history: [],
    candidate_model: {},
  },
  "/api/dynamic_rectification_score": {
    success: true,
    endpoint: "dynamic_rectification_score",
    result_id: "1d8ee348-61a3-433d-8907-ff6d281b9992",
    confidence: "low",
    can_apply: false,
    winning_segment: null,
    event_count: 1,
    domain_count: 1,
    top_score: 0.5,
    second_score: 0,
    margin_percent: 50,
    reasons: ["insufficient_effective_evidence"],
    evidence: [],
    algorithm_version: "birth-time-choice-scoring-v2",
    evidence_mode: "dynamic_choice",
    effective_answer_count: 1,
    dimension_count: 1,
  },
};

function engineHarness(dynamicToken: string | null) {
  const calls: { readonly url: string; readonly init: RequestInit }[] = [];
  const timeoutCalls: number[] = [];
  const timeoutSignal = new AbortController().signal;
  const fetchImpl: JourneyEngineFetch = async (url, init) => {
    calls.push({ url, init });
    const payload = dynamicResponses[new URL(url).pathname];
    return { ok: true, status: 200, async json() { return payload; } };
  };
  const wire = createJourneyEngineWire({
    apiBase: "https://engine.invalid",
    dynamicToken,
    fetchImpl,
    signalFactory(timeoutMs) {
      timeoutCalls.push(timeoutMs);
      return timeoutSignal;
    },
  });
  return { calls, timeoutCalls, timeoutSignal, engine: createJourneyEngineMethods(wire) };
}

test("both dynamic endpoints send exact bodies with bearer auth and timeout signals", async () => {
  const harness = engineHarness("server-secret");
  await harness.engine.buildDifferencePacket(dynamicInput);
  await harness.engine.scoreChoices(dynamicInput);

  assert.equal(harness.calls.length, 2);
  const opportunityCall = harness.calls[0];
  const scoreCall = harness.calls[1];
  assert.ok(opportunityCall);
  assert.ok(scoreCall);
  assert.equal(opportunityCall.url, "https://engine.invalid/api/dynamic_rectification_opportunities");
  assert.equal(scoreCall.url, "https://engine.invalid/api/dynamic_rectification_score");
  assert.equal(new Headers(opportunityCall.init.headers).get("authorization"), "Bearer server-secret");
  assert.equal(new Headers(scoreCall.init.headers).get("authorization"), "Bearer server-secret");
  assert.equal(opportunityCall.init.method, "POST");
  assert.equal(scoreCall.init.method, "POST");
  assert.deepEqual(JSON.parse(String(opportunityCall.init.body)), expectedOpportunityBody);
  assert.deepEqual(JSON.parse(String(scoreCall.init.body)), expectedScoreBody);
  assert.deepEqual(harness.timeoutCalls, [45_000, 45_000]);
  assert.equal(opportunityCall.init.signal, harness.timeoutSignal);
  assert.equal(scoreCall.init.signal, harness.timeoutSignal);
});

test("missing dynamic token fails both endpoints before fetch", async () => {
  const harness = engineHarness(null);
  await assert.rejects(
    harness.engine.buildDifferencePacket(dynamicInput),
    BirthTimeJourneyEngineConfigurationError,
  );
  await assert.rejects(
    harness.engine.scoreChoices(dynamicInput),
    BirthTimeJourneyEngineConfigurationError,
  );
  assert.equal(harness.calls.length, 0);
});

test("dynamic token derives only from a server-side service role fallback", () => {
  assert.equal(resolveDynamicRectificationToken("configured-token", "service-role"), "configured-token");
  assert.match(resolveDynamicRectificationToken(undefined, "service-role") ?? "", /^[a-f0-9]{64}$/);
  assert.equal(resolveDynamicRectificationToken(undefined, undefined), null);
});

test("legacy wire calls never receive dynamic authorization", async () => {
  const calls: { readonly path: string; readonly init: RequestInit }[] = [];
  const engine = createJourneyEngineMethods(createJourneyEngineWire({
    apiBase: "https://engine.invalid",
    dynamicToken: "server-secret",
    fetchImpl: async (url, init) => {
      const path = new URL(url).pathname;
      calls.push({ path, init });
      const payload = path === "/api/active_rectification_questions"
        ? { questions: [], candidate_scan: { samples: [] } }
        : path === "/api/active_rectification_score"
          ? { answered_count: 0, candidate_cluster_rankings: [], next_round: null, next_round_questions: [] }
          : {
              result_id: "1d8ee348-61a3-433d-8907-ff6d281b9992", confidence: "low", can_apply: false,
              winning_segment: null, event_count: 0, domain_count: 0, top_score: 0, second_score: 0,
              margin_percent: 0, reasons: [], evidence: [], algorithm_version: "birth-time-event-scoring-v1",
            };
      return { ok: true, status: 200, async json() { return payload; } };
    },
  }));
  const scan = await engine.scan({ birthTime: "1990-01-01 05:30", uncertaintyMinutes: 3, lat: 31.23, lon: 121.47, tz: 8, ayanamsa: "lahiri" });
  await engine.score({ questionnaire: scan.questionnaire, answers: {} });
  await engine.scoreEvents({ birthDate: "1990-01-01", startTime: "05:30", endTime: "05:33", lat: 31.23, lon: 121.47, tz: 8, events: [] });
  assert.deepEqual(calls.map((call) => call.path), [
    "/api/active_rectification_questions", "/api/active_rectification_score", "/api/active_rectification_events",
  ]);
  for (const call of calls) {
    assert.equal(new Headers(call.init.headers).has("authorization"), false);
    assert.ok(call.init.signal instanceof AbortSignal);
  }
});

function componentAndHookFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) return componentAndHookFiles(path);
    return /\.(ts|tsx)$/.test(entry.name) ? [path] : [];
  });
}

test("candidate scores stay out of the specified client ownership boundary", () => {
  const files = [
    new URL("../src/lib/birth-time-journey-client.ts", import.meta.url).pathname,
    new URL("../src/lib/birth-time-journey-request.ts", import.meta.url).pathname,
    ...componentAndHookFiles(new URL("../src/components", import.meta.url).pathname),
    ...componentAndHookFiles(new URL("../src/hooks", import.meta.url).pathname),
  ];
  for (const path of files) {
    assert.equal(readFileSync(path, "utf8").includes("candidate_scores"), false, path);
  }
});
