import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  buildProductionConversationalRectificationPacket,
  createBirthTimeConversationPostHandler,
  declaredBirthInputForLegacyCase,
  loadProductionConversationalRectificationProfile,
  type BirthTimeConversationRouteService,
} from "../src/app/api/birth-time-conversation/route.ts";
import { ConversationalRectificationError } from "../src/lib/conversational-rectification/errors.ts";
import type {
  BirthTimeJourneyEngine,
  DifferencePacketInput,
} from "../src/lib/birth-time-journey-service.ts";
import type { LifeEventEvidence } from "../src/lib/conversational-rectification/persistence-contracts.ts";
import type { CandidateResult, LifeEvent } from "../src/lib/birth-time-evidence.ts";

const userId = "00000000-0000-4000-8000-000000000711";
const actionId = "00000000-0000-4000-8000-000000000712";
const caseId = "00000000-0000-4000-8000-000000000713";
const requestId = "00000000-0000-4000-8000-000000000714";

test("production narrator loads the Jyotish Skill without overriding packet truth", () => {
  const source = readFileSync(new URL("../src/app/api/birth-time-conversation/route.ts", import.meta.url), "utf8");

  assert.match(source, /skills:\s*\[jyotishSkillPath\]/);
  assert.match(source, /Use the Jyotish Skill only to choose a natural, one-question-at-a-time evidence strategy and wording/);
  assert.match(source, /supplied packet facts as the exclusive source/);
  assert.match(source, /Never invent, recalculate, or confirm candidate data/);
});

const turn = {
  caseId,
  journeyProtocol: "conversational-evidence-v3" as const,
  status: "active" as const,
  turnVersion: 2,
  narrative: "这是经过服务端验证的合成校正解释。",
  candidate: {
    status: "pending_validation" as const,
    representativeTime: "05:20",
    rangeStart: "05:10",
    rangeEnd: "05:30",
  },
  technicalReceipt: {
    calculationVersion: "rectification-technical-v1",
    stableLayers: ["D1"],
    sensitiveLayers: ["D9", "D10"],
    candidateDifferenceRefs: ["consult-d9", "consult-d10"],
  },
  evidenceRequest: {
    domains: ["relationship" as const, "career" as const],
    datePrecision: "month_preferred" as const,
    freeTextAllowed: true as const,
  },
  evidenceRecap: [],
  actions: ["answer" as const, "pause" as const, "abandon" as const],
  pendingConsultationQuestion: null,
};

function request(body: unknown, events: string[]) {
  return {
    headers: new Headers({ "x-request-id": requestId }),
    async json() {
      events.push("body");
      return body;
    },
  } as Request;
}

function service(overrides: Partial<BirthTimeConversationRouteService> = {}): BirthTimeConversationRouteService {
  const response = async () => turn;
  return {
    importLegacyCase: response,
    start: response,
    resume: response,
    answer: response,
    pause: response,
    abandon: response,
    confirm: response,
    ...overrides,
  };
}

function syntheticEvidence(
  index: number,
  domain: LifeEventEvidence["domain"],
  dateValue = `${2010 + index}-07`,
  datePrecision: LifeEventEvidence["datePrecision"] = "month",
): LifeEventEvidence {
  return {
    id: `00000000-0000-4000-8000-${String(800 + index).padStart(12, "0")}`,
    rawText: `synthetic event ${index}`,
    domain,
    eventSummary: `synthetic summary ${index}`,
    dateValue,
    datePrecision,
    extractionStatus: "clear",
    scoreable: true,
  };
}

function packetEngine(options: {
  readonly scoreCalls?: LifeEvent[][];
  readonly differenceCalls?: DifferencePacketInput[];
  readonly scanTimes?: readonly string[];
  readonly scanCalls?: Array<{ readonly birthTime: string; readonly uncertaintyMinutes: number }>;
  readonly scoreResults?: readonly CandidateResult[];
  readonly differenceError?: Error;
} = {}): BirthTimeJourneyEngine {
  let scoreResultIndex = 0;
  const minute = (value: string) => {
    const [hour = 0, part = 0] = value.slice(-5).split(":").map(Number);
    return hour * 60 + part;
  };
  const clock = (value: number) => {
    const normalized = ((value % 1_440) + 1_440) % 1_440;
    return `${String(Math.floor(normalized / 60)).padStart(2, "0")}:${String(normalized % 60).padStart(2, "0")}`;
  };
  return {
    async scan(input) {
      options.scanCalls?.push({
        birthTime: input.birthTime,
        uncertaintyMinutes: input.uncertaintyMinutes,
      });
      const center = minute(input.birthTime);
      const times = options.scanTimes ?? Array.from(
        { length: input.uncertaintyMinutes * 2 + 1 },
        (_, index) => clock(center - input.uncertaintyMinutes + index),
      );
      return {
        questionnaire: {
          questions: [],
          samples: times.map((time, index) => ({
            ascendantSign: "Cancer",
            d4Sign: index % 2 === 0 ? "Aries" : "Taurus",
            d9Sign: index % 2 === 0 ? "Gemini" : "Virgo",
            d10Sign: index % 2 === 0 ? "Leo" : "Libra",
            d24Sign: "Sagittarius",
            d30Sign: "Pisces",
          })),
          raw: {
            candidate_scan: {
              samples: times.map((time) => ({ time: `1990-01-01 ${time}` })),
            },
          },
        },
      };
    },
    async score() { throw new Error("unexpected questionnaire score"); },
    async scoreEvents(input) {
      assert.ok(input.events.length >= 3 && input.events.length <= 8);
      for (const event of input.events) {
        const birthBoundary = event.precision === "year"
          ? input.birthDate.slice(0, 4)
          : event.precision === "month"
            ? input.birthDate.slice(0, 7)
            : input.birthDate;
        assert.ok(event.date >= birthBoundary, "synthetic scorer rejected pre-birth evidence");
      }
      options.scoreCalls?.push([...input.events]);
      const configured = options.scoreResults?.[scoreResultIndex];
      scoreResultIndex += 1;
      if (configured) return configured;
      return {
        resultId: "00000000-0000-4000-8000-000000000899",
        confidence: "low",
        canApply: false,
        winningSegment: null,
        eventCount: input.events.length,
        domainCount: new Set(input.events.map((event) => event.domain)).size,
        topScore: 1,
        secondScore: 1,
        marginPercent: 0,
        reasons: ["synthetic low result"],
        evidence: [],
        algorithmVersion: "synthetic-event-score-v1",
      };
    },
    async buildDifferencePacket(input) {
      options.differenceCalls?.push(input);
      if (options.differenceError) throw options.differenceError;
      return {
        packet: {
          caseId: input.caseId,
          scoringVersion: "birth-time-choice-scoring-v2",
          currentRange: { startTime: input.startTime, endTime: input.endTime },
          opportunities: [],
          askedQuestionFingerprints: [],
          candidatePartitionFingerprints: [],
          recentRangeHistory: [],
        },
        candidateModel: { version: "birth-time-choice-scoring-v2" },
        scoringPartitions: {},
      };
    },
    async scoreChoices() { throw new Error("unexpected choice score"); },
  };
}

test("production first turn continues when optional candidate differences time out", async () => {
  const built = await buildProductionConversationalRectificationPacket(
    packetEngine({ differenceError: new DOMException("timed out", "TimeoutError") }),
    {
      userId,
      caseId,
      asOfDate: "2026-07-22",
      declaredBirthInput: {
        source: "hospital_record",
        birthDate: "1990-01-01",
        reportedTime: "05:20",
        uncertaintyBeforeMinutes: 2,
        uncertaintyAfterMinutes: 2,
        birthTimeClue: null,
        birthplace: packetBirthplace,
      },
      privateCandidate: null,
      evidence: [],
    },
  );

  assert.equal(built.packet.candidate.status, "pending_validation");
  assert.deepEqual(built.packet.candidate.range, { startTime: "05:18", endTime: "05:22" });
  assert.deepEqual(built.packet.candidateDifferenceRefs.filter((item) => (
    item.startsWith("birth-time-choice-scoring")
  )), []);
  assert.equal(built.packet.suggestedDomains.length >= 2, true);
});

test("production first turn skips the minute-heavy candidate partition call for a full day", async () => {
  const differenceCalls: DifferencePacketInput[] = [];
  const built = await buildProductionConversationalRectificationPacket(
    packetEngine({ differenceCalls }),
    {
      userId,
      caseId,
      asOfDate: "2026-07-22",
      declaredBirthInput: {
        source: "unknown",
        birthDate: "1990-01-01",
        birthTimeClue: null,
        birthplace: packetBirthplace,
      },
      privateCandidate: null,
      evidence: [],
    },
  );

  assert.equal(differenceCalls.length, 0);
  assert.deepEqual(built.packet.candidate.range, { startTime: "00:00", endTime: "23:59" });
  assert.equal(built.packet.suggestedDomains.length >= 2, true);
});

const packetBirthplace = {
  cityCode: "TPE-CITY",
  latitude: 25.0268,
  longitude: 121.5434,
  timezoneOffset: 8,
};

test("authentication happens before body parsing and unauthenticated requests create no privileged service", async () => {
  const events: string[] = [];
  let creates = 0;
  const handler = createBirthTimeConversationPostHandler({
    async authenticate() {
      events.push("auth");
      return null;
    },
    async createService() {
      creates += 1;
      return service();
    },
    createRequestId: () => requestId,
  });
  const response = await handler(request({ type: "start", actionId }, events));
  assert.equal(response.status, 401);
  assert.deepEqual(events, ["auth"]);
  assert.equal(creates, 0);
  assert.deepEqual(await response.json(), {
    code: "authentication_required",
    status: 401,
    error: "请先登录",
    message: "登录后才能继续生时校正。",
    retryable: false,
  });
});

test("strict invalid commands return 400 before admin, billing, or service construction", async () => {
  const events: string[] = [];
  let creates = 0;
  const handler = createBirthTimeConversationPostHandler({
    async authenticate() {
      events.push("auth");
      return { userId, context: null };
    },
    async createService() {
      creates += 1;
      return service();
    },
    createRequestId: () => requestId,
  });
  const response = await handler(request({ type: "start", actionId, price: 0 }, events));
  assert.equal(response.status, 400);
  assert.deepEqual(events, ["auth", "body"]);
  assert.equal(creates, 0);
  assert.equal((await response.json() as { code: string }).code, "invalid_command");
});

test("valid commands dispatch exactly one authenticated service method", async () => {
  const events: string[] = [];
  const calls: unknown[] = [];
  const handler = createBirthTimeConversationPostHandler({
    async authenticate() {
      events.push("auth");
      return { userId, context: { authenticated: true } };
    },
    async createService() {
      events.push("service");
      return service({
        async answer(receivedUserId, command) {
          calls.push([receivedUserId, command]);
          return turn;
        },
      });
    },
    createRequestId: () => requestId,
  });
  const command = { type: "answer", caseId, actionId, turnVersion: 1, answer: "2021年7月毕业" };
  const response = await handler(request(command, events));
  assert.equal(response.status, 200);
  assert.deepEqual(events, ["auth", "body", "service"]);
  assert.deepEqual(calls, [[userId, command]]);
  assert.deepEqual(await response.json(), turn);
});

test("known conflicts and unavailable failures use stable safe Chinese responses", async () => {
  for (const [failure, status, code] of [
    [new ConversationalRectificationError("stale_turn"), 409, "stale_turn"],
    [new ConversationalRectificationError("action_conflict"), 409, "action_conflict"],
    [new ConversationalRectificationError("service_unavailable"), 503, "service_unavailable"],
  ] as const) {
    const logs: unknown[] = [];
    const handler = createBirthTimeConversationPostHandler({
      async authenticate() { return { userId, context: null }; },
      async createService() {
        return service({ async resume() { throw failure; } });
      },
      createRequestId: () => requestId,
      log: (entry) => logs.push(entry),
    });
    const response = await handler(request({ type: "resume", caseId, actionId, turnVersion: 1 }, []));
    const body = await response.json() as { code: string; error: string; message: string };
    assert.equal(response.status, status);
    assert.equal(body.code, code);
    assert.match(`${body.error}${body.message}`, /校正|服务|进度|稍后|重试/);
    assert.deepEqual(logs, [{ code }]);
  }
});

test("unknown SQL, model, and browser errors are never exposed or logged", async () => {
  const raw = "duplicate key SQL WebKit DOMException model response with token=secret";
  const logs: unknown[] = [];
  const handler = createBirthTimeConversationPostHandler({
    async authenticate() { return { userId, context: null }; },
    async createService() {
      return service({ async pause() { throw new Error(raw); } });
    },
    createRequestId: () => requestId,
    log: (entry) => logs.push(entry),
  });
  const response = await handler(request({ type: "pause", caseId, actionId, turnVersion: 1 }, []));
  const serialized = JSON.stringify(await response.json());
  assert.equal(response.status, 503);
  assert.equal(serialized.includes(raw), false);
  assert.equal(JSON.stringify(logs).includes(raw), false);
  assert.deepEqual(logs, [{ code: "service_unavailable" }]);
});

test("production profile conversion links terminal v3 revisions and owner-bound unfinished legacy imports", async () => {
  const priorId = "00000000-0000-4000-8000-000000000715";
  const profile = {
    birth_date: "1990-01-01",
    reported_birth_time: "04:58:00",
    active_birth_time: "05:21:00",
    birth_time_source: "legacy_import",
    birth_time_period: null,
    birth_time_clue: "synthetic dawn clue",
    uncertainty_before_minutes: 0,
    uncertainty_after_minutes: 0,
    country_code: "TW",
    province_code: "TPE",
    city_code: "TPE-CITY",
    district_code: "DAAN",
    latitude: 25.0268,
    longitude: 121.5434,
    timezone_offset: 8,
    rectification_case_id: priorId,
  };
  for (const [prior, expectedRevision, expectedLegacy] of [
    [{ id: priorId, journey_protocol: "conversational-evidence-v3", status: "completed" }, priorId, null],
    [{ id: priorId, journey_protocol: "conversational-evidence-v3", status: "abandoned" }, priorId, null],
    [{ id: priorId, journey_protocol: "conversational-evidence-v3", status: "active" }, null, null],
    [{ id: priorId, journey_protocol: "dynamic-choice-v2", status: "assessing" }, null, priorId],
    [{ id: priorId, journey_protocol: "dynamic-choice-v2", status: "rectifying" }, null, priorId],
    [{ id: priorId, journey_protocol: "legacy-guided-v1", status: "candidate" }, null, priorId],
    [{ id: priorId, journey_protocol: "legacy-guided-v1", status: "confirming" }, null, priorId],
    [{ id: priorId, journey_protocol: "dynamic-choice-v2", status: "reported" }, null, null],
    [{ id: priorId, journey_protocol: "legacy-guided-v1", status: "starting" }, null, null],
    [{ id: priorId, journey_protocol: "dynamic-choice-v2", status: "active" }, null, null],
    [{ id: priorId, journey_protocol: "legacy-guided-v1", status: "paused" }, null, null],
    [{ id: priorId, journey_protocol: "dynamic-choice-v2", status: "confirmed" }, null, null],
    [{ id: priorId, journey_protocol: "legacy-guided-v1", status: "abandoned" }, null, null],
    [{ id: priorId, journey_protocol: "dynamic-choice-v2", status: null }, null, null],
    [{ id: priorId, journey_protocol: "legacy-guided-v1", status: "unexpected" }, null, null],
    [{ id: actionId, journey_protocol: "dynamic-choice-v2", status: "rectifying" }, null, null],
  ] as const) {
    const caseLoads: unknown[] = [];
    const loaded = await loadProductionConversationalRectificationProfile({
      async loadProfile(receivedUserId) {
        assert.equal(receivedUserId, userId);
        return profile;
      },
      async loadRectificationCase(receivedUserId, receivedCaseId) {
        caseLoads.push([receivedUserId, receivedCaseId]);
        return prior;
      },
    }, userId);

    assert.equal(loaded.revisionOfCaseId, expectedRevision);
    assert.equal(loaded.legacyCaseId, expectedLegacy);
    assert.deepEqual(caseLoads, [[userId, priorId]]);
    assert.equal(loaded.declaredBirthInput.source, "legacy_import");
    assert.equal("reportedTime" in loaded.declaredBirthInput
      ? loaded.declaredBirthInput.reportedTime
      : null, "04:58");
  }
});

test("legacy import declaration uses the immutable old case time while preserving current place and clue", () => {
  const declared = declaredBirthInputForLegacyCase({
    birth_date: "1990-01-01",
    reported_birth_time: "06:40:00",
    birth_time_source: "family_exact",
    birth_time_period: null,
    birth_time_clue: "现存账户线索",
    uncertainty_before_minutes: 15,
    uncertainty_after_minutes: 15,
    country_code: "TW",
    province_code: "TPE",
    city_code: "TPE-CITY",
    district_code: "DAAN",
    latitude: 25.0268,
    longitude: 121.5434,
    timezone_offset: 8,
  }, {
    reported_date: "1990-01-01",
    reported_time: "05:20:00",
    source: "approximate",
    reported_period: null,
    uncertainty_before_minutes: 30,
    uncertainty_after_minutes: 30,
  });

  assert.deepEqual(declared, {
    source: "approximate",
    birthDate: "1990-01-01",
    reportedTime: "05:20",
    uncertaintyBeforeMinutes: 30,
    uncertaintyAfterMinutes: 30,
    birthTimeClue: "现存账户线索",
    birthplace: {
      countryCode: "TW",
      provinceCode: "TPE",
      cityCode: "TPE-CITY",
      districtCode: "DAAN",
      latitude: 25.0268,
      longitude: 121.5434,
      timezoneOffset: 8,
    },
  });
});

test("an abandoned imported v3 profile pointer becomes the paid revision base", async () => {
  const importedCaseId = "00000000-0000-4000-8000-000000000120";
  const importedFromCaseId = "00000000-0000-4000-8000-000000000121";
  const loaded = await loadProductionConversationalRectificationProfile({
    async loadProfile() {
      return {
        birth_date: "1990-01-01",
        reported_birth_time: "05:20:00",
        active_birth_time: "04:58:00",
        birth_time_source: "legacy_import",
        birth_time_period: null,
        birth_time_clue: "现存账户线索",
        uncertainty_before_minutes: 0,
        uncertainty_after_minutes: 0,
        country_code: "TW",
        province_code: "TPE",
        city_code: "TPE-CITY",
        district_code: "DAAN",
        latitude: 25.0268,
        longitude: 121.5434,
        timezone_offset: 8,
        rectification_case_id: importedCaseId,
      };
    },
    async loadRectificationCase() {
      return {
        id: importedCaseId,
        journey_protocol: "conversational-evidence-v3",
        status: "abandoned",
        imported_from_case_id: importedFromCaseId,
      };
    },
  }, userId);

  assert.equal(loaded.revisionOfCaseId, importedCaseId);
  assert.equal(loaded.legacyCaseId, null);
});

test("production unknown-time adapter covers the declared full day with bounded deduplicated scans", async () => {
  const scanCalls: Array<{ birthTime: string; uncertaintyMinutes: number }> = [];
  const minute = (value: string) => {
    const [hour = 0, part = 0] = value.slice(-5).split(":").map(Number);
    return hour * 60 + part;
  };
  const clock = (value: number) => {
    const normalized = ((value % 1_440) + 1_440) % 1_440;
    return `${String(Math.floor(normalized / 60)).padStart(2, "0")}:${String(normalized % 60).padStart(2, "0")}`;
  };
  const engine: BirthTimeJourneyEngine = {
    async scan(input) {
      scanCalls.push({ birthTime: input.birthTime, uncertaintyMinutes: input.uncertaintyMinutes });
      const center = minute(input.birthTime);
      const times = Array.from(
        { length: input.uncertaintyMinutes * 2 + 1 },
        (_, index) => clock(center - input.uncertaintyMinutes + index),
      );
      return {
        questionnaire: {
          questions: [],
          samples: times.map((time) => {
            const value = minute(time);
            return {
              ascendantSign: "Cancer",
              d4Sign: value < 720 ? "Aries" : "Taurus",
              d9Sign: value < 720 ? "Gemini" : "Virgo",
              d10Sign: value < 720 ? "Leo" : "Libra",
              d24Sign: "Sagittarius",
              d30Sign: "Pisces",
            };
          }),
          raw: {
            candidate_scan: {
              samples: times.map((time) => ({ time: `1990-01-01 ${time}` })),
            },
          },
        },
      };
    },
    async score() { throw new Error("unexpected questionnaire score"); },
    async scoreEvents() { throw new Error("unexpected event score"); },
    async buildDifferencePacket(input) {
      return {
        packet: {
          caseId: input.caseId,
          scoringVersion: "birth-time-choice-scoring-v2",
          currentRange: { startTime: input.startTime, endTime: input.endTime },
          opportunities: [],
          askedQuestionFingerprints: [],
          candidatePartitionFingerprints: [],
          recentRangeHistory: [],
        },
        candidateModel: { version: "birth-time-choice-scoring-v2" },
        scoringPartitions: {},
      };
    },
    async scoreChoices() { throw new Error("unexpected choice score"); },
  };

  const result = await buildProductionConversationalRectificationPacket(engine, {
    userId,
    caseId,
    asOfDate: "2026-07-21",
    declaredBirthInput: {
      source: "unknown",
      birthDate: "1990-01-01",
      birthTimeClue: null,
      birthplace: {
        cityCode: "TPE-CITY",
        latitude: 25.0268,
        longitude: 121.5434,
        timezoneOffset: 8,
      },
    },
    privateCandidate: null,
    evidence: [],
  });

  assert.equal(scanCalls.length, 4);
  assert.ok(scanCalls.every((call) => call.uncertaintyMinutes >= 1
    && call.uncertaintyMinutes <= 180));
  const covered = new Set<number>();
  for (const call of scanCalls) {
    const center = minute(call.birthTime);
    for (let value = center - call.uncertaintyMinutes;
      value <= center + call.uncertaintyMinutes; value += 1) {
      assert.ok(value >= 0 && value <= 1_439, `scan invented minute ${value}`);
      covered.add(value);
    }
  }
  assert.equal(covered.size, 1_440);
  assert.deepEqual(result.packet.candidate.range, { startTime: "00:00", endTime: "23:59" });
  const sampleTimes = result.packet.sensitivityScope.sampleTimes;
  assert.equal(new Set(sampleTimes).size, sampleTimes.length);
  assert.deepEqual(sampleTimes, [...sampleTimes].sort((left, right) => minute(left) - minute(right)));
});

test("production packet waits for three supported events and then scores the accumulated evidence", async () => {
  const scoreCalls: LifeEvent[][] = [];
  const differenceCalls: DifferencePacketInput[] = [];
  const engine = packetEngine({ scoreCalls, differenceCalls });
  const evidence = [
    syntheticEvidence(1, "education"),
    syntheticEvidence(2, "relocation"),
    syntheticEvidence(3, "career"),
  ];

  for (let count = 1; count <= 3; count += 1) {
    const built = await buildProductionConversationalRectificationPacket(engine, {
      userId,
      caseId,
      asOfDate: "2026-07-21",
      declaredBirthInput: {
        source: "approximate",
        birthDate: "1990-01-01",
        reportedTime: "05:20",
        uncertaintyBeforeMinutes: 30,
        uncertaintyAfterMinutes: 30,
        birthTimeClue: null,
        birthplace: packetBirthplace,
      },
      privateCandidate: null,
      evidence: evidence.slice(0, count),
    });
    assert.equal(built.packet.candidate.status, "pending_validation");
    assert.equal(
      built.resultId,
      count < 3 ? null : "00000000-0000-4000-8000-000000000899",
    );
  }

  assert.equal(scoreCalls.length, 1);
  assert.deepEqual(scoreCalls[0]?.map((event) => event.id), evidence.map((item) => item.id));
  assert.deepEqual(
    differenceCalls.map((input) => input.events.map((event) => event.id)),
    [evidence.slice(0, 1), evidence.slice(0, 2), evidence].map((items) => items.map((item) => item.id)),
    "every next-question request receives the historical evidence available at that turn",
  );
});

test("production keeps the prior candidate range when a scored segment loses technical discrimination", async () => {
  const scanCalls: Array<{ readonly birthTime: string; readonly uncertaintyMinutes: number }> = [];
  const evidence = [
    syntheticEvidence(11, "education"),
    syntheticEvidence(12, "relocation"),
    syntheticEvidence(13, "career"),
  ];
  const overNarrowed: CandidateResult = {
    resultId: "00000000-0000-4000-8000-000000000897",
    confidence: "high",
    canApply: true,
    winningSegment: {
      startTime: "05:20",
      endTime: "05:20",
      representativeTime: "05:20",
      widthMinutes: 1,
    },
    eventCount: 3,
    domainCount: 3,
    topScore: 10,
    secondScore: 1,
    marginPercent: 90,
    reasons: ["synthetic over-narrowed segment"],
    evidence: evidence.map((item) => ({
      eventId: item.id,
      domain: item.domain as "career" | "education" | "relocation",
      candidateTime: "05:20",
      ruleIds: ["synthetic-rule"],
      points: 1,
    })),
    algorithmVersion: "synthetic-event-score-v1",
  };

  const built = await buildProductionConversationalRectificationPacket(
    packetEngine({ scanCalls, scoreResults: [overNarrowed] }),
    {
      userId,
      caseId,
      asOfDate: "2026-07-21",
      declaredBirthInput: {
        source: "approximate",
        birthDate: "1990-01-01",
        reportedTime: "05:20",
        uncertaintyBeforeMinutes: 30,
        uncertaintyAfterMinutes: 30,
        birthTimeClue: null,
        birthplace: packetBirthplace,
      },
      privateCandidate: null,
      evidence,
    },
  );

  assert.deepEqual(scanCalls, [{
    birthTime: "1990-01-01 05:20",
    uncertaintyMinutes: 1,
  }, {
    birthTime: "1990-01-01 05:20",
    uncertaintyMinutes: 30,
  }]);
  assert.deepEqual(built.packet.candidate.range, { startTime: "04:50", endTime: "05:50" });
  assert.equal(built.packet.candidate.status, "pending_validation");
  assert.equal(built.resultId, null);
  assert.deepEqual(
    built.packet.scoredHistoricalEvidence.map((item) => item.evidenceId),
    evidence.map((item) => item.id),
  );
});

test("legacy import scores inherited events without silently replacing the inherited candidate range", async () => {
  const scoreCalls: LifeEvent[][] = [];
  const inherited = { startTime: "05:10", endTime: "05:50" };
  const inheritedEvidence = [
    syntheticEvidence(1, "career"),
    syntheticEvidence(2, "education"),
    syntheticEvidence(3, "relocation"),
  ];
  const scored: CandidateResult = {
    resultId: "00000000-0000-4000-8000-000000000898",
    confidence: "low",
    canApply: false,
    winningSegment: {
      startTime: "05:20",
      endTime: "05:24",
      representativeTime: "05:22",
      widthMinutes: 5,
    },
    eventCount: 3,
    domainCount: 3,
    topScore: 4,
    secondScore: 3,
    marginPercent: 10,
    reasons: ["synthetic narrower scored segment"],
    evidence: inheritedEvidence.map((item) => ({
      eventId: item.id,
      domain: item.domain as "career" | "education" | "relocation",
      candidateTime: "05:22",
      ruleIds: ["synthetic-rule"],
      points: 1,
    })),
    algorithmVersion: "synthetic-event-score-v1",
  };
  const result = await buildProductionConversationalRectificationPacket(
    packetEngine({ scoreCalls, scoreResults: [scored] }),
    {
      userId,
      caseId,
      asOfDate: "2026-07-21",
      declaredBirthInput: {
        source: "approximate",
        birthDate: "1990-01-01",
        reportedTime: "05:20",
        uncertaintyBeforeMinutes: 30,
        uncertaintyAfterMinutes: 30,
        birthTimeClue: null,
        birthplace: packetBirthplace,
      },
      privateCandidate: {
        calculationVersion: "legacy-import-range-v1",
        rangeStart: inherited.startTime,
        rangeEnd: inherited.endTime,
      },
      evidence: inheritedEvidence,
      preserveCandidateRange: true,
    },
  );

  assert.equal(scoreCalls.length, 1, "trusted inherited facts still contribute technical evidence");
  assert.deepEqual(result.packet.candidate.range, inherited);
  assert.equal(result.packet.candidate.status, "pending_validation");
  assert.deepEqual(
    result.packet.scoredHistoricalEvidence.map((item) => item.evidenceId),
    scored.evidence.map((item) => item.eventId),
  );
});

test("production rescans the declared range after correction while ordinary evidence stays incremental", async () => {
  const scanCalls: Array<{ readonly birthTime: string; readonly uncertaintyMinutes: number }> = [];
  const narrowResult: CandidateResult = {
    resultId: "00000000-0000-4000-8000-000000001301",
    confidence: "low",
    canApply: false,
    winningSegment: {
      startTime: "05:16",
      endTime: "05:20",
      representativeTime: "05:18",
      widthMinutes: 5,
    },
    eventCount: 3,
    domainCount: 3,
    topScore: 4,
    secondScore: 3,
    marginPercent: 10,
    reasons: ["synthetic narrowed range"],
    evidence: [],
    algorithmVersion: "synthetic-event-score-v1",
  };
  const broadResult: CandidateResult = {
    ...narrowResult,
    resultId: "00000000-0000-4000-8000-000000001302",
    winningSegment: null,
    reasons: ["synthetic evidence no longer narrows the range"],
  };
  const engine = packetEngine({
    scanCalls,
    scoreResults: [narrowResult, broadResult, broadResult],
  });
  const declaredBirthInput = {
    source: "approximate" as const,
    birthDate: "1990-01-01",
    reportedTime: "05:20",
    uncertaintyBeforeMinutes: 30 as const,
    uncertaintyAfterMinutes: 30 as const,
    birthTimeClue: null,
    birthplace: packetBirthplace,
  };
  const oldEvidence = [
    syntheticEvidence(41, "education"),
    syntheticEvidence(42, "relocation"),
    syntheticEvidence(43, "career"),
  ];

  const narrowed = await buildProductionConversationalRectificationPacket(engine, {
    userId,
    caseId,
    asOfDate: "2026-07-21",
    declaredBirthInput,
    privateCandidate: null,
    evidence: oldEvidence,
  });
  assert.deepEqual(narrowed.packet.candidate.range, { startTime: "05:16", endTime: "05:20" });
  assert.deepEqual(scanCalls.at(-1), {
    birthTime: "1990-01-01 05:18",
    uncertaintyMinutes: 2,
  });

  const currentCandidate = {
    calculationVersion: narrowed.packet.calculationVersion,
    rangeStart: narrowed.packet.candidate.range.startTime,
    rangeEnd: narrowed.packet.candidate.range.endTime,
    representativeTime: narrowed.packet.candidate.representativeTime,
  };
  const ordinary = await buildProductionConversationalRectificationPacket(engine, {
    userId,
    caseId,
    asOfDate: "2026-07-21",
    declaredBirthInput,
    privateCandidate: currentCandidate,
    evidence: [...oldEvidence, syntheticEvidence(44, "relationship")],
  });
  assert.deepEqual(ordinary.packet.candidate.range, { startTime: "05:16", endTime: "05:20" });
  assert.deepEqual(scanCalls.at(-1), {
    birthTime: "1990-01-01 05:18",
    uncertaintyMinutes: 2,
  });

  const corrected = await buildProductionConversationalRectificationPacket(engine, {
    userId,
    caseId,
    asOfDate: "2026-07-21",
    declaredBirthInput,
    privateCandidate: null,
    evidence: [
      syntheticEvidence(45, "education"),
      syntheticEvidence(46, "relocation"),
      syntheticEvidence(47, "career"),
    ],
  });
  assert.deepEqual(corrected.packet.candidate.range, { startTime: "04:50", endTime: "05:50" });
  assert.deepEqual(scanCalls.at(-1), {
    birthTime: "1990-01-01 05:20",
    uncertaintyMinutes: 30,
  });
  assert.ok(corrected.packet.sensitivityScope.sampleTimes.includes("04:50"));
  assert.equal(ordinary.packet.sensitivityScope.sampleTimes.includes("04:50"), false);
});

test("production packet sends health evidence and uses the shared eight-event convergence limit", async () => {
  const scoreCalls: LifeEvent[][] = [];
  const differenceCalls: DifferencePacketInput[] = [];
  const engine = packetEngine({ scoreCalls, differenceCalls });
  const domains = ["education", "relocation", "career", "relationship", "health_pressure"] as const;
  const evidence = Array.from({ length: 8 }, (_, index) =>
    syntheticEvidence(index + 1, domains[index % domains.length] ?? "career"));

  await buildProductionConversationalRectificationPacket(engine, {
    userId,
    caseId,
    asOfDate: "2026-07-21",
    declaredBirthInput: {
      source: "approximate",
      birthDate: "1990-01-01",
      reportedTime: "05:20",
      uncertaintyBeforeMinutes: 30,
      uncertaintyAfterMinutes: 30,
      birthTimeClue: null,
      birthplace: packetBirthplace,
    },
    privateCandidate: null,
    evidence,
  });

  assert.equal(scoreCalls.length, 1);
  assert.deepEqual(
    scoreCalls[0]?.map((event) => event.id),
    evidence.map((item) => item.id),
  );
  assert.deepEqual(
    differenceCalls.at(-1)?.events.map((event) => event.id),
    evidence.map((item) => item.id),
  );
  assert.ok(scoreCalls[0]?.some((event) => event.domain === "health_pressure"));
});

test("persistable future background evidence never reaches the production scorer", async () => {
  const scoreCalls: LifeEvent[][] = [];
  const engine = packetEngine({ scoreCalls });
  const historical = [
    syntheticEvidence(61, "education", "2018-06", "month"),
    syntheticEvidence(62, "relocation", "2020-09", "month"),
    syntheticEvidence(63, "career", "2024-03", "month"),
  ];
  const future = {
    ...syntheticEvidence(64, "career", "2027", "year"),
    rawText: "2027年计划换工作",
    eventSummary: "计划换工作",
    scoreable: false as const,
  };

  await buildProductionConversationalRectificationPacket(engine, {
    userId,
    caseId,
    asOfDate: "2026-07-21",
    declaredBirthInput: {
      source: "approximate",
      birthDate: "1990-01-01",
      reportedTime: "05:20",
      uncertaintyBeforeMinutes: 30,
      uncertaintyAfterMinutes: 30,
      birthTimeClue: null,
      birthplace: packetBirthplace,
    },
    privateCandidate: null,
    evidence: [...historical, future],
  });

  assert.deepEqual(scoreCalls.map((events) => events.map((event) => event.id)), [[
    ...historical.map((item) => item.id),
  ]]);
});

test("family evidence stays out of relationship scoring when three real scorer domains exist", async () => {
  const scoreCalls: LifeEvent[][] = [];
  const engine = packetEngine({ scoreCalls });
  const family = syntheticEvidence(1, "family");
  const supported = [
    syntheticEvidence(2, "education"),
    syntheticEvidence(3, "relocation"),
    syntheticEvidence(4, "career"),
  ];

  await buildProductionConversationalRectificationPacket(engine, {
    userId,
    caseId,
    asOfDate: "2026-07-21",
    declaredBirthInput: {
      source: "approximate",
      birthDate: "1990-01-01",
      reportedTime: "05:20",
      uncertaintyBeforeMinutes: 30,
      uncertaintyAfterMinutes: 30,
      birthTimeClue: null,
      birthplace: packetBirthplace,
    },
    privateCandidate: null,
    evidence: [family, ...supported],
  });

  assert.equal(scoreCalls.length, 1);
  assert.deepEqual(scoreCalls[0]?.map((event) => event.domain), [
    "education",
    "relocation",
    "career",
  ]);
  assert.equal(scoreCalls[0]?.some((event) => event.id === family.id), false);
  assert.equal(scoreCalls[0]?.some((event) => event.domain === "relationship"), false);
});

test("dated finance evidence reaches the minute scorer without being downgraded to other", async () => {
  const scoreCalls: LifeEvent[][] = [];
  const engine = packetEngine({ scoreCalls });

  await buildProductionConversationalRectificationPacket(engine, {
    userId,
    caseId,
    asOfDate: "2026-07-21",
    declaredBirthInput: {
      source: "approximate",
      birthDate: "1990-01-01",
      reportedTime: "05:20",
      uncertaintyBeforeMinutes: 30,
      uncertaintyAfterMinutes: 30,
      birthTimeClue: null,
      birthplace: packetBirthplace,
    },
    privateCandidate: null,
    evidence: [
      syntheticEvidence(71, "education"),
      syntheticEvidence(72, "relocation"),
      syntheticEvidence(73, "finance"),
    ],
  });

  assert.equal(scoreCalls.length, 1);
  assert.deepEqual(scoreCalls[0]?.map((event) => event.domain), [
    "education",
    "relocation",
    "finance",
  ]);
});

test("a single period-only scan filters duplicate and out-of-range samples from the exact :59 range", async () => {
  const engine = packetEngine({ scanTimes: ["08:00", "08:01", "10:00", "10:00", "12:00"] });
  const built = await buildProductionConversationalRectificationPacket(engine, {
    userId,
    caseId,
    asOfDate: "2026-07-21",
    declaredBirthInput: {
      source: "period_only",
      birthDate: "1990-01-01",
      reportedPeriod: "morning",
      birthTimeClue: null,
      birthplace: packetBirthplace,
    },
    privateCandidate: null,
    evidence: [],
  });

  assert.deepEqual(built.packet.candidate.range, { startTime: "08:00", endTime: "11:59" });
  assert.deepEqual(built.packet.sensitivityScope.sampleTimes, ["08:00", "08:01", "10:00"]);
});

test("year-precision evidence before birth waits while the birth year can become the valid third event", async () => {
  const scoreCalls: LifeEvent[][] = [];
  const engine = packetEngine({ scoreCalls });
  const valid = [
    syntheticEvidence(20, "education", "2018", "year"),
    syntheticEvidence(21, "relocation", "2019", "year"),
  ];
  const beforeBirth = syntheticEvidence(22, "career", "1999", "year");
  const birthYear = syntheticEvidence(23, "relationship", "2000", "year");
  const input = {
    userId,
    caseId,
    asOfDate: "2026-07-21",
    declaredBirthInput: {
      source: "approximate" as const,
      birthDate: "2000-06-15",
      reportedTime: "05:20",
      uncertaintyBeforeMinutes: 30 as const,
      uncertaintyAfterMinutes: 30 as const,
      birthTimeClue: null,
      birthplace: packetBirthplace,
    },
    privateCandidate: null,
  };

  const waiting = await buildProductionConversationalRectificationPacket(engine, {
    ...input,
    evidence: [...valid, beforeBirth],
  });
  assert.equal(waiting.resultId, null);
  assert.equal(scoreCalls.length, 0);

  await buildProductionConversationalRectificationPacket(engine, {
    ...input,
    evidence: [...valid, beforeBirth, birthYear],
  });
  assert.deepEqual(scoreCalls.map((events) => events.map((event) => event.id)), [[
    ...valid.map((item) => item.id),
    birthYear.id,
  ]]);
});

test("month-precision evidence excludes the month before birth and accepts the birth month", async () => {
  const scoreCalls: LifeEvent[][] = [];
  const engine = packetEngine({ scoreCalls });
  const valid = [
    syntheticEvidence(30, "education", "2018-01", "month"),
    syntheticEvidence(31, "relocation", "2019-02", "month"),
  ];
  const monthBeforeBirth = syntheticEvidence(32, "career", "2000-05", "month");
  const birthMonth = syntheticEvidence(33, "relationship", "2000-06", "month");

  await buildProductionConversationalRectificationPacket(engine, {
    userId,
    caseId,
    asOfDate: "2026-07-21",
    declaredBirthInput: {
      source: "approximate",
      birthDate: "2000-06-15",
      reportedTime: "05:20",
      uncertaintyBeforeMinutes: 30,
      uncertaintyAfterMinutes: 30,
      birthTimeClue: null,
      birthplace: packetBirthplace,
    },
    privateCandidate: null,
    evidence: [...valid, monthBeforeBirth, birthMonth],
  });

  assert.deepEqual(scoreCalls.map((events) => events.map((event) => event.id)), [[
    ...valid.map((item) => item.id),
    birthMonth.id,
  ]]);
});
