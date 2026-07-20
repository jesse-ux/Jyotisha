import assert from "node:assert/strict";
import test from "node:test";
import {
  conversationalRectificationCommandSchema,
  conversationalRectificationTurnSchema,
} from "../src/lib/conversational-rectification/contracts.ts";
import {
  ConversationalRectificationError,
  toConversationalRectificationPublicError,
} from "../src/lib/conversational-rectification/errors.ts";

const actionId = "a9890e09-d535-46f0-9a36-86017515a5a1";
const caseId = "77b29d28-c576-429e-9e3d-d0a90348e3cb";

function parseCommand(value: unknown) {
  return conversationalRectificationCommandSchema.safeParse(value).success;
}

test("accepts only the six strict conversational commands", () => {
  const commands = [
    { type: "start", actionId, pendingConsultationQuestion: null },
    { type: "resume", caseId, actionId, turnVersion: 0 },
    { type: "answer", caseId, actionId, turnVersion: 1, answer: "2019 年 7 月换了工作" },
    { type: "pause", caseId, actionId, turnVersion: 1 },
    { type: "abandon", caseId, actionId, turnVersion: 1 },
    { type: "confirm", caseId, actionId, turnVersion: 1, time: "05:21" },
  ];

  for (const command of commands) assert.equal(parseCommand(command), true, command.type);
  assert.equal(parseCommand({ type: "complete", caseId, actionId, turnVersion: 1 }), false);
  assert.equal(parseCommand({ type: "pause", caseId, actionId, turnVersion: 1, ignored: true }), false);
});

test("requires UUID actions and current nonnegative versions after start", () => {
  assert.equal(parseCommand({ type: "start", actionId: "not-a-uuid", pendingConsultationQuestion: null }), false);
  assert.equal(parseCommand({ type: "resume", caseId, actionId: "not-a-uuid", turnVersion: 0 }), false);
  assert.equal(parseCommand({ type: "answer", caseId, actionId, answer: "有效回答" }), false);
  assert.equal(parseCommand({ type: "answer", caseId, actionId, turnVersion: -1, answer: "有效回答" }), false);
  assert.equal(parseCommand({ type: "answer", caseId, actionId, turnVersion: 1.5, answer: "有效回答" }), false);
});

test("bounds free-text answers and requires a strict HH:mm confirmation time", () => {
  assert.equal(parseCommand({ type: "answer", caseId, actionId, turnVersion: 1, answer: "   " }), false);
  assert.equal(parseCommand({ type: "answer", caseId, actionId, turnVersion: 1, answer: "x".repeat(4_001) }), false);
  assert.equal(parseCommand({ type: "confirm", caseId, actionId, turnVersion: 1, time: "5:21" }), false);
  assert.equal(parseCommand({ type: "confirm", caseId, actionId, turnVersion: 1, time: "24:00" }), false);
});

test("rejects client candidate scores and technical receipts", () => {
  assert.equal(parseCommand({
    type: "answer", caseId, actionId, turnVersion: 1, answer: "2019 年 7 月换了工作",
    candidateScores: [0.99],
  }), false);
  assert.equal(parseCommand({
    type: "confirm", caseId, actionId, turnVersion: 1, time: "05:21",
    technicalReceipt: { calculationVersion: "client-forged" },
  }), false);
});

test("accepts only the exact public turn shape", () => {
  const turn = {
    caseId,
    journeyProtocol: "conversational-evidence-v3",
    status: "active",
    turnVersion: 1,
    narrative: "我们先用已经发生的人生事件缩小候选范围。",
    candidate: {
      status: "pending_validation",
      representativeTime: "05:21",
      rangeStart: "05:10",
      rangeEnd: "05:30",
    },
    technicalReceipt: {
      calculationVersion: "v3.0",
      stableLayers: ["D1"],
      sensitiveLayers: ["D9"],
      candidateDifferenceRefs: ["candidate-difference-1"],
    },
    evidenceRequest: {
      domains: ["career", "relocation"],
      datePrecision: "month_preferred",
      freeTextAllowed: true,
    },
    evidenceRecap: [{
      id: "37e0e35e-cfdc-4c7a-8375-84310ee6bd42",
      summary: "2019 年换工作",
      dateLabel: "2019-07",
    }],
    actions: ["answer", "pause", "abandon"],
    pendingConsultationQuestion: null,
  };

  assert.equal(conversationalRectificationTurnSchema.safeParse(turn).success, true);
  assert.equal(conversationalRectificationTurnSchema.safeParse({ ...turn, candidateScores: [0.99] }).success, false);
  assert.equal(conversationalRectificationTurnSchema.safeParse({ ...turn, candidate: { ...turn.candidate, score: 0.99 } }).success, false);
  assert.equal(conversationalRectificationTurnSchema.safeParse({ ...turn, technicalReceipt: { ...turn.technicalReceipt, rawModelOutput: "secret" } }).success, false);
});

function assertNoReachableText(value: unknown, forbidden: string, seen = new Set<unknown>()) {
  if (typeof value === "string") {
    assert.equal(value.includes(forbidden), false, `found raw text in ${value}`);
    return;
  }
  if (value === null || (typeof value !== "object" && typeof value !== "function") || seen.has(value)) return;

  seen.add(value);
  for (const key of Reflect.ownKeys(value)) {
    assertNoReachableText(String(key), forbidden, seen);
    const descriptor = Object.getOwnPropertyDescriptor(value, key);
    if (descriptor && "value" in descriptor) assertNoReachableText(descriptor.value, forbidden, seen);
  }
}

test("maps known domain failures to a frozen stable public DTO", () => {
  const stale = toConversationalRectificationPublicError(new ConversationalRectificationError("stale_turn"));
  assert.deepEqual(stale, {
    code: "stale_turn",
    status: 409,
    error: "校正进度已更新",
    message: "请加载最新进度后再试。",
    retryable: true,
  });
  assert.equal(Object.isFrozen(stale), true);
  assert.equal(Reflect.set(stale, "message", "mutated"), false);
});

test("exposes stable store and billing failures without retaining infrastructure details", () => {
  const expected = [
    ["action_conflict", 409],
    ["billing_failed", 503],
    ["store_unavailable", 503],
  ] as const;

  for (const [code, status] of expected) {
    const error = new ConversationalRectificationError(code);
    const publicError = toConversationalRectificationPublicError(error);
    assert.equal(publicError.code, code);
    assert.equal(publicError.status, status);
    assert.equal(publicError.retryable, true);
    assert.equal(Object.isFrozen(publicError), true);
    assert.deepEqual(Reflect.ownKeys(publicError).sort(), ["code", "error", "message", "retryable", "status"]);
  }
});

test("maps unknown failures to a complete non-leaking public DTO", () => {
  const rawMessage = "WebKit SyntaxError: SQL password=model secret";
  const rawFailure = Object.assign(new Error(rawMessage, { cause: new Error(rawMessage) }), {
    browserError: rawMessage,
    modelResponse: { message: rawMessage },
  });
  const recovered = toConversationalRectificationPublicError(rawFailure);
  assert.deepEqual(recovered, {
    code: "service_unavailable",
    status: 503,
    error: "生时校正暂时不可用",
    message: "服务暂时不可用，请稍后重试。",
    retryable: true,
  });
  assert.equal(Object.isFrozen(recovered), true);
  assertNoReachableText(recovered, rawMessage);
  assert.equal(JSON.stringify(recovered).includes(rawMessage), false);
  assert.equal(Reflect.set(recovered, "error", rawMessage), false);
});

function assertExactSafePublicDto(
  value: unknown,
  expected: {
    code: string;
    status: number;
    error: string;
    message: string;
    retryable: boolean;
  },
  rawMessage: string,
) {
  assert.deepEqual(value, expected);
  assert.equal(Object.getPrototypeOf(value), Object.prototype);
  assert.deepEqual(Reflect.ownKeys(value).sort(), ["code", "error", "message", "retryable", "status"]);
  assert.equal(Object.isFrozen(value), true);
  assert.equal("cause" in (value as object), false);
  assert.deepEqual(JSON.parse(JSON.stringify(value)), expected);
  assertNoReachableText(value, rawMessage);
}

test("rebuilds safe DTOs from forged or mutated recognized errors", () => {
  const rawMessage = "raw browser SQL model cause";
  const expectedStale = {
    code: "stale_turn",
    status: 409,
    error: "校正进度已更新",
    message: "请加载最新进度后再试。",
    retryable: true,
  };
  const expectedUnavailable = {
    code: "service_unavailable",
    status: 503,
    error: "生时校正暂时不可用",
    message: "服务暂时不可用，请稍后重试。",
    retryable: true,
  };
  const mutatedPublic = new ConversationalRectificationError("stale_turn");
  const poisonedPublic = {
    ...expectedStale,
    message: rawMessage,
    cause: new Error(rawMessage),
  };
  Object.defineProperty(mutatedPublic, "public", { value: poisonedPublic });
  Object.assign(mutatedPublic, { cause: new Error(rawMessage), rawMessage });

  const rebuilt = toConversationalRectificationPublicError(mutatedPublic);
  assert.notStrictEqual(rebuilt, poisonedPublic);
  assertExactSafePublicDto(rebuilt, expectedStale, rawMessage);

  const mutatedCode = new ConversationalRectificationError("stale_turn");
  Object.defineProperty(mutatedCode, "code", { value: "forged_code" });
  assertExactSafePublicDto(
    toConversationalRectificationPublicError(mutatedCode),
    expectedUnavailable,
    rawMessage,
  );

  const forged = Object.create(ConversationalRectificationError.prototype);
  Object.assign(forged, {
    code: "stale_turn",
    public: poisonedPublic,
    cause: new Error(rawMessage),
    rawMessage,
  });
  assertExactSafePublicDto(
    toConversationalRectificationPublicError(forged),
    expectedUnavailable,
    rawMessage,
  );
});
