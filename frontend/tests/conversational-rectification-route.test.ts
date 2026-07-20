import assert from "node:assert/strict";
import test from "node:test";
import {
  buildProductionConversationalRectificationPacket,
  createBirthTimeConversationPostHandler,
  loadProductionConversationalRectificationProfile,
  type BirthTimeConversationRouteService,
} from "../src/app/api/birth-time-conversation/route.ts";
import { ConversationalRectificationError } from "../src/lib/conversational-rectification/errors.ts";
import type { BirthTimeJourneyEngine } from "../src/lib/birth-time-journey-service.ts";
import type { LifeEventEvidence } from "../src/lib/conversational-rectification/persistence-contracts.ts";
import type { LifeEvent } from "../src/lib/birth-time-evidence.ts";

const userId = "00000000-0000-4000-8000-000000000711";
const actionId = "00000000-0000-4000-8000-000000000712";
const caseId = "00000000-0000-4000-8000-000000000713";
const requestId = "00000000-0000-4000-8000-000000000714";

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
  readonly scanTimes?: readonly string[];
} = {}): BirthTimeJourneyEngine {
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
      const center = minute(input.birthTime);
      const times = options.scanTimes ?? [
        clock(center - input.uncertaintyMinutes),
        clock(center),
        clock(center + input.uncertaintyMinutes),
      ];
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
      assert.ok(input.events.length >= 3 && input.events.length <= 6);
      for (const event of input.events) {
        const birthBoundary = event.precision === "year"
          ? input.birthDate.slice(0, 4)
          : event.precision === "month"
            ? input.birthDate.slice(0, 7)
            : input.birthDate;
        assert.ok(event.date >= birthBoundary, "synthetic scorer rejected pre-birth evidence");
      }
      options.scoreCalls?.push([...input.events]);
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
    assert.deepEqual(logs, [{ requestId, actionId, caseId, code }]);
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
  assert.deepEqual(logs, [{ requestId, actionId, caseId, code: "service_unavailable" }]);
});

test("production profile conversion only links terminal v3 revisions and leaves pre-v3 baselines unlinked", async () => {
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
  for (const [prior, expectedRevision] of [
    [{ id: priorId, journey_protocol: "conversational-evidence-v3", status: "completed" }, priorId],
    [{ id: priorId, journey_protocol: "conversational-evidence-v3", status: "abandoned" }, priorId],
    [{ id: priorId, journey_protocol: "conversational-evidence-v3", status: "active" }, null],
    [{ id: priorId, journey_protocol: "dynamic-choice-v2", status: "confirmed" }, null],
    [{ id: priorId, journey_protocol: "legacy-guided-v1", status: "confirmed" }, null],
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
    assert.deepEqual(caseLoads, [[userId, priorId]]);
    assert.equal(loaded.declaredBirthInput.source, "legacy_import");
    assert.equal("reportedTime" in loaded.declaredBirthInput
      ? loaded.declaredBirthInput.reportedTime
      : null, "04:58");
  }
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
      const times = [center - input.uncertaintyMinutes, center, center + input.uncertaintyMinutes]
        .map(clock);
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
  const engine = packetEngine({ scoreCalls });
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
});

test("production packet deterministically sends only the latest six supported events", async () => {
  const scoreCalls: LifeEvent[][] = [];
  const engine = packetEngine({ scoreCalls });
  const domains = ["education", "relocation", "career", "relationship"] as const;
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
    evidence.slice(-6).map((item) => item.id),
  );
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

test("a single period-only scan filters duplicate and out-of-range samples from the exact :59 range", async () => {
  const engine = packetEngine({ scanTimes: ["08:00", "10:00", "10:00", "12:00"] });
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
  assert.deepEqual(built.packet.sensitivityScope.sampleTimes, ["08:00", "10:00"]);
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
