import assert from "node:assert/strict";
import test from "node:test";
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
  StoredConversationalRectificationCase,
} from "../src/lib/conversational-rectification/store.ts";

const userId = "00000000-0000-4000-8000-000000000701";
const startActionId = "00000000-0000-4000-8000-000000000702";
const answerActionId = "00000000-0000-4000-8000-000000000703";
const pauseActionId = "00000000-0000-4000-8000-000000000704";
const resumeActionId = "00000000-0000-4000-8000-000000000705";
const confirmActionId = "00000000-0000-4000-8000-000000000706";
const priorCaseId = "00000000-0000-4000-8000-000000000707";
const resultId = "00000000-0000-4000-8000-000000000708";
const laterActionId = "00000000-0000-4000-8000-000000000710";
const secondAnswerActionId = "00000000-0000-4000-8000-000000000711";
const thirdAnswerActionId = "00000000-0000-4000-8000-000000000712";
const fourthAnswerActionId = "00000000-0000-4000-8000-000000000713";
const fifthAnswerActionId = "00000000-0000-4000-8000-000000000715";
const secondStartActionId = "00000000-0000-4000-8000-000000000714";

const declaredBirthInput = {
  source: "approximate" as const,
  birthDate: "2000-01-01",
  reportedTime: "05:20",
  uncertaintyBeforeMinutes: 30 as const,
  uncertaintyAfterMinutes: 30 as const,
  birthTimeClue: null,
  birthplace: {
    countryCode: "CN",
    provinceCode: "110000",
    cityCode: "110000-city",
    latitude: 39.9042,
    longitude: 116.4074,
    timezoneOffset: 8,
  },
};

function packet(ready = false): RectificationTechnicalPacket {
  return {
    calculationVersion: "rectification-technical-v1",
    candidate: {
      status: ready ? "ready_for_confirmation" : "pending_validation",
      representativeTime: ready ? "05:18" : "05:20",
      range: ready
        ? { startTime: "05:16", endTime: "05:20" }
        : { startTime: "04:50", endTime: "05:50" },
    },
    useBoundary: ready
      ? "该候选已达到确认门槛，但必须由用户明确确认后才能替换当前排盘时间。"
      : "该时间仅是待验证候选，必须由用户明确确认后才能替换当前排盘时间。",
    candidateModelRefs: ["candidate-model-v1"],
    candidateDifferenceRefs: ["consult-d1", "consult-d9", "consult-d10"],
    candidateWeights: { "05:16": 0.4, "05:18": 0.6 },
    partitionIds: ["private-partition"],
    d1Stability: "stable",
    boundaryDistanceMinutes: 2,
    sensitivityScope: {
      source: "time_linked_candidate_scan_samples",
      rangeStart: ready ? "05:16" : "04:50",
      rangeEnd: ready ? "05:20" : "05:50",
      sampleTimes: ready ? ["05:16", "05:20"] : ["04:50", "05:20", "05:50"],
    },
    stableLayers: [{ layer: "D1", values: ["Cancer"], referenceIds: ["consult-d1"] }],
    sensitiveLayers: [
      { layer: "D9", values: ["Aries", "Leo"], referenceIds: ["consult-d9"] },
      { layer: "D10", values: ["Taurus", "Libra"], referenceIds: ["consult-d10"] },
    ],
    supportedSensitiveLayers: ["D9", "D10"],
    scoredHistoricalEvidence: ready ? [{
      evidenceId: "00000000-0000-4000-8000-000000000709",
      domain: "career",
      candidateTime: "05:18",
      score: 8,
      ruleRefs: ["vim-career"],
    }] : [],
    suggestedDomains: [
      { domain: "relationship", layer: "D9", reason: "D9 在候选范围内呈现 Aries / Leo 差异，可用已发生的关系事件区分。" },
      { domain: "career", layer: "D10", reason: "D10 在候选范围内呈现 Taurus / Libra 差异，可用已发生的事业事件区分。" },
    ],
    referenceIds: ["consult-d1", "consult-d9", "consult-d10"],
    futureWindows: [{
      label: "未来事业背景窗口",
      startDate: "2028-03-01",
      endDate: "2028-05-31",
      scoreable: false,
    }],
  };
}

function validGenerator(
  events: string[],
  varyNarrative = false,
  invalidNarrativeFromGeneration?: number,
  prompts: string[] = [],
  continueLatestEvent = false,
  detailQuestion = "这份工作是正式工作，还是实习或兼职？",
  mislabelLatestDetailAsNewEvent = false,
  classifyEvidenceDomain?: (text: string) => "career" | "education" | "finance" | "health_pressure" | "relocation" | "relationship" | "family" | "other" | null,
) {
  let generation = 0;
  return {
    modelId: "synthetic-rectification-model",
    ...(classifyEvidenceDomain ? {
      async classifyEvidenceDomain(input: Readonly<{ text: string }>) {
        return classifyEvidenceDomain(input.text);
      },
    } : {}),
    async generate(prompt: string) {
      generation += 1;
      events.push("narrative");
      prompts.push(prompt);
      if (invalidNarrativeFromGeneration !== undefined
        && generation >= invalidNarrativeFromGeneration) {
        return { text: "not a grounded narrative result" };
      }
      const request = JSON.parse(prompt) as {
        phase: "first" | "intermediate" | "final";
        conversationContext?: {
          recentConversation?: Array<{ role: "assistant" | "user"; text: string }>;
          latestEvidence?: Array<{ dateLabel: string; summary: string }>;
          eventLedger?: Array<{
            id: string;
            summary: string;
            active: boolean;
          }>;
          unresolvedEvidence?: Array<{
            id: string;
            summary: string;
            dateLabel: string;
          }>;
        };
        packet: Omit<ReturnType<typeof packet>, "candidate"> & {
          candidate: ReturnType<typeof packet>["candidate"] & {
            rangeStart: string;
            rangeEnd: string;
          };
        };
      };
      const value = request.packet;
      const hasRelationshipEvidence = request.conversationContext?.eventLedger
        ?.some((item) => item.active && /关系|恋爱|分手|结婚|离婚|伴侣/.test(item.summary)) === true;
      const domains = hasRelationshipEvidence
        ? ["career" as const]
        : ["relationship" as const];
      const nextDomain = domains[0] === "relationship" ? "重要关系" : "事业";
      const latest = request.conversationContext?.latestEvidence?.at(-1);
      const latestActiveEvent = request.conversationContext?.eventLedger
        ?.filter((item) => item.active)
        .at(-1);
      const unresolved = request.conversationContext?.unresolvedEvidence?.at(-1);
      const asksForLatestDetail = continueLatestEvent
        && request.phase === "intermediate"
        && latestActiveEvent !== undefined;
      const narrative = [
        request.phase === "intermediate" && latest
          ? `记下了：${latest.dateLabel} · ${latest.summary}。`
          : `当前仍在核对 ${value.candidate.rangeStart}–${value.candidate.rangeEnd} 的候选范围，不能视为已经确认的出生分钟。`,
        varyNarrative ? `这是第 ${generation} 次合成措辞。` : "",
        request.phase === "final"
          ? "当前证据已形成候选总结。"
          : unresolved?.dateLabel === "日期待补充"
            ? `我先把“${unresolved.summary}”这件事补完整：它大约发生在哪一年、哪一月？`
          : asksForLatestDetail
            ? detailQuestion
            : `先说一件已经发生的${nextDomain}经历好吗？请写明哪一年、哪一月以及发生了什么。`,
      ].join("");
      return { text: JSON.stringify({
        narrative,
        candidateStatus: value.candidate.status,
        representativeTime: value.candidate.representativeTime,
        rangeStart: value.candidate.rangeStart,
        rangeEnd: value.candidate.rangeEnd,
        useBoundary: value.useBoundary,
        stableLayers: value.stableLayers.map((item) => typeof item === "string" ? item : item.layer),
        sensitiveLayers: value.sensitiveLayers.map((item) => typeof item === "string" ? item : item.layer),
        referenceIds: [],
        domainReasons: [],
        evidenceRequest: request.phase === "final" ? null : {
          domains,
          datePrecision: "month_preferred",
          prompt: unresolved?.dateLabel === "日期待补充"
            ? `“${unresolved.summary}”大约发生在哪一年、哪一月？`
            : asksForLatestDetail
            ? detailQuestion
            : `请说一件已经发生的${nextDomain}经历，并写明哪一年、哪一月以及发生了什么。`,
          followUp: unresolved?.dateLabel === "日期待补充"
            ? { kind: "event_date", evidenceId: unresolved.id }
            : asksForLatestDetail
            ? mislabelLatestDetailAsNewEvent
              ? { kind: "new_event", evidenceId: null }
              : { kind: "event_detail", evidenceId: latestActiveEvent.id }
            : { kind: "new_event", evidenceId: null },
        },
      }) };
    },
  };
}

type MutableCase = {
  row: LoadedConversationalRectificationCase;
};

function harness(options: {
  readonly createFailure?: Error;
  readonly packetFailure?: Error;
  readonly packetFailureFromBuild?: number;
  readonly completeFailures?: number;
  readonly releaseFailure?: boolean;
  readonly readyAfterEvidenceCount?: number;
  readonly packetForEvidenceCount?: (count: number) => RectificationTechnicalPacket;
  readonly varyNarrative?: boolean;
  readonly invalidNarrativeFromGeneration?: number;
  readonly continueLatestEvent?: boolean;
  readonly detailQuestion?: string;
  readonly mislabelLatestDetailAsNewEvent?: boolean;
  readonly classifyEvidenceDomain?: (text: string) => "career" | "education" | "finance" | "health_pressure" | "relocation" | "relationship" | "family" | "other" | null;
} = {}) {
  const events: string[] = [];
  const narrativePrompts: string[] = [];
  const mutations: string[] = [];
  const cases = new Map<string, MutableCase>();
  const receipts = new Map<string, {
    input: unknown;
    response: StoredConversationalRectificationCase;
    actionKind?: "save_turn" | "pause" | "abandon" | "confirm";
    expectedVersion?: number;
    commandFingerprint?: string;
  }>();
  const packetEvidenceCounts: number[] = [];
  const packetEvidenceIds: string[][] = [];
  const packetPrivateCandidates: Array<Readonly<{
    rangeStart?: string | null;
    rangeEnd?: string | null;
    resultId?: string | null;
  }> | null> = [];
  let packetBuilds = 0;
  let reserveCount = 0;
  let releaseCount = 0;
  let remainingCompleteFailures = options.completeFailures ?? 0;
  let billingState: LoadedConversationalRectificationCase["billingState"] = null;

  function updateBillingState(next: LoadedConversationalRectificationCase["billingState"]) {
    billingState = next;
    for (const [caseId, value] of cases) {
      cases.set(caseId, { row: { ...value.row, billingState: next } });
    }
  }

  function stored(input: {
    readonly userId: string;
    readonly caseId: string;
    readonly turn: ConversationalRectificationTurnInput;
    readonly privateCandidate: LoadedConversationalRectificationCase["privateCandidate"];
    readonly evidence?: LoadedConversationalRectificationCase["eventEvidence"];
    readonly receipts?: LoadedConversationalRectificationCase["validationReceipts"];
    readonly revisionOfCaseId?: string | null;
  }): LoadedConversationalRectificationCase {
    return {
      caseId: input.caseId,
      userId: input.userId,
      status: input.turn.status === "completed" ? "completed" : input.turn.status,
      turnVersion: input.turn.turnVersion,
      revisionOfCaseId: input.revisionOfCaseId ?? priorCaseId,
      importedFromCaseId: null,
      baselineActiveTime: "04:58",
      pendingConsultationQuestion: input.turn.pendingConsultationQuestion,
      billingState,
      latestTurn: conversationalRectificationTurnSchema.parse(input.turn),
      declaredBirthInput,
      privateCandidate: input.privateCandidate,
      eventEvidence: input.evidence ?? [],
      validationReceipts: input.receipts ?? [],
    };
  }

  function replay(
    actionId: string,
    input: { readonly expectedVersion?: number; readonly commandFingerprint?: string },
    make: () => LoadedConversationalRectificationCase,
    actionKind?: "save_turn" | "pause" | "abandon" | "confirm",
  ) {
    const prior = receipts.get(actionId);
    if (prior) {
      if (prior.actionKind && prior.commandFingerprint) {
        assert.equal(actionKind, prior.actionKind);
        assert.equal(input.expectedVersion, prior.expectedVersion);
        assert.equal(input.commandFingerprint, prior.commandFingerprint);
      } else {
        assert.deepEqual(input, prior.input);
      }
      return prior.response;
    }
    const response = make();
    receipts.set(actionId, {
      input: structuredClone(input),
      response,
      actionKind,
      expectedVersion: input.expectedVersion,
      commandFingerprint: input.commandFingerprint,
    });
    return response;
  }

  const store: ConversationalRectificationServicePorts["store"] = {
    async loadActionReceipt(input) {
      const prior = receipts.get(input.actionId);
      if (!prior?.actionKind) return null;
      if (prior.actionKind !== input.actionKind
        || prior.expectedVersion !== input.expectedVersion
        || prior.commandFingerprint !== input.commandFingerprint) {
        throw new ConversationalRectificationError("action_conflict");
      }
      return prior.response;
    },
    async loadCase(input) {
      const value = input.caseId
        ? cases.get(input.caseId)?.row
        : [...cases.values()].at(-1)?.row;
      return value ?? null;
    },
    async createCaseWithFirstTurn(input) {
      events.push("create");
      mutations.push("create");
      if (options.createFailure) throw options.createFailure;
      return replay(input.actionId, input, () => {
        const row = stored({
          userId: input.userId,
          caseId: input.caseId,
          turn: input.firstTurn,
          privateCandidate: input.privateCandidate,
          receipts: [input.validationReceipt],
          revisionOfCaseId: input.revisionOfCaseId,
        });
        cases.set(input.caseId, { row });
        return row;
      });
    },
    async saveTurn(input) {
      mutations.push("saveTurn");
      return replay(input.actionId, input, () => {
        const current = cases.get(input.turn.caseId)?.row;
        assert.ok(current);
        if (current.turnVersion !== input.expectedVersion) throw new ConversationalRectificationError("stale_turn");
        const row = stored({
          userId: input.userId,
          caseId: input.turn.caseId,
          turn: input.turn,
          privateCandidate: input.privateCandidate,
          evidence: [...current.eventEvidence, ...input.evidence],
          receipts: [...current.validationReceipts, input.validationReceipt],
          revisionOfCaseId: current.revisionOfCaseId,
        });
        cases.set(input.turn.caseId, { row });
        return row;
      }, "save_turn");
    },
    async pause(input) {
      mutations.push("pause");
      return replay(input.actionId, input, () => {
        const current = cases.get(input.turn.caseId)?.row;
        assert.ok(current);
        if (current.turnVersion !== input.expectedVersion) throw new ConversationalRectificationError("stale_turn");
        const row = stored({ ...current, userId: input.userId, caseId: input.turn.caseId, turn: input.turn,
          receipts: [...current.validationReceipts, input.validationReceipt] });
        cases.set(input.turn.caseId, { row });
        return row;
      }, "pause");
    },
    async abandon(input) {
      mutations.push("abandon");
      return replay(input.actionId, input, () => {
        const current = cases.get(input.turn.caseId)?.row;
        assert.ok(current);
        const row = stored({ ...current, userId: input.userId, caseId: input.turn.caseId, turn: input.turn,
          receipts: [...current.validationReceipts, input.validationReceipt] });
        cases.set(input.turn.caseId, { row });
        return row;
      }, "abandon");
    },
    async confirm(input) {
      mutations.push("confirm");
      return replay(input.actionId, input, () => {
        const current = cases.get(input.turn.caseId)?.row;
        assert.ok(current);
        const row = stored({ ...current, userId: input.userId, caseId: input.turn.caseId, turn: input.turn,
          receipts: [...current.validationReceipts, input.validationReceipt] });
        cases.set(input.turn.caseId, { row });
        return row;
      }, "confirm");
    },
  };

  const ports: ConversationalRectificationServicePorts = {
    get rectificationPriceCredits() {
      events.push("price");
      return 9;
    },
    store,
    billing: {
      async reserve(input) {
        reserveCount += 1;
        events.push(`reserve:${input.price}`);
        updateBillingState("reserved");
        return { success: true, credits: 91, billingState: "reserved" };
      },
      async complete() {
        events.push("complete");
        if (remainingCompleteFailures > 0) {
          remainingCompleteFailures -= 1;
          throw new Error("complete response unavailable");
        }
        updateBillingState("charged");
        return { success: true, credits: 91, billingState: "charged" };
      },
      async release() {
        releaseCount += 1;
        events.push("release");
        if (options.releaseFailure) throw new Error("release SQL detail");
        updateBillingState("released");
        return { success: true, credits: 100, billingState: "released" };
      },
    },
    async loadDeclaredProfile() {
      events.push("profile");
      return { declaredBirthInput, revisionOfCaseId: priorCaseId };
    },
    async buildTechnicalPacket(input) {
      packetBuilds += 1;
      packetEvidenceCounts.push(input.evidence.length);
      packetEvidenceIds.push(input.evidence.map((item) => item.id));
      packetPrivateCandidates.push(input.privateCandidate
        ? {
            rangeStart: input.privateCandidate.rangeStart,
            rangeEnd: input.privateCandidate.rangeEnd,
            resultId: input.privateCandidate.resultId,
          }
        : null);
      events.push(input.evidence.length > 0 ? "score-packet" : "packet");
      if (options.packetFailure
        && (options.packetFailureFromBuild === undefined
          || packetBuilds >= options.packetFailureFromBuild)) throw options.packetFailure;
      const selectedPacket = options.packetForEvidenceCount?.(input.evidence.length)
        ?? packet(input.evidence.length >= (options.readyAfterEvidenceCount ?? 1));
      return {
        packet: selectedPacket,
        resultId: selectedPacket.candidate.status === "ready_for_confirmation" ? resultId : null,
      };
    },
    narrativeGenerator: validGenerator(
      events,
      options.varyNarrative,
      options.invalidNarrativeFromGeneration,
      narrativePrompts,
      options.continueLatestEvent,
      options.detailQuestion,
      options.mislabelLatestDetailAsNewEvent,
      options.classifyEvidenceDomain,
    ),
    asOfDate: () => "2026-07-21",
  };

  return {
    events,
    narrativePrompts,
    mutations,
    packetEvidenceCounts,
    packetEvidenceIds,
    packetPrivateCandidates,
    cases,
    service: createConversationalRectificationService(ports),
    counts: () => ({ packetBuilds, reserveCount, releaseCount }),
    forceLaterVersion(caseId: string, turnVersion: number) {
      const current = cases.get(caseId)?.row;
      assert.ok(current);
      cases.set(caseId, {
        row: {
          ...current,
          status: "active",
          turnVersion,
          latestTurn: conversationalRectificationTurnSchema.parse({
            ...current.latestTurn,
            status: "active",
            turnVersion,
            candidate: current.latestTurn.candidate.status === "confirmed"
              ? { ...current.latestTurn.candidate, status: "pending_validation" }
              : current.latestTurn.candidate,
            actions: ["answer", "pause", "abandon"],
          }),
        },
      });
    },
  };
}

async function start(value: ReturnType<typeof harness>, pendingConsultationQuestion: string | null = "我的工作何时变化？") {
  return value.service.start(userId, {
    type: "start",
    actionId: startActionId,
    pendingConsultationQuestion,
  });
}

test("start creates a deterministic opening without scanning or narrative generation", async () => {
  const value = harness();
  const turn = await start(value);

  assert.deepEqual(value.events, ["profile", "price", "reserve:9", "create", "complete"]);
  assert.equal(value.counts().packetBuilds, 0);
  assert.equal(turn.caseId, startActionId);
  assert.equal(turn.turnVersion, 0);
  assert.equal(turn.pendingConsultationQuestion, "我的工作何时变化？");
  assert.equal(turn.candidate.status, "pending_validation");
  assert.equal(turn.candidate.representativeTime, "05:20");
  assert.equal(turn.candidate.rangeStart, "04:50");
  assert.equal(turn.candidate.rangeEnd, "05:50");
  assert.match(turn.narrative, /当前先核对 04:50–05:50/);
  assert.match(turn.narrative, /还不能把其中某一分钟当作已确认出生时间/);
  assert.match(turn.narrative, /请先说一件/);
  assert.deepEqual(turn.technicalReceipt, {
    calculationVersion: "rectification-opening-v1",
    stableLayers: [],
    sensitiveLayers: [],
    candidateDifferenceRefs: [],
  });
  assert.equal(turn.evidenceRequest?.followUp?.kind, "new_event");
  assert.equal(JSON.stringify(turn).includes("candidateWeights"), false);
  assert.equal(value.cases.get(startActionId)?.row.revisionOfCaseId, priorCaseId);
  assert.equal(value.cases.get(startActionId)?.row.baselineActiveTime, "04:58");
  assert.equal(value.cases.get(startActionId)?.row.validationReceipts[0]?.modelId, "deterministic-rectification-opening");
});

test("start rejects a client price before profile, billing, or calculation", async () => {
  const value = harness();
  await assert.rejects(value.service.start(userId, {
    type: "start", actionId: startActionId, price: 0,
  } as never), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "invalid_command");
  assert.deepEqual(value.events, []);
});

test("every post-reservation failure releases exactly once and never leaks its cause", async () => {
  const raw = "SQL model browser secret detail";
  const value = harness({ createFailure: new Error(raw) });
  await assert.rejects(start(value), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "service_unavailable" && !error.message.includes(raw));
  assert.equal(value.counts().releaseCount, 1);
  assert.deepEqual(value.events, ["profile", "price", "reserve:9", "create", "release"]);
});

test("a start retry settles an existing reservation without reserving or computing again", async () => {
  const value = harness({ completeFailures: 1, releaseFailure: true });
  await assert.rejects(start(value), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "billing_failed");
  assert.equal(value.cases.get(startActionId)?.row.billingState, "reserved");

  const replayed = await start(value);

  assert.equal(replayed.status, "active");
  assert.equal(value.cases.get(startActionId)?.row.billingState, "charged");
  assert.deepEqual(value.counts(), { packetBuilds: 0, reserveCount: 1, releaseCount: 1 });
  assert.deepEqual(value.events.slice(-3), ["profile", "price", "complete"]);
});

test("a duplicate start with the same declared birth input reuses the unfinished case", async () => {
  const value = harness();
  const first = await start(value, null);
  const countsBeforeRetry = value.counts();

  const replayed = await value.service.start(userId, {
    type: "start",
    actionId: secondStartActionId,
    pendingConsultationQuestion: null,
  });

  assert.deepEqual(replayed, first);
  assert.deepEqual(value.counts(), countsBeforeRetry);
  assert.deepEqual(value.events, [
    "profile", "price", "reserve:9", "create", "complete",
    "profile", "price",
  ]);
});

test("a duplicate start with changed declared birth input remains a conflict", async () => {
  const value = harness();
  await start(value, null);

  const current = value.cases.get(startActionId)?.row;
  assert.ok(current);
  value.cases.set(startActionId, {
    row: {
      ...current,
      declaredBirthInput: {
        ...current.declaredBirthInput,
        birthDate: "2000-01-02",
      },
    },
  });
  await assert.rejects(value.service.start(userId, {
    type: "start",
    actionId: secondStartActionId,
    pendingConsultationQuestion: null,
  }), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "action_conflict");
  assert.equal(value.counts().reserveCount, 1);
  assert.equal(value.counts().packetBuilds, 0);
});

test("a settlement failure releases its created case once and cannot replay as success", async () => {
  const value = harness({ completeFailures: 1 });
  await assert.rejects(start(value), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "service_unavailable");
  assert.equal(value.cases.get(startActionId)?.row.billingState, "released");
  assert.deepEqual(value.events.slice(-3), ["create", "complete", "release"]);

  await assert.rejects(start(value), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "billing_failed");
  assert.deepEqual(value.counts(), { packetBuilds: 0, reserveCount: 1, releaseCount: 1 });
});

test("clear historical evidence is extracted, scored, narrated, recapped, and atomically saved", async () => {
  const value = harness();
  await start(value);
  const turn = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2018年6月毕业，2019年7月开始第一份工作，2020年3月去外地工作，2022年8月结婚",
  });

  assert.equal(value.counts().packetBuilds, 1);
  assert.equal(turn.status, "confirming");
  assert.equal(turn.candidate.status, "ready_for_confirmation");
  assert.equal(turn.turnVersion, 1);
  assert.equal(turn.evidenceRecap.length, 4);
  const saved = value.cases.get(startActionId)?.row.eventEvidence ?? [];
  assert.equal(saved.length, 4);
  assert.ok(saved.every((item) => item.rawText === "2018年6月毕业，2019年7月开始第一份工作，2020年3月去外地工作，2022年8月结婚"));
  assert.ok(saved.every((item) => item.scoreable === true));
  assert.ok(value.events.includes("score-packet"));
});

test("evidence corrections are append-only while recap and scoring use only the effective lineage tip", async () => {
  const value = harness({ readyAfterEvidenceCount: 99 });
  await start(value, null);
  await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2019年7月开始第一份工作",
  });
  const firstId = value.cases.get(startActionId)?.row.eventEvidence[0]?.id;
  assert.ok(firstId);

  const corrected = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: secondAnswerActionId,
    turnVersion: 1,
    answer: "更正：其实是2020年11月离职",
    correctsEvidenceId: firstId,
  });
  const secondId = value.cases.get(startActionId)?.row.eventEvidence[1]?.id;
  assert.ok(secondId);
  assert.deepEqual(corrected.evidenceRecap, [{
    id: secondId,
    summary: "其实是离职",
    dateLabel: "2020-11",
    domain: "career",
    isCorrection: true,
  }]);

  const twiceCorrected = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: thirdAnswerActionId,
    turnVersion: 2,
    answer: "更正：准确的是2021年2月入职",
    correctsEvidenceId: secondId,
  });

  const stored = value.cases.get(startActionId)?.row.eventEvidence ?? [];
  assert.equal(stored.length, 3, "the audit lineage must remain append-only");
  assert.deepEqual(stored[0]?.correctsEvidenceIds ?? [], []);
  assert.deepEqual(stored[1]?.correctsEvidenceIds, [firstId]);
  assert.deepEqual(stored[2]?.correctsEvidenceIds, [secondId]);
  assert.deepEqual(twiceCorrected.evidenceRecap, [{
    id: stored[2]?.id,
    summary: "准确的是入职",
    dateLabel: "2021-02",
    domain: "career",
    isCorrection: true,
  }]);
  assert.deepEqual(value.packetEvidenceCounts, [1, 1, 1]);
});

test("uses Agent semantic classification when a single event falls through the deterministic keywords", async () => {
  const classifiedTexts: string[] = [];
  const value = harness({
    readyAfterEvidenceCount: 99,
    classifyEvidenceDomain(text) {
      classifiedTexts.push(text);
      return "career";
    },
  });
  await start(value, null);

  await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2020年4月去石油化工研究院实习做研究员",
  });

  assert.deepEqual(classifiedTexts, ["2020年4月去石油化工研究院实习做研究员"]);
  const saved = value.cases.get(startActionId)?.row.eventEvidence.at(-1);
  assert.equal(saved?.dateValue, "2020-04");
  assert.equal(saved?.domain, "career");
  assert.equal(saved?.scoreable, true);
});

test("repeated evidence remains auditable but identical date-domain-semantics score only once", async () => {
  const value = harness({ readyAfterEvidenceCount: 2 });
  await start(value, null);
  await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: answerActionId,
    turnVersion: 0, answer: "2019年7月开始第一份工作",
  });
  const firstId = value.cases.get(startActionId)?.row.eventEvidence[0]?.id;
  assert.ok(firstId);

  const repeated = await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: secondAnswerActionId,
    turnVersion: 1, answer: "2019年7月开始第一份工作",
  });

  const stored = value.cases.get(startActionId)?.row.eventEvidence ?? [];
  assert.equal(stored.length, 2, "both user submissions remain in the audit ledger");
  assert.equal(repeated.evidenceRecap.length, 2);
  assert.deepEqual(value.packetEvidenceCounts, [1, 1]);
  assert.deepEqual(value.packetEvidenceIds.at(-1), [firstId]);
  assert.equal(repeated.status, "active");
  assert.equal(repeated.actions.includes("confirm"), false);
});

test("an unclear correction immediately retires the wrong fact and stays retired after later turns", async () => {
  const value = harness();
  await start(value, null);
  await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: answerActionId,
    turnVersion: 0, answer: "2019年7月开始第一份工作",
  });
  const wrongId = value.cases.get(startActionId)?.row.eventEvidence[0]?.id;
  assert.ok(wrongId);

  const clarification = await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: secondAnswerActionId,
    turnVersion: 1, answer: "更正：具体年月记不清", correctsEvidenceId: wrongId,
  });
  const unclear = value.cases.get(startActionId)?.row.eventEvidence[1];
  assert.equal(unclear?.extractionStatus, "needs_clarification");
  assert.equal(unclear?.scoreable, false);
  assert.deepEqual(unclear?.correctsEvidenceIds, [wrongId]);
  assert.deepEqual(clarification.evidenceRecap, [{
    id: unclear?.id,
    summary: "具体年月记不清",
    dateLabel: "日期待补充",
    domain: "other",
    isCorrection: true,
  }]);
  assert.equal(clarification.status, "active");
  assert.equal(clarification.candidate.status, "pending_validation");
  assert.equal(clarification.actions.includes("confirm"), false);
  assert.equal(value.cases.get(startActionId)?.row.privateCandidate.resultId, null);
  assert.deepEqual(
    value.cases.get(startActionId)?.row.privateCandidate.scoredHistoricalEvidence ?? [],
    [],
  );
  assert.deepEqual(value.packetEvidenceCounts, [1, 0]);

  const later = await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: thirdAnswerActionId,
    turnVersion: 2, answer: "2022年3月搬家",
  });
  assert.deepEqual(value.packetEvidenceCounts, [1, 0, 1]);
  assert.equal(later.evidenceRecap.some((item) => item.id === wrongId), false);
  assert.equal(later.evidenceRecap.some((item) => item.id === unclear?.id), true);
});

test("every non-confirmable correction rescans the declared range and withdraws the old candidate", async () => {
  const scenarios = [
    { name: "unclear", answer: "更正：具体年月记不清" },
    { name: "future", answer: "更正：2099年3月开始新工作" },
    { name: "direction change", answer: "更正：这些都不符合" },
  ] as const;

  for (const scenario of scenarios) {
    const value = harness();
    await start(value, null);
    const prior = await value.service.answer(userId, {
      type: "answer",
      caseId: startActionId,
      actionId: answerActionId,
      turnVersion: 0,
      answer: "2018年6月毕业，2019年7月开始第一份工作，2021年3月搬家，2022年8月结婚",
    });
    assert.equal(prior.status, "confirming", scenario.name);
    const wrongId = value.cases.get(startActionId)?.row.eventEvidence[0]?.id;
    assert.ok(wrongId, scenario.name);
    const buildsBeforeCorrection = value.counts().packetBuilds;

    const corrected = await value.service.answer(userId, {
      type: "answer",
      caseId: startActionId,
      actionId: secondAnswerActionId,
      turnVersion: 1,
      answer: scenario.answer,
      correctsEvidenceId: wrongId,
    });

    const stored = value.cases.get(startActionId)?.row;
    const replacement = stored?.eventEvidence.at(-1);
    assert.ok(stored && replacement, scenario.name);
    assert.equal(value.counts().packetBuilds, buildsBeforeCorrection + 1, scenario.name);
    assert.equal(value.packetPrivateCandidates.at(-1), null, scenario.name);
    assert.equal(value.packetEvidenceIds.at(-1)?.includes(wrongId), false, scenario.name);
    assert.equal(corrected.status, "active", scenario.name);
    assert.equal(corrected.candidate.status, "pending_validation", scenario.name);
    assert.equal(corrected.actions.includes("confirm"), false, scenario.name);
    assert.equal(stored.privateCandidate.resultId ?? null, null, scenario.name);
    assert.equal(stored.privateCandidate.workingState?.phase, "collecting_evidence", scenario.name);
    assert.equal(corrected.evidenceRecap.some((item) => item.id === wrongId), false, scenario.name);
    assert.equal(corrected.evidenceRecap.some((item) => item.id === replacement.id), true, scenario.name);
    assert.equal(value.counts().reserveCount, 1, scenario.name);

    const expectedPacketEvidenceIds = stored.eventEvidence
      .filter((item) => item.id !== wrongId
        && item.scoreable === true
        && item.extractionStatus !== "needs_clarification")
      .map((item) => item.id);
    assert.deepEqual(value.packetEvidenceIds.at(-1), expectedPacketEvidenceIds);
  }
});

test("a narrative fallback cannot discard a confirmation candidate produced by a valid correction", async () => {
  const value = harness({ invalidNarrativeFromGeneration: 2 });
  await start(value, null);
  await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: answerActionId,
    turnVersion: 0, answer: "2018年6月毕业，2019年7月开始第一份工作，2021年3月搬家，2022年8月结婚",
  });
  const wrongId = value.cases.get(startActionId)?.row.eventEvidence[0]?.id;
  assert.ok(wrongId);

  const corrected = await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: secondAnswerActionId,
    turnVersion: 1, answer: "更正：其实是2020年11月离职", correctsEvidenceId: wrongId,
  });
  const stored = value.cases.get(startActionId)?.row;
  assert.ok(stored);
  assert.equal(stored.validationReceipts.at(-1)?.fallbackUsed, true);
  assert.equal(corrected.status, "confirming");
  assert.equal(corrected.candidate.status, "ready_for_confirmation");
  assert.equal(stored.privateCandidate.resultId, resultId);
  assert.equal(stored.privateCandidate.workingState?.phase, "ready");

  const confirmed = await value.service.confirm(userId, {
    type: "confirm", caseId: startActionId, actionId: confirmActionId,
    turnVersion: corrected.turnVersion, time: "05:18",
  });
  assert.equal(confirmed.status, "completed");
  assert.equal(value.mutations.at(-1), "confirm");
});

test("a clear one-to-one correction can form a new confirmation candidate only after a declared-range rescan", async () => {
  const value = harness();
  await start(value, null);
  await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: answerActionId,
    turnVersion: 0, answer: "2018年6月毕业，2019年7月开始第一份工作，2021年3月搬家，2022年8月结婚",
  });
  const wrongId = value.cases.get(startActionId)?.row.eventEvidence[0]?.id;
  assert.ok(wrongId);

  const corrected = await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: secondAnswerActionId,
    turnVersion: 1, answer: "更正：其实是2020年11月离职",
    correctsEvidenceId: wrongId,
  });
  const stored = value.cases.get(startActionId)?.row;
  const replacementId = stored?.eventEvidence.at(-1)?.id;
  assert.ok(stored && replacementId);

  assert.equal(value.packetPrivateCandidates.at(-1), null);
  assert.deepEqual(
    value.packetEvidenceIds.at(-1),
    stored.eventEvidence
      .filter((item) => item.id !== wrongId
        && item.scoreable === true
        && item.extractionStatus !== "needs_clarification")
      .map((item) => item.id),
  );
  assert.equal(corrected.status, "confirming");
  assert.equal(corrected.candidate.status, "ready_for_confirmation");
  assert.equal(corrected.actions.includes("confirm"), true);
  assert.equal(stored.privateCandidate.resultId, resultId);
});

test("a targeted correction must extract exactly one replacement before scoring or persistence", async () => {
  const value = harness({ readyAfterEvidenceCount: 99 });
  await start(value, null);
  await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: answerActionId,
    turnVersion: 0, answer: "2019年7月开始第一份工作",
  });
  const wrongId = value.cases.get(startActionId)?.row.eventEvidence[0]?.id;
  assert.ok(wrongId);
  const before = {
    builds: value.counts().packetBuilds,
    mutations: [...value.mutations],
    version: value.cases.get(startActionId)?.row.turnVersion,
    evidenceCount: value.cases.get(startActionId)?.row.eventEvidence.length,
  };

  await assert.rejects(value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: secondAnswerActionId,
    turnVersion: 1,
    answer: "更正：2020年11月离职，并在2021年2月入职",
    correctsEvidenceId: wrongId,
  }), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "invalid_command");

  assert.equal(value.counts().packetBuilds, before.builds);
  assert.deepEqual(value.mutations, before.mutations);
  assert.equal(value.cases.get(startActionId)?.row.turnVersion, before.version);
  assert.equal(value.cases.get(startActionId)?.row.eventEvidence.length, before.evidenceCount);
});

test("ordinary new evidence continues incrementally from the current candidate range", async () => {
  const value = harness();
  await start(value, null);
  await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: answerActionId,
    turnVersion: 0, answer: "2019年7月开始第一份工作",
  });
  await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: secondAnswerActionId,
    turnVersion: 1, answer: "2020年11月搬家",
  });

  assert.deepEqual(value.packetPrivateCandidates, [
    { rangeStart: "04:50", rangeEnd: "05:50", resultId: null },
    { rangeStart: "05:16", rangeEnd: "05:20", resultId: null },
  ]);
});

test("missing or already-retired correction targets fail closed without advancing or persisting", async () => {
  const value = harness({ readyAfterEvidenceCount: 99 });
  await start(value, null);
  const before = [...value.mutations];
  await assert.rejects(value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: answerActionId,
    turnVersion: 0, answer: "更正：2020年11月离职",
    correctsEvidenceId: "00000000-0000-4000-8000-000000000799",
  }), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "action_conflict");
  assert.deepEqual(value.mutations, before);
  assert.equal(value.cases.get(startActionId)?.row.turnVersion, 0);
  assert.equal(value.cases.get(startActionId)?.row.eventEvidence.length, 0);

  await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: secondAnswerActionId,
    turnVersion: 0, answer: "2019年7月开始第一份工作",
  });
  const firstId = value.cases.get(startActionId)?.row.eventEvidence[0]?.id;
  assert.ok(firstId);
  await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: thirdAnswerActionId,
    turnVersion: 1, answer: "更正：2020年11月离职", correctsEvidenceId: firstId,
  });
  const versionBeforeConflict = value.cases.get(startActionId)?.row.turnVersion;
  const evidenceBeforeConflict = value.cases.get(startActionId)?.row.eventEvidence.length;
  await assert.rejects(value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: fourthAnswerActionId,
    turnVersion: 2, answer: "再次覆盖旧错误：2021年2月入职", correctsEvidenceId: firstId,
  }), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "action_conflict");
  assert.equal(value.cases.get(startActionId)?.row.turnVersion, versionBeforeConflict);
  assert.equal(value.cases.get(startActionId)?.row.eventEvidence.length, evidenceBeforeConflict);
});

test("generic date uncertainty does not suppress clear historical evidence", async () => {
  const value = harness();
  await start(value, null);

  const turn = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2021年7月毕业，具体日期不确定",
  });

  assert.equal(turn.status, "active");
  assert.equal(turn.candidate.status, "pending_validation");
  assert.equal(value.counts().packetBuilds, 1);
  assert.ok(value.events.includes("score-packet"));
  assert.ok((value.cases.get(startActionId)?.row.eventEvidence ?? [])
    .some((item) => item.eventSummary.includes("毕业") && item.scoreable === true));
});

test("a concrete event without a date is acknowledged and a date-only follow-up completes it", async () => {
  const value = harness({ readyAfterEvidenceCount: 99 });
  await start(value, null);

  const clarification = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "我离开家去北京开始工作",
  });

  assert.match(clarification.narrative, /离开家去北京开始工作/);
  assert.match(clarification.narrative, /哪一年、哪一月/);
  assert.doesNotMatch(
    clarification.narrative,
    /你提到.*具体内容我已经记下了|只记得年份也可以/,
  );
  assert.equal(clarification.evidenceRecap.at(-1)?.dateLabel, "日期待补充");

  const completed = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: secondAnswerActionId,
    turnVersion: 1,
    answer: "2023年3月",
  });

  const stored = value.cases.get(startActionId)?.row.eventEvidence ?? [];
  assert.equal(stored.length, 2, "the incomplete fact and its completion remain auditable");
  assert.deepEqual(stored[1]?.correctsEvidenceIds, [stored[0]?.id]);
  assert.equal(stored[1]?.eventSummary, "我离开家去北京开始工作");
  assert.equal(stored[1]?.dateValue, "2023-03");
  assert.equal(stored[1]?.scoreable, true);
  assert.deepEqual(completed.evidenceRecap.map((item) => ({
    summary: item.summary,
    dateLabel: item.dateLabel,
  })), [{ summary: "我离开家去北京开始工作", dateLabel: "2023-03" }]);
  assert.match(completed.narrative, /记下了：2023-03 · 我离开家去北京开始工作/);
});

test("a descriptive date follow-up completes the targeted event instead of becoming a new event", async () => {
  const value = harness({ readyAfterEvidenceCount: 99 });
  await start(value, null);

  await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "我彻底离开了学校",
  });

  const completed = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: secondAnswerActionId,
    turnVersion: 1,
    answer: "2023年1月我正式办完了手续",
  });

  const stored = value.cases.get(startActionId)?.row.eventEvidence ?? [];
  assert.equal(stored.length, 2, "the original answer and its completion remain auditable");
  assert.deepEqual(stored[1]?.correctsEvidenceIds, [stored[0]?.id]);
  assert.equal(stored[1]?.dateValue, "2023-01");
  assert.equal(stored[1]?.eventSummary, "我彻底离开了学校");
  assert.equal(stored[1]?.rawText, "我彻底离开了学校\n补充：2023年1月我正式办完了手续");
  assert.equal(completed.evidenceRecap.length, 1);
  assert.doesNotMatch(completed.narrative, /还差时间定位/);
});

test("an independent future event does not get swallowed as the date of an unresolved historical event", async () => {
  const value = harness({ readyAfterEvidenceCount: 99 });
  await start(value, null);

  await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "后来工作压力很大",
  });

  const completed = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: secondAnswerActionId,
    turnVersion: 1,
    answer: "2027年计划换工作",
  });

  const stored = value.cases.get(startActionId)?.row.eventEvidence ?? [];
  assert.equal(stored.length, 2);
  assert.equal(stored[0]?.dateValue, null);
  assert.deepEqual(stored[1]?.correctsEvidenceIds, []);
  assert.equal(stored[1]?.dateValue, "2027");
  assert.equal(stored[1]?.scoreable, false);
  assert.deepEqual(completed.evidenceRecap.map((item) => item.dateLabel), [
    "日期待补充",
    "2027（未来，仅作背景）",
  ]);
});

test("a next-year month answer resolves from the event being discussed", async () => {
  const value = harness({ readyAfterEvidenceCount: 99, continueLatestEvent: true });
  await start(value, null);

  const first = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2022年12月正式退学",
  });
  assert.equal(first.evidenceRequest?.followUp?.kind, "event_detail");

  const completed = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: secondAnswerActionId,
    turnVersion: 1,
    answer: "来年 1 月份我彻底离开的学校",
  });

  const stored = value.cases.get(startActionId)?.row.eventEvidence ?? [];
  assert.deepEqual(stored.map((item) => item.dateValue), ["2022-12", "2023-01"]);
  assert.equal(stored[1]?.rawText, "来年 1 月份我彻底离开的学校");
  assert.equal(stored[1]?.scoreable, true);
  assert.doesNotMatch(completed.narrative, /还差时间定位|大约是哪一年、哪一月/);
});

test("a bare month-day answer refines the targeted month without another confirmation", async () => {
  const value = harness({ readyAfterEvidenceCount: 99, continueLatestEvent: true });
  await start(value, null);

  await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2026年7月我们三个人决定一起开公司",
  });

  const current = value.cases.get(startActionId)?.row;
  const target = current?.eventEvidence.at(-1);
  assert.ok(current);
  assert.ok(target);
  assert.ok(current.latestTurn.evidenceRequest);
  value.cases.set(startActionId, {
    row: {
      ...current,
      latestTurn: {
        ...current.latestTurn,
        evidenceRequest: {
          ...current.latestTurn.evidenceRequest,
          followUp: { kind: "event_date", evidenceId: target.id },
        },
      },
    },
  });

  const completed = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: secondAnswerActionId,
    turnVersion: 1,
    answer: "7 月 10 号",
  });

  const stored = value.cases.get(startActionId)?.row.eventEvidence ?? [];
  assert.equal(stored.length, 2, "the month event and day refinement remain auditable");
  assert.deepEqual(stored[1]?.correctsEvidenceIds, [target.id]);
  assert.equal(stored[1]?.dateValue, "2026-07-10");
  assert.equal(stored[1]?.eventSummary, "我们三个人决定一起开公司");
  assert.equal(stored[1]?.rawText, "2026年7月我们三个人决定一起开公司\n补充：7 月 10 号");
  assert.equal(completed.evidenceRecap.at(-1)?.dateLabel, "2026-07-10");
  assert.doesNotMatch(completed.narrative, /是指.*7 月 10|哪一天|哪一年、哪一月/);
});

async function preparedDateConfirmation() {
  const value = harness({ readyAfterEvidenceCount: 99 });
  await start(value, null);
  await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2020年我去石油化工研究院实习，后来主动辞职",
  });
  const current = value.cases.get(startActionId)?.row;
  const target = current?.eventEvidence.at(-1);
  assert.ok(current);
  assert.ok(target);
  value.cases.set(startActionId, {
    row: {
      ...current,
      latestTurn: {
        ...current.latestTurn,
        narrative: "这个10月是2020年10月吗？",
        evidenceRequest: {
          domains: ["career"],
          datePrecision: "month_preferred",
          freeTextAllowed: true,
          prompt: "这个10月是2020年10月吗？",
          followUp: {
            kind: "event_date",
            evidenceId: target.id,
            answerMode: "yes_no",
            proposedDate: { value: "2020-10", precision: "month" },
          },
        },
      },
    },
  });
  return { value, target, initialEvidenceCount: current.eventEvidence.length };
}

test("all supported affirmative tokens confirm the structured proposed date", async () => {
  for (const answer of ["对", "没错", "嗯", "确认"]) {
    const { value, target, initialEvidenceCount } = await preparedDateConfirmation();
    await value.service.answer(userId, {
      type: "answer",
      caseId: startActionId,
      actionId: secondAnswerActionId,
      turnVersion: 1,
      answer,
    });

    const stored = value.cases.get(startActionId)?.row.eventEvidence ?? [];
    assert.equal(stored.length, initialEvidenceCount + 1, answer);
    assert.equal(stored.at(-1)?.dateValue, "2020-10", answer);
    assert.deepEqual(stored.at(-1)?.correctsEvidenceIds, [target.id], answer);
  }
});

test("the alternate negative token rejects the proposal without creating evidence", async () => {
  const { value, target, initialEvidenceCount } = await preparedDateConfirmation();
  const completed = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: secondAnswerActionId,
    turnVersion: 1,
    answer: "不对",
  });

  assert.equal(value.cases.get(startActionId)?.row.eventEvidence.length, initialEvidenceCount);
  assert.deepEqual(completed.evidenceRequest?.followUp, {
    kind: "event_date",
    evidenceId: target.id,
    answerMode: "free_text",
    proposedDate: null,
  });
});

test("an affirmative reply confirms the date proposed by the previous Agent turn", async () => {
  const value = harness({ readyAfterEvidenceCount: 99 });
  await start(value, null);

  await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2020年我去石油化工研究院实习，后来主动辞职",
  });

  const current = value.cases.get(startActionId)?.row;
  const target = current?.eventEvidence.at(-1);
  const initialEvidenceCount = current?.eventEvidence.length ?? 0;
  assert.ok(current);
  assert.ok(target);
  value.cases.set(startActionId, {
    row: {
      ...current,
      latestTurn: {
        ...current.latestTurn,
        narrative: "你说实习到10月份然后辞职，这个10月是2020年10月吗？",
        evidenceRequest: {
          domains: ["career"],
          datePrecision: "month_preferred",
          freeTextAllowed: true,
          prompt: "这个10月是2020年10月吗？",
          followUp: {
            kind: "event_date",
            evidenceId: target.id,
            answerMode: "yes_no",
            proposedDate: { value: "2020-10", precision: "month" },
          },
        },
      },
    },
  });

  const completed = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: secondAnswerActionId,
    turnVersion: 1,
    answer: "是的",
  });

  const stored = value.cases.get(startActionId)?.row.eventEvidence ?? [];
  assert.equal(stored.length, initialEvidenceCount + 1, "confirmation is an auditable correction, not a standalone event");
  assert.deepEqual(stored.at(-1)?.correctsEvidenceIds, [target.id]);
  assert.equal(stored.at(-1)?.dateValue, "2020-10");
  assert.doesNotMatch(stored.at(-1)?.eventSummary ?? "", /^是的$/);
  assert.doesNotMatch(completed.narrative, /这个10月是2020年10月吗/);
  assert.notEqual(completed.evidenceRequest?.followUp?.evidenceId, target.id);

  const prompt = JSON.parse(value.narrativePrompts.at(-1) ?? "{}") as {
    conversationContext?: {
      recentConversation?: Array<{ role: string; text: string }>;
      previousEvidencePrompt?: string;
      previousFollowUp?: { answerMode?: string; proposedDate?: { value: string } };
    };
  };
  assert.deepEqual(prompt.conversationContext?.recentConversation?.slice(-2), [
    { role: "assistant", text: "你说实习到10月份然后辞职，这个10月是2020年10月吗？" },
    { role: "user", text: "是的" },
  ]);
  assert.equal(prompt.conversationContext?.previousEvidencePrompt, "这个10月是2020年10月吗？");
  assert.equal(prompt.conversationContext?.previousFollowUp?.answerMode, "yes_no");
  assert.equal(prompt.conversationContext?.previousFollowUp?.proposedDate?.value, "2020-10");

  await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: secondAnswerActionId,
    turnVersion: 1,
    answer: "是的",
  });
  assert.equal(
    value.cases.get(startActionId)?.row.eventEvidence.length,
    initialEvidenceCount + 1,
    "replaying the same action does not duplicate the correction",
  );
});

test("a rejected proposed date stays on the same event and switches to free text", async () => {
  const value = harness({ readyAfterEvidenceCount: 99 });
  await start(value, null);
  await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "我去石油化工研究院实习到10月，后来主动辞职",
  });

  const current = value.cases.get(startActionId)?.row;
  const target = current?.eventEvidence.at(-1);
  assert.ok(current);
  assert.ok(target);
  value.cases.set(startActionId, {
    row: {
      ...current,
      latestTurn: {
        ...current.latestTurn,
        narrative: "这个10月是2020年10月吗？",
        evidenceRequest: {
          domains: ["career"],
          datePrecision: "month_preferred",
          freeTextAllowed: true,
          prompt: "这个10月是2020年10月吗？",
          followUp: {
            kind: "event_date",
            evidenceId: target.id,
            answerMode: "yes_no",
            proposedDate: { value: "2020-10", precision: "month" },
          },
        },
      },
    },
  });

  const resumed = await value.service.resume(userId, {
    type: "resume",
    caseId: startActionId,
    actionId: resumeActionId,
    turnVersion: 1,
  });
  assert.equal(resumed.evidenceRequest?.followUp?.proposedDate?.value, "2020-10");

  const beforeCount = current.eventEvidence.length;
  const completed = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: secondAnswerActionId,
    turnVersion: 1,
    answer: "不是",
  });

  assert.equal(value.cases.get(startActionId)?.row.eventEvidence.length, beforeCount);
  assert.deepEqual(completed.evidenceRequest?.followUp, {
    kind: "event_date",
    evidenceId: target.id,
    answerMode: "free_text",
    proposedDate: null,
  });
  assert.doesNotMatch(completed.narrative, /这个10月是2020年10月吗/);
});

test("an explicit correction after rejecting a proposed date uses the supplied date", async () => {
  const value = harness({ readyAfterEvidenceCount: 99 });
  await start(value, null);
  await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "我去石油化工研究院实习到10月，后来主动辞职",
  });

  const current = value.cases.get(startActionId)?.row;
  const target = current?.eventEvidence.at(-1);
  assert.ok(current);
  assert.ok(target);
  value.cases.set(startActionId, {
    row: {
      ...current,
      latestTurn: {
        ...current.latestTurn,
        narrative: "这个10月是2020年10月吗？",
        evidenceRequest: {
          domains: ["career"],
          datePrecision: "month_preferred",
          freeTextAllowed: true,
          prompt: "这个10月是2020年10月吗？",
          followUp: {
            kind: "event_date",
            evidenceId: target.id,
            answerMode: "yes_no",
            proposedDate: { value: "2020-10", precision: "month" },
          },
        },
      },
    },
  });

  await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: secondAnswerActionId,
    turnVersion: 1,
    answer: "不是，是2021年10月",
  });

  const stored = value.cases.get(startActionId)?.row.eventEvidence ?? [];
  assert.equal(stored.at(-1)?.dateValue, "2021-10");
  assert.deepEqual(stored.at(-1)?.correctsEvidenceIds, [target.id]);
  assert.doesNotMatch(stored.at(-1)?.eventSummary ?? "", /^不是/);
});

test("an authored event-detail follow-up survives progress decoration and keeps the prior date", async () => {
  const value = harness({ readyAfterEvidenceCount: 99, continueLatestEvent: true });
  await start(value, null);

  const firstAnswer = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2017年5月参加工作",
  });

  const current = value.cases.get(startActionId)?.row;
  const target = current?.eventEvidence.at(-1);
  assert.ok(current);
  assert.ok(target);
  assert.match(firstAnswer.narrative, /正式工作，还是实习或兼职/);
  assert.deepEqual(
    value.cases.get(startActionId)?.row.latestTurn.evidenceRequest?.followUp,
    { kind: "event_detail", evidenceId: target.id },
  );

  const completed = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: secondAnswerActionId,
    turnVersion: 1,
    answer: "正式工作",
  });

  const stored = value.cases.get(startActionId)?.row.eventEvidence ?? [];
  assert.equal(stored.length, 2, "the original event and merged correction remain auditable");
  assert.deepEqual(stored[1]?.correctsEvidenceIds, [target.id]);
  assert.equal(stored[1]?.dateValue, "2017-05");
  assert.equal(stored[1]?.eventSummary, "参加工作；正式工作");
  assert.equal(stored[1]?.scoreable, true);
  assert.equal(completed.evidenceRecap.at(-1)?.dateLabel, "2017-05");
  assert.doesNotMatch(completed.narrative, /大致是什么年月|只记得年份/);
});

test("an unscored event detail mislabeled as new_event is not heuristically merged as a correction", async () => {
  const value = harness({
    readyAfterEvidenceCount: 99,
    continueLatestEvent: true,
    detailQuestion: "这几个月里，学业压力具体体现在哪些方面，主要原因是什么？",
    mislabelLatestDetailAsNewEvent: true,
  });
  await start(value, null);

  const firstAnswer = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "1972年12月因为学业压力正式退学",
  });

  const target = value.cases.get(startActionId)?.row.eventEvidence.at(-1);
  assert.ok(target);
  assert.match(firstAnswer.narrative, /压力具体体现在哪些方面/);
  assert.deepEqual(
    value.cases.get(startActionId)?.row.latestTurn.evidenceRequest?.followUp,
    { kind: "new_event", evidenceId: null },
  );

  const completed = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: secondAnswerActionId,
    turnVersion: 1,
    answer: "经济负担导致无法继续",
  });

  const stored = value.cases.get(startActionId)?.row.eventEvidence ?? [];
  assert.equal(stored.length, 2);
  assert.deepEqual(stored[1]?.correctsEvidenceIds, []);
  assert.equal(stored[1]?.dateValue, null);
  assert.match(stored[1]?.eventSummary ?? "", /经济负担导致无法继续/);
  assert.equal(completed.evidenceRecap.length, 2);
  assert.equal(completed.evidenceRecap.some((item) => item.id === target.id), true);
  assert.doesNotMatch(completed.narrative, /这件事很有用|还差时间定位|大约是哪一年、哪一月/);
});

test("an undated independent event is not swallowed by a broad detail question mislabeled as new_event", async () => {
  const value = harness({
    readyAfterEvidenceCount: 99,
    continueLatestEvent: true,
    detailQuestion: "这几个月里，学业压力具体体现在哪些方面，主要原因是什么？",
    mislabelLatestDetailAsNewEvent: true,
  });
  await start(value, null);
  await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: answerActionId,
    turnVersion: 0, answer: "2017年5月硕士毕业",
  });
  const firstId = value.cases.get(startActionId)?.row.eventEvidence[0]?.id;
  assert.ok(firstId);

  const next = await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: secondAnswerActionId,
    turnVersion: 1, answer: "后来我搬去上海开始工作",
  });

  const stored = value.cases.get(startActionId)?.row.eventEvidence ?? [];
  assert.equal(stored.length, 2);
  assert.deepEqual(stored[1]?.correctsEvidenceIds, []);
  assert.equal(stored[1]?.dateValue, null);
  assert.match(stored[1]?.eventSummary ?? "", /搬去上海开始工作/);
  assert.equal(next.evidenceRecap.some((item) => item.id === firstId), true);
  assert.equal(next.evidenceRecap.at(-1)?.dateLabel, "日期待补充");
});

test("a dated independent event is not swallowed by a broad detail question mislabeled as new_event", async () => {
  const value = harness({
    readyAfterEvidenceCount: 99,
    continueLatestEvent: true,
    detailQuestion: "这几个月里，学业压力具体体现在哪些方面，主要原因是什么？",
    mislabelLatestDetailAsNewEvent: true,
  });
  await start(value, null);
  await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: answerActionId,
    turnVersion: 0, answer: "2017年5月硕士毕业",
  });
  const firstId = value.cases.get(startActionId)?.row.eventEvidence[0]?.id;
  assert.ok(firstId);

  const next = await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: secondAnswerActionId,
    turnVersion: 1, answer: "2017年7月入职第一家公司",
  });

  const stored = value.cases.get(startActionId)?.row.eventEvidence ?? [];
  assert.equal(stored.length, 2);
  assert.deepEqual(stored[1]?.correctsEvidenceIds, []);
  assert.equal(stored[1]?.dateValue, "2017-07");
  assert.match(stored[1]?.eventSummary ?? "", /入职第一家公司/);
  assert.equal(next.evidenceRecap.length, 2);
  assert.equal(next.evidenceRecap.some((item) => item.id === firstId), true);
});

test("the next evidence request moves past a domain the user already answered", async () => {
  const value = harness({ readyAfterEvidenceCount: 99 });
  await start(value, null);

  const turn = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2020年5月结婚",
  });

  assert.deepEqual(turn.evidenceRequest?.domains, ["career"]);
  assert.match(turn.narrative, /事业/);
  assert.doesNotMatch(turn.narrative, /下一步[^\n]*重要关系/);
});

test("a rejected intermediate narrative returns a retryable error without saving a template turn", async () => {
  const value = harness({ invalidNarrativeFromGeneration: 1 });
  await start(value, null);

  await assert.rejects(value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: answerActionId,
    turnVersion: 0, answer: "2021年7月开始第一份长期工作",
  }), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "service_unavailable");

  const stored = value.cases.get(startActionId)?.row;
  assert.equal(stored?.turnVersion, 0);
  assert.equal(stored?.privateCandidate.resultId, null);
  assert.equal(stored?.eventEvidence.length, 0);
  assert.equal(stored?.validationReceipts.length, 1);
  assert.equal(value.mutations.filter((mutation) => mutation === "saveTurn").length, 0);
});

test("one through three supported events save and narrate before the fourth accumulated event ranks", async () => {
  const value = harness({ readyAfterEvidenceCount: 4 });
  await start(value, null);
  const answers = [
    [answerActionId, "2019年7月毕业"],
    [secondAnswerActionId, "2020年8月搬家"],
    [thirdAnswerActionId, "2021年9月换工作"],
    [fourthAnswerActionId, "2022年10月结婚"],
  ] as const;

  for (const [index, [receivedActionId, answer]] of answers.entries()) {
    const turn = await value.service.answer(userId, {
      type: "answer",
      caseId: startActionId,
      actionId: receivedActionId,
      turnVersion: index,
      answer,
    });
    const stored = value.cases.get(startActionId)?.row;
    assert.equal(stored?.eventEvidence.length, index + 1);
    assert.equal(turn.evidenceRecap.length, index + 1);
    assert.equal(turn.status, index < 3 ? "active" : "confirming");
    assert.ok(turn.narrative.length > 0);
    assert.doesNotMatch(turn.narrative, /当前累计|本轮已纳入|本轮区分重点|下一步：/);
  }

  assert.equal(value.counts().packetBuilds, 4);
  assert.equal(value.events.filter((event) => event === "narrative").length, 4);
});

test("intermediate narrative receives the complete active event ledger", async () => {
  const value = harness({ readyAfterEvidenceCount: 99 });
  await start(value, null);
  await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2020年9月底主动离开研究单位",
  });
  await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: secondAnswerActionId,
    turnVersion: 1,
    answer: "2023年4月进入下一家公司",
  });

  const prompt = value.narrativePrompts.at(-1) ?? "";
  assert.match(prompt, /2020年9月底主动离开研究单位/);
  assert.match(prompt, /2023年4月进入下一家公司/);
  assert.match(prompt, /eventLedger/);
});

test("a plateaued non-confirmable conversational case returns a bounded candidate after current domains are covered", async () => {
  const value = harness({ readyAfterEvidenceCount: 99 });
  await start(value, "请继续回答原来的事业问题");
  const answers = [
    [answerActionId, "2019年7月毕业"],
    [secondAnswerActionId, "2020年8月搬家"],
    [thirdAnswerActionId, "2021年9月换工作"],
    [fourthAnswerActionId, "2022年10月结婚"],
  ] as const;
  let latest = value.cases.get(startActionId)?.row.latestTurn;

  for (const [index, [receivedActionId, answer]] of answers.entries()) {
    latest = await value.service.answer(userId, {
      type: "answer",
      caseId: startActionId,
      actionId: receivedActionId,
      turnVersion: index,
      answer,
    });
    if (index === 2) {
      assert.equal(latest.status, "active");
      assert.deepEqual(latest.evidenceRequest?.domains, ["relationship"]);
    }
  }

  assert.equal(latest?.status, "completed");
  assert.equal(latest?.candidate.status, "pending_validation");
  assert.deepEqual(latest?.actions, ["continue_original_question"]);
  assert.equal(latest?.evidenceRequest, null);
  assert.equal(value.cases.get(startActionId)?.row.status, "completed");
  assert.equal(value.cases.get(startActionId)?.row.privateCandidate.representativeTime, "05:20");
  assert.equal(value.cases.get(startActionId)?.row.privateCandidate.resultId, null);
});

test("an unanswered suggested domain keeps a plateaued candidate conversational", async () => {
  const value = harness({
    packetForEvidenceCount() {
      const pending = packet(false);
      return {
        ...pending,
        suggestedDomains: [{
          domain: "finance",
          layer: "D2",
          reason: "D2 仍需要一条已发生的财务事件区分。",
        }],
      };
    },
  });
  await start(value, null);
  const answers = [
    [answerActionId, "2019年7月毕业"],
    [secondAnswerActionId, "2020年8月搬家"],
    [thirdAnswerActionId, "2021年9月换工作"],
    [fourthAnswerActionId, "2022年10月结婚"],
  ] as const;
  let latest = value.cases.get(startActionId)?.row.latestTurn;

  for (const [index, [receivedActionId, answer]] of answers.entries()) {
    latest = await value.service.answer(userId, {
      type: "answer",
      caseId: startActionId,
      actionId: receivedActionId,
      turnVersion: index,
      answer,
    });
  }

  assert.equal(latest?.status, "active");
  assert.deepEqual(latest?.evidenceRequest?.domains, ["finance"]);
  assert.deepEqual(latest?.actions, ["answer", "pause", "abandon"]);
});

test("system-only blockers return a bounded result without waiting for another plateau", async () => {
  const value = harness({
    packetForEvidenceCount(count) {
      const pending = packet(false);
      if (count === 0) return pending;
      const range = count >= 4
        ? { startTime: "05:00", endTime: "05:40" }
        : pending.candidate.range;
      return {
        ...pending,
        candidate: { ...pending.candidate, range },
        sensitivityScope: {
          ...pending.sensitivityScope,
          rangeStart: range.startTime,
          rangeEnd: range.endTime,
        },
        suggestedDomains: [],
        expertWorkflow: {
          boundary: "not_auto_rectified",
          candidateWindows: [{ ...range, status: "pending_validation" }],
          techniqueAuditTable: [],
          confirmationAllowed: false,
          hardBlockers: ["required_layers_incomplete"],
          gates: {},
        },
      };
    },
  });
  await start(value, null);
  const turn = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2019年7月毕业，2020年8月搬家，2021年9月换工作，2022年10月结婚",
  });

  assert.equal(turn.status, "completed");
  assert.equal(turn.candidate.status, "pending_validation");
  assert.equal(turn.evidenceRequest, null);
  assert.deepEqual(turn.actions, []);
  assert.equal(turn.candidate.rangeStart, "05:00");
  assert.equal(turn.candidate.rangeEnd, "05:40");
});

test("family evidence remains stored and public without changing its domain", async () => {
  const value = harness({ readyAfterEvidenceCount: 3 });
  await start(value, null);

  const turn = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2020年7月父亲生病",
  });

  const stored = value.cases.get(startActionId)?.row.eventEvidence ?? [];
  assert.equal(stored.length, 1);
  assert.equal(stored[0]?.domain, "family");
  assert.match(stored[0]?.eventSummary ?? "", /父亲/);
  assert.deepEqual(turn.evidenceRecap, [{
    id: stored[0]?.id,
    summary: stored[0]?.eventSummary,
    dateLabel: "2020-07",
    domain: "family",
  }]);
  assert.deepEqual(value.packetEvidenceCounts, [0]);
  assert.equal(turn.status, "active");
});

test("three valid events plus pre-birth evidence wait until a later valid fourth event confirms", async () => {
  const value = harness({ readyAfterEvidenceCount: 4 });
  await start(value, null);
  const answers = [
    [answerActionId, "2019年7月毕业"],
    [secondAnswerActionId, "2020年8月搬家"],
    [thirdAnswerActionId, "1999年12月开始工作"],
    [fourthAnswerActionId, "2021年9月换工作"],
    [fifthAnswerActionId, "2022年10月结婚"],
  ] as const;

  let latest = value.cases.get(startActionId)?.row.latestTurn;
  for (const [index, [receivedActionId, answer]] of answers.entries()) {
    latest = await value.service.answer(userId, {
      type: "answer",
      caseId: startActionId,
      actionId: receivedActionId,
      turnVersion: index,
      answer,
    });
    assert.equal(latest.status, index < 4 ? "active" : "confirming");
  }

  const stored = value.cases.get(startActionId)?.row;
  const preBirth = stored?.eventEvidence.find((item) => item.dateValue === "1999-12");
  assert.equal(preBirth?.scoreable, false);
  assert.equal(preBirth?.extractionStatus, "needs_clarification");
  assert.equal(stored?.eventEvidence.length, 5);
  assert.equal(latest?.evidenceRecap.length, 5);
  assert.deepEqual(value.packetEvidenceCounts, [1, 2, 2, 3, 4]);
});

test("vague, future, and unmatched answers stay conversational and never score", async () => {
  for (const [answer, domain] of [
    ["后来换了工作", undefined],
    ["2099年3月开始新工作", undefined],
    ["这些都不符合，我想从家庭变化说起", "family"],
  ] as const) {
    const value = harness();
    await start(value, null);
    const turn = await value.service.answer(userId, {
      type: "answer",
      caseId: startActionId,
      actionId: answerActionId,
      turnVersion: 0,
      answer,
      ...(domain ? { domain } : {}),
    });
    assert.equal(value.counts().packetBuilds, 1);
    assert.equal(turn.status, "active");
    assert.match(turn.narrative, /哪一年|哪一月|年月|已发生|已经发生|换个方向|未来/);
    assert.doesNotMatch(turn.narrative, /好的，我们不沿用不符合你的方向|已保存这段描述|我已保存你的原话|这条更正已保存/);
    assert.doesNotMatch(turn.narrative, /A[.、:]|B[.、:]|2006.?2011/);
    assert.equal(value.cases.get(startActionId)?.row.eventEvidence.at(-1)?.scoreable, false);
  }
});

test("a non-scoring packet failure responds to the current turn instead of replaying the prior agent message", async () => {
  const value = harness({
    packetFailure: new Error("synthetic packet outage"),
    packetFailureFromBuild: 1,
  });
  const initial = await start(value, null);

  const turn = await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: answerActionId,
    turnVersion: 0, answer: "化学专业",
  });

  assert.notEqual(turn.narrative, initial.narrative);
  assert.match(turn.narrative, /化学专业|这轮|这次分析/);
  assert.match(turn.narrative, /暂时没有完成/);
  assert.equal(value.cases.get(startActionId)?.row.validationReceipts.at(-1)?.fallbackUsed, true);
  assert.equal(value.cases.get(startActionId)?.row.eventEvidence.at(-1)?.rawText, "化学专业");
});

test("resume returns the latest owned turn on a stale new-device version without mutation or charge", async () => {
  const value = harness();
  const initial = await start(value, null);
  const paused = await value.service.pause(userId, {
    type: "pause", caseId: startActionId, actionId: pauseActionId, turnVersion: 0,
  });
  assert.equal(paused.status, "paused");
  assert.equal(paused.narrative, initial.narrative);
  const latest = await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: answerActionId,
    turnVersion: 1, answer: "2021年7月毕业，并在2022年3月去外地工作",
  });
  const mutationsBeforeResume = [...value.mutations];
  const resumed = await value.service.resume(userId, {
    type: "resume", caseId: startActionId, actionId: resumeActionId, turnVersion: 0,
  });
  assert.deepEqual(resumed, latest);
  assert.deepEqual(value.mutations, mutationsBeforeResume);
  assert.equal(value.counts().reserveCount, 1);
  await assert.rejects(value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: laterActionId,
    turnVersion: 0, answer: "2021年7月毕业",
  }), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "stale_turn");
});

test("a lost-response retry replays the saved answer without rescoring or regenerating", async () => {
  const value = harness();
  await start(value, null);
  const command = {
    type: "answer" as const,
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2021年7月毕业，并在2022年3月去外地工作",
  };
  const first = await value.service.answer(userId, command);
  const before = [...value.events];
  const replayed = await value.service.answer(userId, command);
  assert.deepEqual(replayed, first);
  assert.equal(value.counts().packetBuilds, 1);
  assert.deepEqual(value.events, before);
});

test("regenerate rewrites only the current narrative and preserves evidence, scoring, candidate, and billing", async () => {
  const value = harness({ readyAfterEvidenceCount: 99, varyNarrative: true });
  await start(value, null);
  const answered = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2012年12月正式退学，2013年1月彻底离开学校",
  });
  const storedBefore = value.cases.get(startActionId)?.row;
  assert.ok(storedBefore);
  const evidenceBefore = structuredClone(storedBefore.eventEvidence);
  const candidateBefore = structuredClone(storedBefore.privateCandidate);
  const countsBefore = value.counts();
  const scoreableCountBefore = value.packetEvidenceCounts.at(-1);
  const scoreableIdsBefore = value.packetEvidenceIds.at(-1);

  const regenerated = await value.service.regenerate(userId, {
    type: "regenerate",
    caseId: startActionId,
    actionId: laterActionId,
    turnVersion: answered.turnVersion,
  });

  const storedAfter = value.cases.get(startActionId)?.row;
  assert.ok(storedAfter);
  assert.equal(regenerated.turnVersion, answered.turnVersion + 1);
  assert.notEqual(regenerated.narrative, answered.narrative);
  assert.deepEqual(storedAfter.eventEvidence, evidenceBefore);
  assert.deepEqual(storedAfter.privateCandidate, candidateBefore);
  assert.equal(value.counts().reserveCount, countsBefore.reserveCount);
  assert.equal(value.packetEvidenceCounts.at(-1), scoreableCountBefore);
  assert.deepEqual(value.packetEvidenceIds.at(-1), scoreableIdsBefore);
  assert.equal(value.mutations.filter((mutation) => mutation === "saveTurn").length, 2);
  assert.match(value.narrativePrompts.at(-1) ?? "", /2012年12月正式退学/);
});

test("a failed regenerate preserves the prior turn, evidence, candidate, and billing", async () => {
  const value = harness({ readyAfterEvidenceCount: 99, invalidNarrativeFromGeneration: 2 });
  await start(value, null);
  const answered = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2012年12月正式退学，2013年1月彻底离开学校",
  });
  const storedBefore = value.cases.get(startActionId)?.row;
  assert.ok(storedBefore);
  const snapshotBefore = structuredClone(storedBefore);
  const countsBefore = value.counts();
  const saveTurnsBefore = value.mutations.filter((mutation) => mutation === "saveTurn").length;

  await assert.rejects(value.service.regenerate(userId, {
    type: "regenerate",
    caseId: startActionId,
    actionId: laterActionId,
    turnVersion: answered.turnVersion,
  }), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "service_unavailable");

  const storedAfter = value.cases.get(startActionId)?.row;
  assert.deepEqual(storedAfter, snapshotBefore);
  assert.equal(storedAfter?.turnVersion, answered.turnVersion);
  assert.equal(storedAfter?.latestTurn.narrative, answered.narrative);
  assert.equal(value.counts().reserveCount, countsBefore.reserveCount);
  assert.equal(value.counts().releaseCount, countsBefore.releaseCount);
  assert.equal(value.counts().packetBuilds, countsBefore.packetBuilds + 1);
  assert.equal(
    value.mutations.filter((mutation) => mutation === "saveTurn").length,
    saveTurnsBefore,
  );
});

test("overlapping identical answers converge on the first receipt despite different derived narratives", async () => {
  const value = harness({ varyNarrative: true });
  await start(value, null);
  const command = {
    type: "answer" as const,
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2021年7月毕业，并在2022年3月去外地工作",
  };

  const [first, second] = await Promise.all([
    value.service.answer(userId, command),
    value.service.answer(userId, command),
  ]);

  assert.deepEqual(second, first);
  assert.equal(value.cases.get(startActionId)?.row.eventEvidence.length, 2);
  assert.equal(value.events.filter((event) => event === "narrative").length, 2);
  assert.equal(value.mutations.filter((mutation) => mutation === "saveTurn").length, 2);
});

test("receipt-first delayed retries replay the original answer, pause, abandon, and confirm after later turns", async () => {
  const scenarios = [
    {
      name: "answer",
      async perform(value: ReturnType<typeof harness>) {
        const command = {
          type: "answer" as const,
          caseId: startActionId,
          actionId: answerActionId,
          turnVersion: 0,
          answer: "2018年6月毕业，2019年7月开始第一份工作，2020年3月去外地工作，2022年8月结婚",
        };
        return { command, first: await value.service.answer(userId, command) };
      },
    },
    {
      name: "pause",
      async perform(value: ReturnType<typeof harness>) {
        const command = {
          type: "pause" as const,
          caseId: startActionId,
          actionId: pauseActionId,
          turnVersion: 0,
        };
        return { command, first: await value.service.pause(userId, command) };
      },
    },
    {
      name: "abandon",
      async perform(value: ReturnType<typeof harness>) {
        const command = {
          type: "abandon" as const,
          caseId: startActionId,
          actionId: laterActionId,
          turnVersion: 0,
        };
        return { command, first: await value.service.abandon(userId, command) };
      },
    },
    {
      name: "confirm",
      async perform(value: ReturnType<typeof harness>) {
        const ready = await value.service.answer(userId, {
          type: "answer",
          caseId: startActionId,
          actionId: answerActionId,
          turnVersion: 0,
          answer: "2018年6月毕业，2019年7月开始第一份工作，2020年3月去外地工作，2022年8月结婚",
        });
        const command = {
          type: "confirm" as const,
          caseId: startActionId,
          actionId: confirmActionId,
          turnVersion: ready.turnVersion,
          time: "05:18",
        };
        return { command, first: await value.service.confirm(userId, command) };
      },
    },
  ] as const;

  for (const scenario of scenarios) {
    const value = harness();
    await start(value, null);
    const { command, first } = await scenario.perform(value);
    value.forceLaterVersion(startActionId, first.turnVersion + 2);
    const mutationsBeforeReplay = [...value.mutations];
    const eventsBeforeReplay = [...value.events];

    const replayed = await value.service[scenario.name](userId, command as never);

    assert.deepEqual(replayed, first, scenario.name);
    assert.deepEqual(value.mutations, mutationsBeforeReplay, scenario.name);
    assert.deepEqual(value.events, eventsBeforeReplay, scenario.name);
  }
});

test("receipt-first delayed replay rejects the same action id with a different command payload", async () => {
  const value = harness();
  await start(value, null);
  const command = {
    type: "answer" as const,
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    domain: "education" as const,
    answer: "2021年7月毕业",
  };
  const first = await value.service.answer(userId, command);
  value.forceLaterVersion(startActionId, first.turnVersion + 2);

  await assert.rejects(value.service.answer(userId, {
    ...command,
    domain: "career",
  }), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "action_conflict");
});

test("confirm delegates to the atomic store call, preserves the old baseline until then, and returns the saved question", async () => {
  const value = harness();
  await start(value, "请继续回答原来的事业问题");
  const ready = await value.service.answer(userId, {
    type: "answer", caseId: startActionId, actionId: answerActionId,
    turnVersion: 0, answer: "2018年6月毕业，2019年7月开始第一份工作，2020年3月去外地工作，2022年8月结婚",
  });
  assert.equal(value.cases.get(startActionId)?.row.baselineActiveTime, "04:58");
  const before = value.mutations.length;
  const confirmed = await value.service.confirm(userId, {
    type: "confirm", caseId: startActionId, actionId: confirmActionId,
    turnVersion: ready.turnVersion, time: "05:18",
  });
  assert.deepEqual(value.mutations.slice(before), ["confirm"]);
  assert.equal(confirmed.status, "completed");
  assert.equal(confirmed.candidate.status, "confirmed");
  assert.equal(confirmed.narrative, ready.narrative);
  assert.equal(confirmed.pendingConsultationQuestion, "请继续回答原来的事业问题");
  assert.deepEqual(confirmed.actions, ["continue_original_question"]);
});
