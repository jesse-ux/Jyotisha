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

function validGenerator(events: string[], varyNarrative = false) {
  let generation = 0;
  return {
    modelId: "synthetic-rectification-model",
    async generate(prompt: string) {
      generation += 1;
      events.push("narrative");
      const request = JSON.parse(prompt) as {
        phase: "first" | "intermediate" | "final";
        packet: Omit<ReturnType<typeof packet>, "candidate"> & {
          candidate: ReturnType<typeof packet>["candidate"] & {
            rangeStart: string;
            rangeEnd: string;
          };
        };
      };
      const value = request.packet;
      const domains = value.suggestedDomains.map((item) => item.domain);
      const narrative = [
        `${value.candidate.representativeTime} 是待验证候选。`,
        "D1（Cancer）保持稳定。",
        "D9（Aries / Leo）呈现分钟敏感差异，关系事件可区分 D9。",
        "D10（Taurus / Libra）呈现分钟敏感差异，事业事件可区分 D10。",
        varyNarrative ? `这是第 ${generation} 次合成措辞。` : "",
        request.phase === "final" ? "当前证据已形成候选总结。" : "请提供已经发生的真实事件，写明哪一年、哪一月以及发生了什么。",
        "这仅是候选，必须由你确认后才会替换当前排盘时间。",
      ].join("");
      return { text: JSON.stringify({
        narrative,
        candidateStatus: value.candidate.status,
        representativeTime: value.candidate.representativeTime,
        rangeStart: value.candidate.rangeStart,
        rangeEnd: value.candidate.rangeEnd,
        useBoundary: value.useBoundary,
        stableLayers: value.stableLayers.map((item) => item.layer),
        sensitiveLayers: value.sensitiveLayers.map((item) => item.layer),
        referenceIds: [],
        domainReasons: value.suggestedDomains.map((item) => ({ ...item })),
        evidenceRequest: request.phase === "final" ? null : {
          domains,
          datePrecision: "month_preferred",
          prompt: "请提供已经发生的真实事件，并写明哪一年、哪一月以及发生了什么。",
        },
      }) };
    },
  };
}

type MutableCase = {
  row: LoadedConversationalRectificationCase;
};

function harness(options: {
  readonly packetFailure?: Error;
  readonly completeFailures?: number;
  readonly releaseFailure?: boolean;
  readonly readyAfterEvidenceCount?: number;
  readonly varyNarrative?: boolean;
} = {}) {
  const events: string[] = [];
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
      events.push(input.evidence.length > 0 ? "score-packet" : "packet");
      if (options.packetFailure) throw options.packetFailure;
      return input.evidence.length >= (options.readyAfterEvidenceCount ?? 1)
        ? { packet: packet(true), resultId }
        : { packet: packet(false), resultId: null };
    },
    narrativeGenerator: validGenerator(events, options.varyNarrative),
    asOfDate: () => "2026-07-21",
  };

  return {
    events,
    mutations,
    packetEvidenceCounts,
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

test("start validates profile, reads server price, reserves, computes, saves, then charges", async () => {
  const value = harness();
  const turn = await start(value);

  assert.deepEqual(value.events, ["profile", "price", "reserve:9", "packet", "narrative", "create", "complete"]);
  assert.equal(turn.caseId, startActionId);
  assert.equal(turn.turnVersion, 0);
  assert.equal(turn.pendingConsultationQuestion, "我的工作何时变化？");
  assert.deepEqual(turn.technicalReceipt.sensitiveLayers, ["D9", "D10"]);
  assert.equal(JSON.stringify(turn).includes("candidateWeights"), false);
  assert.equal(value.cases.get(startActionId)?.row.revisionOfCaseId, priorCaseId);
  assert.equal(value.cases.get(startActionId)?.row.baselineActiveTime, "04:58");
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
  const value = harness({ packetFailure: new Error(raw) });
  await assert.rejects(start(value), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "service_unavailable" && !error.message.includes(raw));
  assert.equal(value.counts().releaseCount, 1);
  assert.deepEqual(value.events, ["profile", "price", "reserve:9", "packet", "release"]);
});

test("a start retry settles an existing reservation without reserving or computing again", async () => {
  const value = harness({ completeFailures: 1, releaseFailure: true });
  await assert.rejects(start(value), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "billing_failed");
  assert.equal(value.cases.get(startActionId)?.row.billingState, "reserved");

  const replayed = await start(value);

  assert.equal(replayed.status, "active");
  assert.equal(value.cases.get(startActionId)?.row.billingState, "charged");
  assert.deepEqual(value.counts(), { packetBuilds: 1, reserveCount: 1, releaseCount: 1 });
  assert.deepEqual(value.events.slice(-3), ["profile", "price", "complete"]);
});

test("a settlement failure releases its created case once and cannot replay as success", async () => {
  const value = harness({ completeFailures: 1 });
  await assert.rejects(start(value), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "service_unavailable");
  assert.equal(value.cases.get(startActionId)?.row.billingState, "released");
  assert.deepEqual(value.events.slice(-3), ["create", "complete", "release"]);

  await assert.rejects(start(value), (error: unknown) => error instanceof ConversationalRectificationError
    && error.code === "billing_failed");
  assert.deepEqual(value.counts(), { packetBuilds: 1, reserveCount: 1, releaseCount: 1 });
});

test("clear historical evidence is extracted, scored, narrated, recapped, and atomically saved", async () => {
  const value = harness();
  await start(value);
  const turn = await value.service.answer(userId, {
    type: "answer",
    caseId: startActionId,
    actionId: answerActionId,
    turnVersion: 0,
    answer: "2021年7月毕业，并在2022年3月去外地工作",
  });

  assert.equal(value.counts().packetBuilds, 2);
  assert.equal(turn.status, "confirming");
  assert.equal(turn.candidate.status, "ready_for_confirmation");
  assert.equal(turn.turnVersion, 1);
  assert.equal(turn.evidenceRecap.length, 2);
  const saved = value.cases.get(startActionId)?.row.eventEvidence ?? [];
  assert.equal(saved.length, 2);
  assert.ok(saved.every((item) => item.rawText === "2021年7月毕业，并在2022年3月去外地工作"));
  assert.ok(saved.every((item) => item.scoreable === true));
  assert.ok(value.events.includes("score-packet"));
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

  assert.equal(turn.status, "confirming");
  assert.equal(value.counts().packetBuilds, 2);
  assert.ok(value.events.includes("score-packet"));
  assert.ok((value.cases.get(startActionId)?.row.eventEvidence ?? [])
    .some((item) => item.eventSummary.includes("毕业") && item.scoreable === true));
});

test("one and two supported events save and narrate before the third accumulated event ranks", async () => {
  const value = harness({ readyAfterEvidenceCount: 3 });
  await start(value, null);
  const answers = [
    [answerActionId, "2019年7月毕业"],
    [secondAnswerActionId, "2020年8月搬家"],
    [thirdAnswerActionId, "2021年9月换工作"],
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
    assert.equal(turn.status, index < 2 ? "active" : "confirming");
  }

  assert.equal(value.counts().packetBuilds, 4);
  assert.equal(value.events.filter((event) => event === "narrative").length, 4);
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
  }]);
  assert.equal(turn.status, "active");
});

test("two valid events plus pre-birth evidence wait until a later valid third event scores", async () => {
  const value = harness({ readyAfterEvidenceCount: 3 });
  await start(value, null);
  const answers = [
    [answerActionId, "2019年7月毕业"],
    [secondAnswerActionId, "2020年8月搬家"],
    [thirdAnswerActionId, "1999年12月开始工作"],
    [fourthAnswerActionId, "2021年9月换工作"],
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
    assert.equal(latest.status, index < 3 ? "active" : "confirming");
  }

  const stored = value.cases.get(startActionId)?.row;
  const preBirth = stored?.eventEvidence.find((item) => item.dateValue === "1999-12");
  assert.equal(preBirth?.scoreable, false);
  assert.equal(preBirth?.extractionStatus, "needs_clarification");
  assert.equal(stored?.eventEvidence.length, 4);
  assert.equal(latest?.evidenceRecap.length, 4);
  assert.deepEqual(value.packetEvidenceCounts, [0, 1, 2, 3]);
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
    assert.match(turn.narrative, /年月|已发生|已经发生|换个方向|未来/);
    assert.doesNotMatch(turn.narrative, /A[.、:]|B[.、:]|2006.?2011/);
    assert.equal(value.cases.get(startActionId)?.row.eventEvidence.at(-1)?.scoreable, false);
  }
});

test("resume returns the latest owned turn on a stale new-device version without mutation or charge", async () => {
  const value = harness();
  await start(value, null);
  const paused = await value.service.pause(userId, {
    type: "pause", caseId: startActionId, actionId: pauseActionId, turnVersion: 0,
  });
  assert.equal(paused.status, "paused");
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
  assert.equal(value.counts().packetBuilds, 2);
  assert.deepEqual(value.events, before);
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
  assert.equal(value.events.filter((event) => event === "narrative").length, 3);
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
          answer: "2021年7月毕业，并在2022年3月去外地工作",
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
          answer: "2021年7月毕业，并在2022年3月去外地工作",
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
    turnVersion: 0, answer: "2021年7月毕业，并在2022年3月去外地工作",
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
  assert.equal(confirmed.pendingConsultationQuestion, "请继续回答原来的事业问题");
  assert.deepEqual(confirmed.actions, ["continue_original_question"]);
});
