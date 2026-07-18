import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { basename, join } from "node:path";
import test from "node:test";
import {
  differencePacketPayload,
  dynamicChoiceScorePayload,
  eventScorePayload,
} from "../src/lib/birth-time-journey-engine-model.ts";

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
  assert.equal("option_id" in payload.evidence[0]!, false);
});

test("dynamic score payload sends only server-resolved choice evidence", () => {
  const payload = dynamicChoiceScorePayload(dynamicInput);

  assert.deepEqual(payload.choice_evidence, differencePacketPayload(dynamicInput).evidence);
  assert.equal("case_id" in payload, false);
  assert.equal("candidate_model" in payload, false);
  assert.equal("confidence" in payload, false);
  assert.equal("can_apply" in payload, false);
});

test("dynamic engine calls are bearer-authenticated while legacy calls stay unauthenticated", () => {
  const source = readFileSync(new URL("../src/lib/birth-time-journey-engine.ts", import.meta.url), "utf8");

  assert.match(source, /JYOTISH_DYNAMIC_RECTIFICATION_TOKEN/);
  assert.match(source, /if \(!token\) throw new BirthTimeJourneyEngineConfigurationError\(\)/);
  assert.match(source, /return `Bearer \$\{token\}`/);
  assert.match(source, /"\/api\/dynamic_rectification_opportunities"[\s\S]*dynamicAuthorization\(\)/);
  assert.match(source, /"\/api\/dynamic_rectification_score"[\s\S]*dynamicAuthorization\(\)/);
  const legacyMethods = source.slice(
    source.indexOf("async scan(input)"),
    source.indexOf("async buildDifferencePacket(input)"),
  );
  assert.match(legacyMethods, /\/api\/active_rectification_questions/);
  assert.match(legacyMethods, /\/api\/active_rectification_score/);
  assert.match(legacyMethods, /\/api\/active_rectification_events/);
  assert.equal(legacyMethods.includes("dynamicAuthorization()"), false);
});

function clientBoundaryFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) return clientBoundaryFiles(path);
    if (!/\.(ts|tsx)$/.test(entry.name)) return [];
    const normalized = path.replaceAll("\\", "/");
    return /\/(components|hooks)\//.test(normalized)
      || /(?:client|request|response)(?:-schema)?\.(?:ts|tsx)$/.test(basename(path))
      ? [path]
      : [];
  });
}

test("private dynamic scoring identifiers never enter client or response modules", () => {
  const sourceRoot = new URL("../src", import.meta.url).pathname;
  const forbidden = [
    "candidate_scores",
    "candidate_model",
    "partition_id",
    "candidateScores",
    "candidateModel",
    "partitionId",
    "JYOTISH_DYNAMIC_RECTIFICATION_TOKEN",
  ];

  for (const path of clientBoundaryFiles(sourceRoot)) {
    const source = readFileSync(path, "utf8");
    for (const identifier of forbidden) {
      assert.equal(source.includes(identifier), false, `${identifier} leaked into ${path}`);
    }
  }
});
