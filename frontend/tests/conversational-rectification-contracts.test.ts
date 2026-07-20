import assert from "node:assert/strict";
import test from "node:test";
import {
  conversationalRectificationCommandSchema,
  conversationalRectificationTurnSchema,
} from "../src/lib/conversational-rectification/contracts.ts";
import {
  ConversationalRectificationError,
  toConversationalRectificationError,
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

test("maps known domain failures to stable Chinese recovery copy", () => {
  const stale = new ConversationalRectificationError("stale_turn");
  assert.deepEqual(stale.public, {
    code: "stale_turn",
    status: 409,
    error: "校正进度已更新",
    message: "请加载最新进度后再试。",
  });

  const recovered = toConversationalRectificationError(new Error("WebKit SyntaxError: SQL password=model secret"));
  assert.deepEqual(recovered.public, {
    code: "service_unavailable",
    status: 503,
    error: "生时校正暂时不可用",
    message: "当前资料已安全保留，请稍后重试。",
  });
  assert.doesNotMatch(recovered.public.message, /WebKit|SQL|model|secret/i);
});
