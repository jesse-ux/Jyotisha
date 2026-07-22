import assert from "node:assert/strict";
import test from "node:test";
import {
  projectLegacyCaseForConversationalImport,
  type LegacyConversationalImportSource,
} from "../src/lib/conversational-rectification/legacy-import.ts";
import {
  createConversationalRectificationService,
  type ConversationalRectificationServicePorts,
} from "../src/lib/conversational-rectification/orchestrator.ts";
import { conversationalRectificationTurnSchema } from "../src/lib/conversational-rectification/contracts.ts";
import { ConversationalRectificationError } from "../src/lib/conversational-rectification/errors.ts";
import type { RectificationTechnicalPacket } from "../src/lib/conversational-rectification/technical-packet.ts";
import type {
  ConversationalRectificationTurnInput,
  LoadedConversationalRectificationCase,
} from "../src/lib/conversational-rectification/store.ts";

const userId = "00000000-0000-4000-8000-000000001101";
const legacyCaseId = "00000000-0000-4000-8000-000000001102";
const actionId = "00000000-0000-4000-8000-000000001103";
const competingActionId = "00000000-0000-4000-8000-000000001104";
const lifeEventId = "00000000-0000-4000-8000-000000001105";
const futureEventId = "00000000-0000-4000-8000-000000001106";

const declaredBirthInput = {
  source: "approximate" as const,
  birthDate: "1990-01-01",
  reportedTime: "05:30",
  uncertaintyBeforeMinutes: 30 as const,
  uncertaintyAfterMinutes: 30 as const,
  birthTimeClue: "家人只记得天刚亮",
  birthplace: {
    countryCode: "CN",
    provinceCode: "130000",
    cityCode: "130400",
    districtCode: "130406",
    latitude: 36.420487,
    longitude: 114.209936,
    timezoneOffset: 8,
  },
};

function source(protocol: "legacy-guided-v1" | "dynamic-choice-v2"): LegacyConversationalImportSource {
  return {
    caseId: legacyCaseId,
    userId,
    journeyProtocol: protocol,
    status: "rectifying",
    turnVersion: protocol === "dynamic-choice-v2" ? 4 : 2,
    declaredBirthInput,
    currentRange: protocol === "dynamic-choice-v2"
      ? { startTime: "05:18", endTime: "05:42" }
      : { startTime: "05:10", endTime: "05:50" },
    lifeEvents: [
      { id: lifeEventId, domain: "career", precision: "month", date: "2021-07" },
      { id: futureEventId, domain: "relationship", precision: "month", date: "2099-01" },
    ],
    // These fields deliberately contain the legacy UX material that must not
    // cross the protocol boundary.
    currentChoicePrompt: "哪一个时间段更接近一次持续的健康压力变化？",
    choiceAnswers: [{ optionId: "2006-2011", label: "2006-2011年" }],
  };
}

function packet(range = { startTime: "05:18", endTime: "05:42" }): RectificationTechnicalPacket {
  return {
    calculationVersion: "legacy-import-technical-v1",
    candidate: {
      status: "pending_validation",
      representativeTime: "05:30",
      range,
    },
    useBoundary: "这是继承的待验证候选范围，不是已经确认的出生分钟。",
    candidateModelRefs: ["legacy-import-range-v1"],
    candidateDifferenceRefs: ["d9-boundary", "d10-boundary"],
    candidateWeights: { "05:18": 0.5, "05:42": 0.5 },
    partitionIds: [],
    d1Stability: "stable",
    boundaryDistanceMinutes: 12,
    sensitivityScope: {
      source: "time_linked_candidate_scan_samples",
      rangeStart: range.startTime,
      rangeEnd: range.endTime,
      sampleTimes: [range.startTime, range.endTime],
    },
    stableLayers: [{ layer: "D1", values: ["Cancer"], referenceIds: ["d1"] }],
    sensitiveLayers: [
      { layer: "D9", values: ["Aries", "Taurus"], referenceIds: ["d9-boundary"] },
      { layer: "D10", values: ["Virgo", "Libra"], referenceIds: ["d10-boundary"] },
    ],
    supportedSensitiveLayers: ["D9", "D10"],
    scoredHistoricalEvidence: [{
      evidenceId: lifeEventId,
      domain: "career",
      candidateTime: "05:30",
      score: 2,
      ruleRefs: ["career-rule"],
    }],
    suggestedDomains: [
      { domain: "relationship", layer: "D9", reason: "D9 区分候选" },
      { domain: "career", layer: "D10", reason: "D10 区分候选" },
    ],
    referenceIds: ["d9-boundary", "d10-boundary", "career-rule"],
    futureWindows: [],
  };
}

test("v1 and v2 projection preserves only declared facts, latest range, and scoreable past events", () => {
  for (const protocol of ["legacy-guided-v1", "dynamic-choice-v2"] as const) {
    const legacy = source(protocol);
    const projected = projectLegacyCaseForConversationalImport({
      source: legacy,
      asOfDate: "2026-07-21",
    });

    assert.equal(projected.legacyCaseId, legacyCaseId);
    assert.equal(projected.expectedVersion, legacy.turnVersion);
    assert.deepEqual(projected.declaredBirthInput, declaredBirthInput);
    assert.deepEqual(projected.currentRange, legacy.currentRange);
    assert.deepEqual(projected.evidence.map((item) => ({
      id: item.id,
      domain: item.domain,
      dateValue: item.dateValue,
      datePrecision: item.datePrecision,
      scoreable: item.scoreable,
    })), [{
      id: lifeEventId,
      domain: "career",
      dateValue: "2021-07",
      datePrecision: "month",
      scoreable: true,
    }]);
    const serialized = JSON.stringify(projected);
    assert.equal(serialized.includes("哪一个时间段"), false);
    assert.equal(serialized.includes("2006-2011"), false);
    assert.equal(serialized.includes(futureEventId), false);
  }
});

test("projection rejects terminal, foreign-owner, and unsupported protocol sources", () => {
  for (const candidate of [
    { ...source("legacy-guided-v1"), status: "reported" },
    { ...source("dynamic-choice-v2"), status: "starting" },
    { ...source("dynamic-choice-v2"), status: "active" },
    { ...source("dynamic-choice-v2"), status: "paused" },
    { ...source("legacy-guided-v1"), status: "completed" },
    { ...source("dynamic-choice-v2"), status: "abandoned" },
    { ...source("dynamic-choice-v2"), status: "confirmed" },
    { ...source("dynamic-choice-v2"), userId: competingActionId },
    { ...source("dynamic-choice-v2"), journeyProtocol: "conversational-evidence-v3" },
  ]) {
    assert.throws(() => projectLegacyCaseForConversationalImport({
      source: candidate as LegacyConversationalImportSource,
      asOfDate: "2026-07-21",
      expectedUserId: userId,
    }), (error: unknown) => error instanceof ConversationalRectificationError
      && ["case_not_found", "invalid_transition"].includes(error.code));
  }
});

test("projection accepts exactly the four legal unfinished legacy case statuses", () => {
  for (const status of ["assessing", "rectifying", "candidate", "confirming"]) {
    const projected = projectLegacyCaseForConversationalImport({
      source: { ...source("dynamic-choice-v2"), status },
      asOfDate: "2026-07-21",
      expectedUserId: userId,
    });
    assert.equal(projected.legacyCaseId, legacyCaseId);
  }
});

function importedRow(input: {
  readonly firstTurn: ConversationalRectificationTurnInput;
  readonly privateCandidate: NonNullable<LoadedConversationalRectificationCase["privateCandidate"]>;
  readonly evidence: LoadedConversationalRectificationCase["eventEvidence"];
  readonly pendingConsultationQuestion: string | null;
}): LoadedConversationalRectificationCase {
  return {
    caseId: actionId,
    userId,
    status: "active",
    turnVersion: 0,
    revisionOfCaseId: null,
    importedFromCaseId: legacyCaseId,
    baselineActiveTime: "04:58",
    pendingConsultationQuestion: input.pendingConsultationQuestion,
    billingState: "migration_waived",
    latestTurn: conversationalRectificationTurnSchema.parse(input.firstTurn),
    declaredBirthInput,
    privateCandidate: input.privateCandidate,
    eventEvidence: input.evidence,
    validationReceipts: [{ modelId: "synthetic-narrator", schemaValidated: true }],
  };
}

function harness() {
  const cases = new Map<string, LoadedConversationalRectificationCase>();
  const events: string[] = [];
  let importCount = 0;
  let reserved = 0;
  let loadLegacyCount = 0;
  const ports: ConversationalRectificationServicePorts = {
    rectificationPriceCredits: 9,
    store: {
      async loadCase(input) {
        if (input.caseId) return cases.get(input.caseId) ?? null;
        return [...cases.values()].at(-1) ?? null;
      },
      async loadActionReceipt() { return null; },
      async createCaseWithFirstTurn() { throw new Error("paid create must not run"); },
      async saveTurn() { throw new Error("not used"); },
      async pause() { throw new Error("not used"); },
      async abandon() { throw new Error("not used"); },
      async confirm() { throw new Error("not used"); },
      async importLegacy(input) {
        importCount += 1;
        events.push("import");
        assert.deepEqual(input.declaredBirthInput, declaredBirthInput);
        assert.deepEqual(input.evidence.map((item) => item.id), [lifeEventId]);
        assert.equal(input.firstTurn.evidenceRecap[0]?.id, lifeEventId);
        assert.equal(input.firstTurn.narrative.includes("候选"), true);
        assert.equal(input.firstTurn.narrative.includes("哪一个时间段"), false);
        const row = importedRow({
          firstTurn: input.firstTurn,
          privateCandidate: input.privateCandidate,
          evidence: input.evidence,
          pendingConsultationQuestion: input.pendingConsultationQuestion,
        });
        cases.set(input.caseId, row);
        return row;
      },
    },
    billing: {
      async reserve() { reserved += 1; throw new Error("must not reserve"); },
      async complete() { throw new Error("must not complete"); },
      async release() { throw new Error("must not release"); },
    },
    async loadDeclaredProfile() {
      return {
        declaredBirthInput,
        revisionOfCaseId: null,
        legacyCaseId,
      };
    },
    async loadLegacyCase(receivedUserId, receivedLegacyCaseId) {
      loadLegacyCount += 1;
      assert.equal(receivedUserId, userId);
      assert.equal(receivedLegacyCaseId, legacyCaseId);
      return source("dynamic-choice-v2");
    },
    async buildTechnicalPacket(input) {
      events.push("packet");
      assert.deepEqual({
        rangeStart: input.privateCandidate?.rangeStart,
        rangeEnd: input.privateCandidate?.rangeEnd,
      }, { rangeStart: "05:18", rangeEnd: "05:42" });
      assert.deepEqual(input.evidence.map((item) => item.id), [lifeEventId]);
      assert.equal(input.preserveCandidateRange, true);
      return { packet: packet(), resultId: null };
    },
    narrativeGenerator: {
      modelId: "synthetic-narrator",
      async generate() {
        events.push("narrative");
        return { text: JSON.stringify({
          narrative: "05:18—05:42 是继承的待验证候选范围。D1 稳定，D9、D10 对分钟敏感；请补充一件带年月的真实事业或关系事件。",
          evidenceRequest: { domains: ["career", "relationship"], datePrecision: "month_preferred" },
          facts: {
            calculationVersion: "legacy-import-technical-v1",
            candidateStatus: "pending_validation",
            representativeTime: "05:30",
            rangeStart: "05:18",
            rangeEnd: "05:42",
            stableLayers: ["D1"],
            sensitiveLayers: ["D9", "D10"],
            candidateDifferenceRefs: ["d9-boundary", "d10-boundary", "career-rule"],
          },
        }) };
      },
    },
    asOfDate: () => "2026-07-21",
  };
  return {
    service: createConversationalRectificationService(ports),
    cases,
    events,
    counts: () => ({ importCount, reserved, loadLegacyCount }),
  };
}

test("start imports an owner-bound unfinished case once, waives billing, and returns a fresh rich turn", async () => {
  const value = harness();
  const first = await value.service.start(userId, {
    type: "start",
    actionId,
    pendingConsultationQuestion: "我的事业什么时候变化？",
  });
  assert.equal(first.caseId, actionId);
  assert.equal(first.evidenceRecap[0]?.id, lifeEventId);
  assert.deepEqual(value.events, ["packet", "narrative", "narrative", "import"]);
  assert.deepEqual(value.counts(), { importCount: 1, reserved: 0, loadLegacyCount: 1 });
  const stored = value.cases.get(actionId);
  assert.equal(stored?.importedFromCaseId, legacyCaseId);
  assert.equal(stored?.billingState, "migration_waived");
  assert.equal(stored?.baselineActiveTime, "04:58");

  const repeated = await value.service.start(userId, {
    type: "start",
    actionId,
    pendingConsultationQuestion: "我的事业什么时候变化？",
  });
  assert.deepEqual(repeated, first);
  assert.deepEqual(value.counts(), { importCount: 1, reserved: 0, loadLegacyCount: 1 });
});

test("a second action for the same imported legacy case reuses the existing v3 case", async () => {
  const value = harness();
  const first = await value.service.importLegacyCase(userId, legacyCaseId, actionId, null);
  const repeated = await value.service.importLegacyCase(
    userId,
    legacyCaseId,
    competingActionId,
    null,
  );
  assert.deepEqual(repeated, first);
  assert.deepEqual(value.counts(), { importCount: 1, reserved: 0, loadLegacyCount: 1 });
});

test("a second import action cannot silently replace the pending consultation question", async () => {
  const value = harness();
  await value.service.importLegacyCase(userId, legacyCaseId, actionId, null);
  await assert.rejects(
    value.service.importLegacyCase(
      userId,
      legacyCaseId,
      competingActionId,
      "请先看事业变化",
    ),
    (error: unknown) => error instanceof ConversationalRectificationError
      && error.code === "action_conflict",
  );
  assert.deepEqual(value.counts(), { importCount: 1, reserved: 0, loadLegacyCount: 1 });
});
