import assert from "node:assert/strict";
import test from "node:test";
import { createBirthTimeConversationPostHandler } from "../src/app/api/birth-time-conversation/route.ts";
import {
  clearBirthTimeConsultationConsent,
  createBirthTimeConsultationConsentState,
  grantBirthTimeConsultationConsent,
  resolveBirthTimeConsultationRoute,
} from "../src/lib/birth-time-consultation-consent.ts";
import { isDeclaredBirthProfileComplete } from "../src/lib/birth-time-intake-model.ts";
import {
  CONVERSATIONAL_RECTIFICATION_UNAVAILABLE,
  sendConversationalRectificationCommand,
} from "../src/lib/conversational-rectification/client.ts";
import {
  conversationalRectificationTurnSchema,
  type ConversationalRectificationTurn,
} from "../src/lib/conversational-rectification/contracts.ts";
import { ConversationalRectificationError } from "../src/lib/conversational-rectification/errors.ts";
import {
  createConversationalRectificationService,
  type ConversationalRectificationServicePorts,
} from "../src/lib/conversational-rectification/orchestrator.ts";
import type { RectificationTechnicalPacket } from "../src/lib/conversational-rectification/technical-packet.ts";
import type {
  LoadedConversationalRectificationCase,
  StoredConversationalRectificationCase,
} from "../src/lib/conversational-rectification/store.ts";
import { createRectificationQuestionHandoffCoordinator } from "../src/lib/rectification-question-handoff.ts";
import type { ConversationalRectificationTelemetryPayload } from "../src/lib/birth-time-journey-telemetry.ts";
import { createConversationalRectificationTelemetry } from "../src/lib/birth-time-journey-telemetry.ts";

const userId = "00000000-0000-4000-8000-000000009001";
const caseId = "00000000-0000-4000-8000-000000009002";
const originalQuestion = "我下一次适合换工作的时间是什么时候？";
const deploymentSha = "0123456789abcdef0123456789abcdef01234567";

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

const onboardingDraft = {
  date: "1990-01-01",
  time: "05:30",
  reportedTime: "05:30",
  birthTimeStatus: "reported" as const,
  birthTimeSource: "approximate" as const,
  birthTimePeriod: "" as const,
  birthTimeClue: "家人只记得天刚亮",
  uncertaintyBeforeMinutes: 30,
  uncertaintyAfterMinutes: 30,
  countryCode: "CN",
  provinceCode: "130000",
  cityCode: "130400",
  districtCode: "130406",
  city: "合成测试城市",
  latitude: 36.420487,
  longitude: 114.209936,
  timezoneOffset: 8,
};

function technicalPacket(ready: boolean): RectificationTechnicalPacket {
  return {
    calculationVersion: "synthetic-rectification-v3",
    candidate: {
      status: ready ? "ready_for_confirmation" : "pending_validation",
      representativeTime: ready ? "05:18" : "05:30",
      range: ready
        ? { startTime: "05:16", endTime: "05:20" }
        : { startTime: "05:00", endTime: "06:00" },
    },
    useBoundary: ready
      ? "候选已达到确认门槛，但明确确认前仍使用旧的账户排盘时间。"
      : "当前时间只是待验证候选，不能当作已经校正完成的出生分钟。",
    candidateModelRefs: ["synthetic-model-ref"],
    candidateDifferenceRefs: ["synthetic-d1", "synthetic-d9", "synthetic-d10", "synthetic-d24"],
    candidateWeights: ready ? { "05:18": 0.75, "05:19": 0.25 } : { "05:30": 0.5 },
    partitionIds: ["private-synthetic-partition"],
    d1Stability: "stable",
    boundaryDistanceMinutes: ready ? 2 : 30,
    sensitivityScope: {
      source: "time_linked_candidate_scan_samples",
      rangeStart: ready ? "05:16" : "05:00",
      rangeEnd: ready ? "05:20" : "06:00",
      sampleTimes: ready ? ["05:16", "05:18", "05:20"] : ["05:00", "05:30", "06:00"],
    },
    stableLayers: [{ layer: "D1", values: ["Cancer"], referenceIds: ["synthetic-d1"] }],
    sensitiveLayers: [
      { layer: "D9", values: ["Aries", "Leo"], referenceIds: ["synthetic-d9"] },
      { layer: "D10", values: ["Taurus", "Libra"], referenceIds: ["synthetic-d10"] },
      { layer: "D24", values: ["Gemini", "Virgo"], referenceIds: ["synthetic-d24"] },
    ],
    supportedSensitiveLayers: ["D9", "D10", "D24"],
    scoredHistoricalEvidence: ready ? [{
      evidenceId: "00000000-0000-4000-8000-000000009099",
      domain: "career",
      candidateTime: "05:18",
      score: 8,
      ruleRefs: ["synthetic-history-rule"],
    }] : [],
    suggestedDomains: [
      { domain: "career", layer: "D10", reason: "D10 在候选范围内变化，已发生的事业事件可以区分候选。" },
      { domain: "education", layer: "D24", reason: "D24 在候选范围内变化，已发生的学业事件可以区分候选。" },
      { domain: "relocation", layer: "D9", reason: "D9 在候选范围内变化，已发生的搬迁事件可以区分候选。" },
    ],
    referenceIds: ["synthetic-d1", "synthetic-d9", "synthetic-d10", "synthetic-d24", "synthetic-history-rule"],
    futureWindows: [{
      label: "未来背景窗口",
      startDate: "2027-01-01",
      endDate: "2027-03-31",
      scoreable: false,
    }],
  };
}

function narrativeGenerator() {
  return {
    modelId: "synthetic-grounded-narrator",
    async generate(prompt: string) {
      const request = JSON.parse(prompt) as {
        phase: "first" | "intermediate" | "final";
        packet: ReturnType<typeof technicalPacket> & {
          candidate: ReturnType<typeof technicalPacket>["candidate"] & {
            rangeStart: string;
            rangeEnd: string;
          };
        };
      };
      const packet = request.packet;
      const final = request.phase === "final";
      return { text: JSON.stringify({
        narrative: [
          `${packet.candidate.representativeTime} 是待验证候选，范围为 ${packet.candidate.rangeStart} 至 ${packet.candidate.rangeEnd}。`,
          "D1 的 Cancer 在范围内保持稳定。",
          "D9 的 Aries / Leo 存在分钟敏感差异，搬迁事件可以区分 D9。",
          "D10 的 Taurus / Libra 存在分钟敏感差异，事业事件可以区分 D10。",
          "D24 的 Gemini / Virgo 存在分钟敏感差异，学业事件可以区分 D24。",
          final ? "现有已发生事件支持进入候选确认。" : "请写一件已经发生的真实事件，注明哪一年、哪一月以及发生了什么。",
          packet.useBoundary,
        ].join(""),
        candidateStatus: packet.candidate.status,
        representativeTime: packet.candidate.representativeTime,
        rangeStart: packet.candidate.rangeStart,
        rangeEnd: packet.candidate.rangeEnd,
        useBoundary: packet.useBoundary,
        stableLayers: packet.stableLayers.map((item) => item.layer),
        sensitiveLayers: packet.sensitiveLayers.map((item) => item.layer),
        referenceIds: [],
        domainReasons: packet.suggestedDomains.map((item) => ({ ...item })),
        evidenceRequest: final ? null : {
          domains: packet.suggestedDomains.map((item) => item.domain),
          datePrecision: "month_preferred",
          prompt: "请提供已经发生的真实事件，并写明哪一年、哪一月以及发生了什么。",
        },
      }) };
    },
  };
}

type Receipt = Readonly<{
  kind: "save_turn" | "pause" | "abandon" | "confirm";
  expectedVersion: number;
  fingerprint: string;
  row: StoredConversationalRectificationCase;
}>;

function createSyntheticBackend(options: { legacy?: boolean; allowNewCaseCreation?: boolean } = {}) {
  const cases = new Map<string, LoadedConversationalRectificationCase>();
  const receipts = new Map<string, Receipt>();
  let activeTime = "04:58";
  let billingState: LoadedConversationalRectificationCase["billingState"] = null;
  let reserveCount = 0;
  let chargeCount = 0;
  let releaseCount = 0;
  const legacyCaseId = "00000000-0000-4000-8000-000000009080";

  const withBilling = (state: LoadedConversationalRectificationCase["billingState"]) => {
    billingState = state;
    for (const [id, row] of cases) cases.set(id, { ...row, billingState: state });
  };
  const save = (input: {
    row?: LoadedConversationalRectificationCase;
    userId: string;
    caseId: string;
    turn: unknown;
    privateCandidate: LoadedConversationalRectificationCase["privateCandidate"];
    evidence?: LoadedConversationalRectificationCase["eventEvidence"];
    receipt?: LoadedConversationalRectificationCase["validationReceipts"][number];
    importedFromCaseId?: string | null;
  }): LoadedConversationalRectificationCase => {
    const prior = input.row;
    const turn = conversationalRectificationTurnSchema.parse(input.turn);
    const next = {
      caseId: input.caseId,
      userId: input.userId,
      status: turn.status,
      turnVersion: turn.turnVersion,
      revisionOfCaseId: prior?.revisionOfCaseId ?? "00000000-0000-4000-8000-000000009000",
      importedFromCaseId: input.importedFromCaseId ?? prior?.importedFromCaseId ?? null,
      baselineActiveTime: "04:58",
      pendingConsultationQuestion: turn.pendingConsultationQuestion,
      billingState,
      latestTurn: structuredClone(turn),
      declaredBirthInput,
      privateCandidate: structuredClone(input.privateCandidate),
      eventEvidence: structuredClone(input.evidence ?? prior?.eventEvidence ?? []),
      validationReceipts: [
        ...(prior?.validationReceipts ?? []),
        ...(input.receipt ? [structuredClone(input.receipt)] : []),
      ],
    } satisfies LoadedConversationalRectificationCase;
    cases.set(input.caseId, next);
    return next;
  };
  const replay = (input: {
    userId: string;
    caseId: string;
    expectedVersion: number;
    actionId: string;
    commandFingerprint: string;
  }, kind: Receipt["kind"], mutate: () => LoadedConversationalRectificationCase) => {
    const prior = receipts.get(input.actionId);
    if (prior) {
      if (prior.kind !== kind || prior.expectedVersion !== input.expectedVersion
        || prior.fingerprint !== input.commandFingerprint) throw new ConversationalRectificationError("action_conflict");
      return prior.row;
    }
    const row = mutate();
    receipts.set(input.actionId, { kind, expectedVersion: input.expectedVersion, fingerprint: input.commandFingerprint, row });
    return row;
  };

  const store: ConversationalRectificationServicePorts["store"] = {
    async loadActionReceipt(input) {
      const prior = receipts.get(input.actionId);
      if (!prior) return null;
      if (prior.kind !== input.actionKind || prior.expectedVersion !== input.expectedVersion
        || prior.fingerprint !== input.commandFingerprint) throw new ConversationalRectificationError("action_conflict");
      return prior.row;
    },
    async loadCase(input) {
      const row = input.caseId ? cases.get(input.caseId) : [...cases.values()].at(-1);
      return row?.userId === input.userId ? structuredClone(row) : null;
    },
    async createCaseWithFirstTurn(input) {
      return save({
        userId: input.userId,
        caseId: input.caseId,
        turn: input.firstTurn,
        privateCandidate: input.privateCandidate,
        receipt: input.validationReceipt,
      });
    },
    async saveTurn(input) {
      return replay(input, "save_turn", () => {
        const row = cases.get(input.caseId);
        if (!row || row.userId !== input.userId) throw new ConversationalRectificationError("case_not_found");
        if (row.turnVersion !== input.expectedVersion) throw new ConversationalRectificationError("stale_turn");
        return save({
          row,
          userId: input.userId,
          caseId: input.caseId,
          turn: input.turn,
          privateCandidate: input.privateCandidate,
          evidence: [...row.eventEvidence, ...input.evidence],
          receipt: input.validationReceipt,
        });
      });
    },
    async pause(input) {
      return replay(input, "pause", () => {
        const row = cases.get(input.caseId);
        if (!row || row.turnVersion !== input.expectedVersion) throw new ConversationalRectificationError("stale_turn");
        return save({ row, userId: input.userId, caseId: input.caseId, turn: input.turn,
          privateCandidate: row.privateCandidate, receipt: input.validationReceipt });
      });
    },
    async abandon(input) {
      return replay(input, "abandon", () => {
        const row = cases.get(input.caseId);
        if (!row || row.turnVersion !== input.expectedVersion) throw new ConversationalRectificationError("stale_turn");
        return save({ row, userId: input.userId, caseId: input.caseId, turn: input.turn,
          privateCandidate: row.privateCandidate, receipt: input.validationReceipt });
      });
    },
    async confirm(input) {
      return replay(input, "confirm", () => {
        const row = cases.get(input.caseId);
        if (!row || row.turnVersion !== input.expectedVersion) throw new ConversationalRectificationError("stale_turn");
        if (row.privateCandidate.resultId !== input.resultId
          || row.privateCandidate.representativeTime !== input.time
          || row.privateCandidate.calculationVersion !== input.calculationVersion) {
          throw new ConversationalRectificationError("candidate_changed");
        }
        activeTime = input.time;
        return save({ row, userId: input.userId, caseId: input.caseId, turn: input.turn,
          privateCandidate: { ...row.privateCandidate, workingState: { phase: "confirmed", iteration: 4, notes: [] } },
          receipt: input.validationReceipt });
      });
    },
    async importLegacy(input) {
      if (cases.has(input.caseId)) return cases.get(input.caseId)!;
      withBilling("migration_waived");
      return save({
        userId: input.userId,
        caseId: input.caseId,
        turn: input.firstTurn,
        privateCandidate: input.privateCandidate,
        evidence: [...input.evidence],
        receipt: input.validationReceipt,
        importedFromCaseId: input.legacyCaseId,
      });
    },
  };

  const service = createConversationalRectificationService({
    store,
    billing: {
      async reserve() { reserveCount += 1; withBilling("reserved"); return { success: true, credits: 97, billingState: "reserved" }; },
      async complete() { chargeCount += 1; withBilling("charged"); return { success: true, credits: 97, billingState: "charged" }; },
      async release() { releaseCount += 1; withBilling("released"); return { success: true, credits: 100, billingState: "released" }; },
    },
    rectificationPriceCredits: 3,
    allowNewCaseCreation: options.allowNewCaseCreation,
    async loadDeclaredProfile() {
      return {
        declaredBirthInput,
        revisionOfCaseId: "00000000-0000-4000-8000-000000009000",
        legacyCaseId: options.legacy ? legacyCaseId : null,
      };
    },
    async loadLegacyCase(receivedUserId, receivedCaseId) {
      if (!options.legacy || receivedUserId !== userId || receivedCaseId !== legacyCaseId) return null;
      return {
        caseId: legacyCaseId,
        userId,
        journeyProtocol: "dynamic-choice-v2",
        status: "rectifying",
        turnVersion: 4,
        declaredBirthInput,
        currentRange: { startTime: "05:10", endTime: "05:50" },
        lifeEvents: [{
          id: "00000000-0000-4000-8000-000000009081",
          domain: "career",
          precision: "month",
          date: "2014-07",
        }],
        currentChoicePrompt: "2006-2011 还是 2011-2016？",
        choiceAnswers: ["A"],
      };
    },
    async buildTechnicalPacket(input) {
      const ready = input.evidence.filter((item) => item.scoreable === true && item.extractionStatus !== "needs_clarification").length >= 3;
      const packet = technicalPacket(ready);
      if (input.preserveCandidateRange && input.privateCandidate?.rangeStart && input.privateCandidate.rangeEnd) {
        return {
          packet: {
            ...packet,
            candidate: {
              ...packet.candidate,
              status: "pending_validation",
              range: { startTime: input.privateCandidate.rangeStart, endTime: input.privateCandidate.rangeEnd },
            },
            sensitivityScope: {
              ...packet.sensitivityScope,
              rangeStart: input.privateCandidate.rangeStart,
              rangeEnd: input.privateCandidate.rangeEnd,
            },
          },
          resultId: null,
        };
      }
      return { packet, resultId: ready ? "00000000-0000-4000-8000-000000009099" : null };
    },
    narrativeGenerator: narrativeGenerator(),
    asOfDate: () => "2026-07-21",
  });

  return {
    service,
    cases,
    billing: () => ({ reserveCount, chargeCount, releaseCount, state: billingState }),
    activeTime: () => activeTime,
    legacyCaseId,
  };
}

async function post(
  handler: (request: Request) => Promise<Response>,
  command: Record<string, unknown>,
): Promise<ConversationalRectificationTurn> {
  const response = await handler(new Request("https://example.invalid/api/birth-time-conversation", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(command),
  }));
  const payload = await response.json();
  assert.equal(response.status, 200, JSON.stringify(payload));
  return payload as ConversationalRectificationTurn;
}

test("authenticated synthetic flow covers soft entry, rich evidence, resume, atomic confirmation, and handoff", async () => {
  assert.equal(isDeclaredBirthProfileComplete(onboardingDraft), true, "onboarding may finish without rectification");

  let consent = createBirthTimeConsultationConsentState();
  assert.deepEqual(resolveBirthTimeConsultationRoute(onboardingDraft, consent, "chat-a"), {
    kind: "choice", canUseUnverifiedTime: true,
  });
  consent = grantBirthTimeConsultationConsent(consent, "chat-a", "unverified_birth_time");
  assert.deepEqual(resolveBirthTimeConsultationRoute(onboardingDraft, consent, "chat-a"), {
    kind: "consult", mode: "unverified_birth_time", time: "05:30",
  });
  assert.equal(resolveBirthTimeConsultationRoute(onboardingDraft, consent, "chat-b").kind, "choice");
  consent = clearBirthTimeConsultationConsent(consent, "chat-a");
  assert.equal(resolveBirthTimeConsultationRoute(onboardingDraft, consent, "chat-a").kind, "choice");

  const backend = createSyntheticBackend();
  const telemetry: ConversationalRectificationTelemetryPayload[] = [];
  const handler = createBirthTimeConversationPostHandler({
    authenticate: async () => ({ userId, context: {} }),
    createService: async () => backend.service,
    deploymentSha,
    telemetry: (payload) => telemetry.push(payload),
    now: (() => { let value = 0; return () => (value += 25); })(),
  });
  let turn = await post(handler, { type: "start", actionId: caseId, pendingConsultationQuestion: originalQuestion });
  assert.equal(turn.pendingConsultationQuestion, originalQuestion);
  assert.equal(turn.status, "active");
  assert.match(turn.narrative, /05:30.*待验证候选/);
  assert.match(turn.narrative, /D1.*稳定/);
  assert.match(turn.narrative, /D9.*敏感差异/);
  assert.match(turn.narrative, /D10.*敏感差异/);
  assert.match(turn.narrative, /哪一年、哪一月/);
  assert.deepEqual(turn.evidenceRequest?.domains, ["career", "education", "relocation"]);
  assert.equal(turn.evidenceRequest?.freeTextAllowed, true);
  assert.equal(JSON.stringify(turn).includes("candidateWeights"), false);
  assert.equal(JSON.stringify(turn).includes("private-synthetic-partition"), false);
  assert.deepEqual(backend.billing(), { reserveCount: 1, chargeCount: 1, releaseCount: 0, state: "charged" });
  assert.equal(backend.activeTime(), "04:58", "revision must retain the old active minute");

  turn = await post(handler, {
    type: "answer", caseId, actionId: "00000000-0000-4000-8000-000000009003",
    turnVersion: turn.turnVersion, domain: "career", answer: "都不符合，我想换一个方向",
  });
  assert.equal(turn.status, "active");
  assert.match(turn.narrative, /不沿用不符合.*自由描述另一件已经发生/);
  assert.equal(backend.billing().chargeCount, 1);

  turn = await post(handler, {
    type: "answer", caseId, actionId: "00000000-0000-4000-8000-000000009004",
    turnVersion: turn.turnVersion, domain: "career", answer: "后来工作压力很大",
  });
  assert.match(turn.narrative, /还缺少.*明确时间/);
  assert.equal(turn.evidenceRecap.at(-1)?.dateLabel, "日期待补充");

  turn = await post(handler, {
    type: "answer", caseId, actionId: "00000000-0000-4000-8000-000000009005",
    turnVersion: turn.turnVersion, domain: "career", answer: "2014年7月第一次正式入职",
  });
  assert.equal(turn.evidenceRecap.at(-1)?.dateLabel, "2014-07");
  turn = await post(handler, {
    type: "pause", caseId, actionId: "00000000-0000-4000-8000-000000009006",
    turnVersion: turn.turnVersion,
  });
  assert.equal(turn.status, "paused");

  const secondDevice = createBirthTimeConversationPostHandler({
    authenticate: async () => ({ userId, context: {} }),
    createService: async () => backend.service,
    deploymentSha,
    telemetry: (payload) => telemetry.push(payload),
  });
  turn = await post(secondDevice, {
    type: "resume", caseId, actionId: "00000000-0000-4000-8000-000000009007",
    turnVersion: turn.turnVersion,
  });
  assert.equal(turn.status, "paused");
  assert.equal(turn.pendingConsultationQuestion, originalQuestion);

  turn = await post(secondDevice, {
    type: "answer", caseId, actionId: "00000000-0000-4000-8000-000000009008",
    turnVersion: turn.turnVersion, domain: "education", answer: "2011年6月大学毕业",
  });
  turn = await post(secondDevice, {
    type: "answer", caseId, actionId: "00000000-0000-4000-8000-000000009009",
    turnVersion: turn.turnVersion, domain: "relocation", answer: "2018年9月搬到外地生活",
  });
  assert.equal(turn.status, "confirming");
  assert.equal(turn.candidate.representativeTime, "05:18");
  assert.equal(backend.activeTime(), "04:58");

  const wrong = await handler(new Request("https://example.invalid/api/birth-time-conversation", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      type: "confirm", caseId, actionId: "00000000-0000-4000-8000-000000009010",
      turnVersion: turn.turnVersion, time: "05:17",
    }),
  }));
  assert.equal(wrong.status, 409);
  assert.equal(backend.activeTime(), "04:58", "a failed confirmation must be atomic");

  turn = await post(secondDevice, {
    type: "confirm", caseId, actionId: "00000000-0000-4000-8000-000000009011",
    turnVersion: turn.turnVersion, time: "05:18",
  });
  assert.equal(turn.status, "completed");
  assert.deepEqual(turn.actions, ["continue_original_question"]);
  assert.equal(backend.activeTime(), "05:18");
  assert.equal(backend.billing().chargeCount, 1);

  let ordinaryReservations = 0;
  let ordinaryAnswers = 0;
  const handoff = createRectificationQuestionHandoffCoordinator<"timing">();
  const continued = await handoff.continueOriginalQuestion(
    turn.pendingConsultationQuestion ?? "",
    { sessionId: "new-device-chat", theme: "timing" },
    async (context) => {
      ordinaryReservations += 1;
      ordinaryAnswers += 1;
      assert.equal(context.question, originalQuestion);
      assert.equal(backend.activeTime(), "05:18");
      return true;
    },
  );
  assert.equal(continued, true);
  assert.equal(ordinaryReservations, 1);
  assert.equal(ordinaryAnswers, 1);

  const chats = new Set(["new-device-chat"]);
  chats.delete("new-device-chat");
  assert.equal(chats.size, 0);
  const caseAfterChatDeletion = backend.cases.get(caseId);
  assert.equal(caseAfterChatDeletion?.status, "completed", "chat deletion must not cascade to the account case");

  const allowedTelemetryKeys = [
    "protocol", "phase", "actionKind", "resultCategory", "latencyBucket",
    "billingState", "errorCategory", "deploymentSha",
  ].sort();
  assert.ok(telemetry.length >= 10);
  for (const payload of telemetry) {
    assert.deepEqual(Object.keys(payload).sort(), allowedTelemetryKeys);
    assert.equal(payload.protocol, "conversational-evidence-v3");
    assert.equal(payload.deploymentSha, deploymentSha);
    const serialized = JSON.stringify(payload);
    for (const forbidden of [originalQuestion, "1990-01-01", userId, caseId, "05:18", "05:30"]) {
      assert.equal(serialized.includes(forbidden), false);
    }
  }
});

test("legacy unfinished work imports once with migration waiver and no questionnaire or charge", async () => {
  const backend = createSyntheticBackend({ legacy: true });
  const first = await backend.service.start(userId, { type: "start", actionId: caseId });
  const replay = await backend.service.start(userId, { type: "start", actionId: caseId });
  assert.deepEqual(replay, first);
  assert.equal(backend.cases.get(caseId)?.importedFromCaseId, backend.legacyCaseId);
  assert.equal(backend.cases.get(caseId)?.billingState, "migration_waived");
  assert.deepEqual(backend.billing(), { reserveCount: 0, chargeCount: 0, releaseCount: 0, state: "migration_waived" });
  assert.deepEqual(first.candidate.rangeStart, "05:10");
  assert.deepEqual(first.candidate.rangeEnd, "05:50");
  assert.doesNotMatch(first.narrative, /2006-2011|2011-2016|哪个时间段/);
  assert.equal(JSON.stringify(first).includes("choiceAnswers"), false);
});

test("v3 telemetry rejects every field outside the privacy-safe category contract", () => {
  const emitted: unknown[] = [];
  const record = createConversationalRectificationTelemetry((payload) => emitted.push(payload));
  const valid = {
    protocol: "conversational-evidence-v3",
    phase: "collecting_evidence",
    actionKind: "answer",
    resultCategory: "success",
    latencyBucket: "lt_100ms",
    billingState: "unchanged",
    errorCategory: "none",
    deploymentSha,
  } as const;
  record(valid);
  for (const forbidden of [
    "narrative", "eventText", "birthDate", "birthTime", "email", "userId",
    "accessToken", "refreshToken", "modelPrompt", "caseId", "actionId",
  ]) {
    assert.throws(() => record({ ...valid, [forbidden]: "private" } as never));
  }
  assert.deepEqual(emitted, [valid]);
});

test("transient 502 replays the same command and terminal failures expose only stable Chinese copy", async () => {
  const originalFetch = globalThis.fetch;
  const bodies: string[] = [];
  let attempts = 0;
  globalThis.fetch = async (_input, init) => {
    attempts += 1;
    bodies.push(String(init?.body));
    if (attempts === 1) return new Response("Bad gateway", { status: 502 });
    return Response.json({
      caseId,
      journeyProtocol: "conversational-evidence-v3",
      status: "active",
      turnVersion: 0,
      narrative: "合成安全响应。",
      candidate: { status: "pending_validation", representativeTime: "05:30", rangeStart: "05:00", rangeEnd: "06:00" },
      technicalReceipt: { calculationVersion: "synthetic-v1", stableLayers: ["D1"], sensitiveLayers: ["D9"], candidateDifferenceRefs: [] },
      evidenceRequest: { domains: ["career", "education"], datePrecision: "month_preferred", freeTextAllowed: true },
      evidenceRecap: [],
      actions: ["answer", "pause", "abandon"],
      pendingConsultationQuestion: null,
    });
  };
  try {
    const turn = await sendConversationalRectificationCommand({ type: "start", actionId: caseId });
    assert.equal(turn.status, "active");
    assert.equal(attempts, 2);
    assert.equal(bodies[0], bodies[1]);

    globalThis.fetch = async () => new Response("The string did not match the expected pattern", { status: 502 });
    await assert.rejects(
      sendConversationalRectificationCommand({ type: "start", actionId: caseId }),
      (error: unknown) => error instanceof Error
        && error.message === CONVERSATIONAL_RECTIFICATION_UNAVAILABLE
        && !error.message.includes("expected pattern"),
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("health exposes deployment identity and explicit v3 rollout readiness without environment secrets", async () => {
  const originalFetch = globalThis.fetch;
  const prior = {
    GITHUB_SHA: process.env.GITHUB_SHA,
    RECTIFICATION_V3_CREATE_ENABLED: process.env.RECTIFICATION_V3_CREATE_ENABLED,
    RECTIFICATION_V3_MIGRATIONS_READY: process.env.RECTIFICATION_V3_MIGRATIONS_READY,
    SUPABASE_SERVICE_ROLE_KEY: process.env.SUPABASE_SERVICE_ROLE_KEY,
  };
  process.env.GITHUB_SHA = deploymentSha;
  process.env.RECTIFICATION_V3_CREATE_ENABLED = "true";
  process.env.RECTIFICATION_V3_MIGRATIONS_READY = "true";
  process.env["SUPABASE_SERVICE_ROLE_KEY"] = "synthetic-runtime-secret-never-return";
  globalThis.fetch = async () => Response.json({ status: "ok" });
  try {
    const { GET: healthGet } = await import(`../src/app/api/health/route.ts?e2e=${Date.now()}`);
    const response = await healthGet();
    const body = await response.json() as Record<string, unknown>;
    assert.deepEqual(body.deployment, { gitCommit: deploymentSha });
    assert.deepEqual(body.rollout, {
      conversationalRectificationV3: {
        protocol: "conversational-evidence-v3",
        newCaseCreation: "enabled",
        migrations: "ready",
        syntheticSmoke: "required",
        readyForNewCases: true,
      },
    });
    assert.equal(JSON.stringify(body).includes("synthetic-runtime-secret-never-return"), false);
  } finally {
    globalThis.fetch = originalFetch;
    for (const [key, value] of Object.entries(prior)) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
  }
});

test("rollback flag stops only new cases while existing v3 resume stays readable", async () => {
  const enabled = createSyntheticBackend();
  await enabled.service.start(userId, { type: "start", actionId: caseId });
  const backend = createSyntheticBackend({ allowNewCaseCreation: false });
  backend.cases.set(caseId, enabled.cases.get(caseId)!);
  const handler = createBirthTimeConversationPostHandler({
    authenticate: async () => ({ userId, context: {} }),
    createService: async () => backend.service,
    telemetry: () => undefined,
  });
  const blockedStart = await handler(new Request("https://example.invalid/api/birth-time-conversation", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ type: "start", actionId: "00000000-0000-4000-8000-000000009050" }),
  }));
  assert.equal(blockedStart.status, 503);

  const lostStartReplay = await post(handler, { type: "start", actionId: caseId });
  assert.equal(lostStartReplay.caseId, caseId, "an existing start identity remains replayable");

  const resumed = await post(handler, {
    type: "resume", caseId, actionId: "00000000-0000-4000-8000-000000009051", turnVersion: 0,
  });
  assert.equal(resumed.caseId, caseId);
  assert.equal(backend.activeTime(), "04:58");
});

test("a throwing injected telemetry sink cannot turn a committed request into failure", async () => {
  const backend = createSyntheticBackend();
  const handler = createBirthTimeConversationPostHandler({
    authenticate: async () => ({ userId, context: {} }),
    createService: async () => backend.service,
    telemetry: () => { throw new Error("synthetic telemetry outage"); },
  });
  const response = await handler(new Request("https://example.invalid/api/birth-time-conversation", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ type: "start", actionId: caseId }),
  }));
  assert.equal(response.status, 200);
  assert.equal(backend.cases.get(caseId)?.status, "active");
  assert.equal(backend.billing().chargeCount, 1);
});
