import assert from "node:assert/strict";
import test from "node:test";
import {
  draftBirthTimeEvidence,
  generateDynamicBirthTimeQuestion,
  reframeUnmatchedBirthTimeAnswer,
  requestBirthTimeGuidePrompt,
} from "../src/lib/birth-time-journey-client.ts";
import { highConfirmationTurn } from "./birth-time-journey-client-test-support.ts";

const caseId = highConfirmationTurn.caseId;
const actionId = "c70ea014-f8b4-41f2-9305-e4ae60c0d4d1";

test("guide prompt client sends only the case identifier", async (context) => {
  let payload: unknown = null;
  context.mock.method(globalThis, "fetch", async (
    _input: string | URL | Request,
    init?: RequestInit,
  ) => {
    payload = JSON.parse(String(init?.body));
    return new Response(JSON.stringify({
      type: "question",
      caseId,
      turnVersion: 1,
      questionId: "baseline_career_1",
      question: "哪一年或哪一月发生过明显的工作变化？",
      source: "fallback",
    }), { status: 200, headers: { "content-type": "application/json" } });
  });

  const response = await requestBirthTimeGuidePrompt(caseId);
  assert.deepEqual(payload, { type: "render_question", caseId });
  assert.equal(response.type, "question");
  assert.equal("nextAction" in response, false);
});

test("draft client round-trips identifiers without deterministic fields", async (context) => {
  let payload: unknown = null;
  context.mock.method(globalThis, "fetch", async (
    _input: string | URL | Request,
    init?: RequestInit,
  ) => {
    payload = JSON.parse(String(init?.body));
    return new Response(JSON.stringify({
      type: "evidence_draft",
      actionId,
      requestedTurnVersion: 1,
      turn: highConfirmationTurn,
    }), { status: 200, headers: { "content-type": "application/json" } });
  });

  const response = await draftBirthTimeEvidence(caseId, actionId, 1, "  2023 年 4 月换工作  ");
  assert.deepEqual(payload, {
    type: "draft_evidence",
    caseId,
    actionId,
    turnVersion: 1,
    message: "2023 年 4 月换工作",
  });
  assert.equal(response.actionId, actionId);
  assert.equal(response.turn.nextAction.kind, "request_candidate_confirmation");
});

test("a lost guide draft response replays the identical action receipt", async (context) => {
  const bodies: string[] = [];
  let attempts = 0;
  context.mock.method(globalThis, "fetch", async (_input: string | URL | Request, init?: RequestInit) => {
    attempts += 1;
    bodies.push(String(init?.body));
    if (attempts === 1) throw new TypeError("response lost");
    return new Response(JSON.stringify({
      type: "evidence_draft",
      actionId,
      requestedTurnVersion: 1,
      turn: highConfirmationTurn,
    }), { status: 200 });
  });

  const result = await draftBirthTimeEvidence(caseId, actionId, 1, "2023 年换工作");

  assert.equal(result.actionId, actionId);
  assert.equal(attempts, 2);
  assert.equal(bodies[0], bodies[1]);
});

test("guide client rejects raw model metadata and malformed nested turns", async (context) => {
  context.mock.method(globalThis, "fetch", async () => new Response(JSON.stringify({
    type: "question",
    caseId,
    turnVersion: 1,
    questionId: "baseline_career_1",
    question: "哪一年发生过工作变化？",
    source: "agent",
    model: "secret-model",
  }), { status: 200, headers: { "content-type": "application/json" } }));

  await assert.rejects(requestBirthTimeGuidePrompt(caseId));
});

test("dynamic guide commands send only public coordination fields", async (context) => {
  const payloads: unknown[] = [];
  context.mock.method(globalThis, "fetch", async (
    _input: string | URL | Request,
    init?: RequestInit,
  ) => {
    payloads.push(JSON.parse(String(init?.body)));
    return new Response(JSON.stringify(highConfirmationTurn), { status: 200 });
  });

  await generateDynamicBirthTimeQuestion(caseId, actionId, 4);
  await reframeUnmatchedBirthTimeAnswer({
    caseId,
    actionId,
    turnVersion: 5,
    questionId: "11111111-1111-4111-8111-111111111111",
    note: "  时间更早  ",
  });

  assert.deepEqual(payloads, [
    { type: "generate_dynamic_question", caseId, actionId, turnVersion: 4 },
    {
      type: "reframe_unmatched",
      caseId,
      actionId,
      turnVersion: 5,
      questionId: "11111111-1111-4111-8111-111111111111",
      note: "时间更早",
    },
  ]);
});
