import assert from "node:assert/strict";
import test from "node:test";
import {
  CONVERSATIONAL_RECTIFICATION_UNAVAILABLE,
  ConversationalRectificationRequestError,
  createConversationalRectificationActionRegistry,
  sendConversationalRectificationCommand,
} from "../src/lib/conversational-rectification/client.ts";
import type { ConversationalRectificationTurn } from "../src/lib/conversational-rectification/contracts.ts";

const caseId = "00000000-0000-4000-8000-000000000801";
const firstActionId = "00000000-0000-4000-8000-000000000802";
const secondActionId = "00000000-0000-4000-8000-000000000803";

const turn: ConversationalRectificationTurn = {
  caseId,
  journeyProtocol: "conversational-evidence-v3",
  status: "active",
  turnVersion: 4,
  narrative: "**05:18** 仍是待验证候选，请提供真实经历。",
  candidate: {
    status: "pending_validation",
    representativeTime: "05:18",
    rangeStart: "05:10",
    rangeEnd: "05:26",
  },
  technicalReceipt: {
    calculationVersion: "rectification-technical-v1",
    stableLayers: ["D1"],
    sensitiveLayers: ["D9", "D10"],
    candidateDifferenceRefs: ["consult-d9", "consult-d10"],
  },
  evidenceRequest: {
    domains: ["relationship", "career"],
    datePrecision: "month_preferred",
    freeTextAllowed: true,
  },
  evidenceRecap: [],
  actions: ["answer", "pause", "abandon"],
  pendingConsultationQuestion: null,
};

test("action registry keeps one id for a failed canonical command and separates changed payloads", async () => {
  const ids = [firstActionId, secondActionId];
  const registry = createConversationalRectificationActionRegistry(
    () => ids.shift() ?? assert.fail("unexpected action id allocation"),
  );
  const seen: string[] = [];
  const first = {
    caseId,
    turnVersion: 4,
    operation: "answer",
    payload: { answer: "2021 年 7 月毕业", domain: "education" },
  } as const;

  await assert.rejects(registry.run(first, async (actionId) => {
    seen.push(actionId);
    throw new TypeError("response lost twice");
  }));
  await assert.rejects(registry.run({
    ...first,
    payload: { domain: "education", answer: "2021 年 7 月毕业" },
  }, async (actionId) => {
    seen.push(actionId);
    throw new TypeError("still offline");
  }));
  await assert.rejects(registry.run({
    ...first,
    payload: { answer: "2022 年 3 月搬家", domain: "relocation" },
  }, async (actionId) => {
    seen.push(actionId);
    throw new TypeError("offline");
  }));

  assert.deepEqual(seen, [firstActionId, firstActionId, secondActionId]);
});

test("client replays the exact action body after a lost response without adding a price", async (context) => {
  const bodies: string[] = [];
  let attempts = 0;
  context.mock.method(globalThis, "fetch", async (_input: string | URL | Request, init?: RequestInit) => {
    attempts += 1;
    bodies.push(String(init?.body));
    if (attempts === 1) throw new TypeError("response lost");
    return new Response(JSON.stringify(turn), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  });

  const result = await sendConversationalRectificationCommand({
    type: "answer",
    caseId,
    actionId: firstActionId,
    turnVersion: 3,
    domain: "career",
    answer: "2021 年 7 月开始第一份工作",
  });

  assert.deepEqual(result, turn);
  assert.equal(attempts, 2);
  assert.equal(bodies[0], bodies[1]);
  assert.equal(Object.hasOwn(JSON.parse(bodies[0]) as object, "price"), false);
});

test("502 and non-JSON failures expose one stable Chinese message", async (context) => {
  context.mock.method(globalThis, "fetch", async () => new Response("upstream html", {
    status: 502,
    headers: { "content-type": "text/html" },
  }));

  await assert.rejects(
    sendConversationalRectificationCommand({
      type: "pause",
      caseId,
      actionId: firstActionId,
      turnVersion: 4,
    }),
    (error: unknown) => error instanceof ConversationalRectificationRequestError
      && error.status === 502
      && error.message === CONVERSATIONAL_RECTIFICATION_UNAVAILABLE,
  );
});
