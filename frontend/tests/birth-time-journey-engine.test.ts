import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";
import {
  BirthTimeJourneyEngineConfigurationError,
  createJourneyEngineMethods,
  createJourneyEngineWire,
  differencePacketPayload,
  dynamicChoiceScorePayload,
  eventScorePayload,
  journeyEngineTimeoutMs,
} from "../src/lib/birth-time-journey-engine-model.ts";
import type { JourneyEngineFetch } from "../src/lib/birth-time-journey-engine-model.ts";

test("journey engine serializes only stored event-scoring inputs", () => {
  const payload = eventScorePayload({
    birthDate: "1993-04-17",
    startTime: "14:00",
    endTime: "15:00",
    lat: 31.2304,
    lon: 121.4737,
    tz: 8,
    events: [
      { id: "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5", domain: "career", date: "2019-07", precision: "month" },
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
      { id: "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5", domain: "career", date: "2019-07", precision: "month" },
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
  dismissedOpportunityIds: ["dismissed-1"],
  questionFingerprints: ["question-fingerprint-1"],
  partitionFingerprints: ["partition-fingerprint-1"],
  recentRanges: [{ startTime: "05:30", endTime: "05:33" }],
  candidateModel: { version: "birth-time-choice-scoring-v2" },
} as const;

test("dynamic opportunity payload owns private evidence and candidate model server-side", () => {
  const payload = differencePacketPayload(dynamicInput);

  assert.deepEqual(payload, {
    case_id: "case-1",
    as_of_date: "2026-07-18",
    birth_date: "1990-01-01",
    start_time: "05:30",
    end_time: "05:33",
    lat: 31.23,
    lon: 121.47,
    tz: 8,
    evidence: [{
      question_id: "question-1",
      opportunity_id: "career-window",
      partition_id: "career-early",
      dimension_code: "career",
      candidate_scores: { "05:30": 0, "05:31": 1, "05:32": 1, "05:33": 0 },
      information_gain: 0.5,
    }],
    dismissed_opportunity_ids: ["dismissed-1"],
    question_fingerprints: ["question-fingerprint-1"],
    partition_fingerprints: ["partition-fingerprint-1"],
    recent_ranges: [{ start_time: "05:30", end_time: "05:33" }],
    candidate_model: { version: "birth-time-choice-scoring-v2" },
  });
  const evidence = payload.evidence[0];
  assert.ok(evidence);
  assert.equal("option_id" in evidence, false);
});

test("dynamic score payload sends only server-resolved choice evidence", () => {
  const payload = dynamicChoiceScorePayload(dynamicInput);

  assert.deepEqual(payload.choice_evidence, [{
    question_id: "question-1",
    opportunity_id: "career-window",
    partition_id: "career-early",
    dimension_code: "career",
    candidate_scores: { "05:30": 0, "05:31": 1, "05:32": 1, "05:33": 0 },
    information_gain: 0.5,
  }]);
  assert.equal("case_id" in payload, false);
  assert.equal("candidate_model" in payload, false);
  assert.equal("confidence" in payload, false);
  assert.equal("can_apply" in payload, false);
});

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
  const fetchImpl: JourneyEngineFetch = async (url, init) => {
    calls.push({ url, init });
    const payload = dynamicResponses[new URL(url).pathname];
    return { ok: true, status: 200, async json() { return payload; } };
  };
  const wire = createJourneyEngineWire({
    apiBase: "https://engine.invalid",
    dynamicToken,
    fetchImpl,
  });
  return { calls, engine: createJourneyEngineMethods(wire) };
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
  assert.deepEqual(JSON.parse(String(opportunityCall.init.body)), differencePacketPayload(dynamicInput));
  assert.deepEqual(JSON.parse(String(scoreCall.init.body)), dynamicChoiceScorePayload(dynamicInput));
  assert.ok(opportunityCall.init.signal instanceof AbortSignal);
  assert.ok(scoreCall.init.signal instanceof AbortSignal);
  assert.equal(journeyEngineTimeoutMs, 45_000);
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
