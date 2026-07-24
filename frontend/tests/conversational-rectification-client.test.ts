import assert from "node:assert/strict";
import test from "node:test";
import {
  CONVERSATIONAL_RECTIFICATION_UNAVAILABLE,
  ConversationalRectificationRequestError,
  createConversationalRectificationActionRegistry,
  conversationalRectificationHistoryForTurn,
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

test("action registry releases a successful identity but keeps it for a manual failure retry", async () => {
  const ids = [firstActionId, secondActionId];
  const registry = createConversationalRectificationActionRegistry(
    () => ids.shift() ?? assert.fail("unexpected action id allocation"),
  );
  const identity = {
    caseId,
    turnVersion: 4,
    operation: "pause",
    payload: {},
  } as const;
  const seen: string[] = [];

  await assert.rejects(registry.run(identity, async (actionId) => {
    seen.push(actionId);
    throw new TypeError("offline");
  }));
  await registry.run(identity, async (actionId) => {
    seen.push(actionId);
    return turn;
  });
  await registry.run(identity, async (actionId) => {
    seen.push(actionId);
    return turn;
  });

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
    modelId: "gpt-5-5",
    domain: "career",
    answer: "2021 年 7 月开始第一份工作",
  });

  assert.deepEqual(result, turn);
  assert.equal(attempts, 2);
  assert.equal(bodies[0], bodies[1]);
  assert.equal((JSON.parse(bodies[0]) as { modelId?: string }).modelId, "gpt-5-5");
  assert.equal(Object.hasOwn(JSON.parse(bodies[0]) as object, "price"), false);
});

test("client keeps recovered one-question-at-a-time history outside the strict turn contract", async (context) => {
  const conversationMessages = [
    { role: "assistant" as const, text: "请先告诉我一件时间明确的重要经历。" },
    { role: "user" as const, text: "2014 年 6 月大学毕业。" },
    { role: "assistant" as const, text: turn.narrative },
  ];
  context.mock.method(globalThis, "fetch", async () => Response.json({
    ...turn,
    conversationMessages,
  }));

  const result = await sendConversationalRectificationCommand({
    type: "resume",
    caseId,
    actionId: firstActionId,
    turnVersion: 4,
  });

  assert.deepEqual(result, turn);
  assert.deepEqual(conversationalRectificationHistoryForTurn(result), conversationMessages);
});

test("client sends regenerate as a payload-free replay command", async (context) => {
  let body: unknown;
  context.mock.method(globalThis, "fetch", async (_input: string | URL | Request, init?: RequestInit) => {
    body = JSON.parse(String(init?.body));
    return Response.json({ ...turn, turnVersion: 5, narrative: "重新生成后的回答。" });
  });

  const result = await sendConversationalRectificationCommand({
    type: "regenerate",
    caseId,
    actionId: firstActionId,
    turnVersion: 4,
  });

  assert.deepEqual(body, {
    type: "regenerate",
    caseId,
    actionId: firstActionId,
    turnVersion: 4,
  });
  assert.equal(result.narrative, "重新生成后的回答。");
});

test("a JSON 502 is retried once with the exact action body before succeeding", async (context) => {
  const bodies: string[] = [];
  context.mock.method(globalThis, "fetch", async (_input: string | URL | Request, init?: RequestInit) => {
    bodies.push(String(init?.body));
    if (bodies.length === 1) {
      return Response.json({ code: "service_unavailable", message: "internal detail" }, { status: 502 });
    }
    return Response.json(turn);
  });

  const result = await sendConversationalRectificationCommand({
    type: "pause",
    caseId,
    actionId: firstActionId,
    turnVersion: 4,
  });

  assert.deepEqual(result, turn);
  assert.equal(bodies.length, 2);
  assert.equal(bodies[0], bodies[1]);
  assert.equal(JSON.parse(bodies[0] ?? "{}").actionId, firstActionId);
});

test("a non-ok non-JSON response is retried once even when a proxy mislabels it as JSON", async (context) => {
  const bodies: string[] = [];
  context.mock.method(globalThis, "fetch", async (_input: string | URL | Request, init?: RequestInit) => {
    bodies.push(String(init?.body));
    if (bodies.length === 1) {
      return new Response("proxy html", {
        status: 503,
        headers: { "content-type": "application/json" },
      });
    }
    return Response.json(turn);
  });

  const result = await sendConversationalRectificationCommand({
    type: "pause",
    caseId,
    actionId: firstActionId,
    turnVersion: 4,
  });

  assert.deepEqual(result, turn);
  assert.equal(bodies.length, 2);
  assert.equal(bodies[0], bodies[1]);
});

test("502 and non-JSON failures retry only once before one stable Chinese message", async (context) => {
  const bodies: string[] = [];
  context.mock.method(globalThis, "fetch", async (_input: string | URL | Request, init?: RequestInit) => {
    bodies.push(String(init?.body));
    return new Response("upstream html", {
      status: 502,
      headers: { "content-type": "text/html" },
    });
  });

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
  assert.equal(bodies.length, 2);
  assert.equal(bodies[0], bodies[1]);
});

test("client emits validated rectification narrative chunks before accepting the durable turn", async (context) => {
  const chunks = ["已记录这段经历。", "接下来核对关系事件。"];
  context.mock.method(globalThis, "fetch", async (_input: string | URL | Request, init?: RequestInit) => {
    assert.match(String((init?.headers as Record<string, string>)?.Accept), /application\/x-ndjson/);
    return new Response([
      ...chunks.map((text) => JSON.stringify({ type: "delta", text })),
      JSON.stringify({ type: "turn", turn }),
      "",
    ].join("\n"), {
      status: 200,
      headers: { "content-type": "application/x-ndjson; charset=utf-8" },
    });
  });
  const seen: string[] = [];

  const result = await sendConversationalRectificationCommand({
    type: "pause",
    caseId,
    actionId: firstActionId,
    turnVersion: 4,
  }, {
    onNarrativeDelta(text) {
      seen.push(text);
    },
  });

  assert.deepEqual(seen, chunks);
  assert.deepEqual(result, turn);
});
