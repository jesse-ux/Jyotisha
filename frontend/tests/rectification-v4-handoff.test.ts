import assert from "node:assert/strict";
import test, { mock } from "node:test";

import {
  createRectificationV4HandoffService,
  rectificationQuestionFingerprint,
} from "../src/lib/rectification-handoff-service.ts";
import { claimRectificationV4Handoff } from "../src/lib/rectification-v4/client.ts";

const userId = "00000000-0000-4000-8000-000000004001";
const caseId = "00000000-0000-4000-8000-000000004002";
const actionId = "00000000-0000-4000-8000-000000004003";
const requestId = "00000000-0000-4000-8000-000000004004";
const question = "未来半年是否适合换工作？";
const acceptedRange = { start: "05:13", end: "05:15" } as const;

function projection(status: "pending" | "claimed" | "in_progress" | "consumed") {
  return {
    protocol: "rectification-evidence-v4" as const,
    caseId,
    caseVersion: 7,
    question,
    questionFingerprint: rectificationQuestionFingerprint(question),
    requestId,
    status,
    acceptedRange,
  };
}

test("v4 handoff adapter binds all RPCs to case, version, action, request, and database range", async () => {
  const calls: Array<{ name: string; args: Readonly<Record<string, unknown>> }> = [];
  const service = createRectificationV4HandoffService({
    async rpc(name, args) {
      calls.push({ name, args });
      if (name === "load_birth_time_rectification_v4_handoff") return { data: projection("pending"), error: null };
      if (name === "begin_birth_time_rectification_v4_handoff_execution") {
        return { data: { status: "ready", requestId, billingReused: false, credits: 8, acceptedRange }, error: null };
      }
      if (name === "settle_birth_time_rectification_v4_handoff") {
        return { data: { status: "consumed", requestId, credits: 8 }, error: null };
      }
      return { data: projection(name.startsWith("claim_") ? "claimed" : "pending"), error: null };
    },
  });

  await service.attach({ userId, caseId, caseVersion: 7, actionId, question: ` ${question} ` });
  await service.load({ userId, caseId });
  await service.claim({ userId, caseId, caseVersion: 7, actionId, question });
  const execution = await service.beginExecution({ userId, caseId, caseVersion: 7, claimActionId: actionId, requestId, question });
  await service.settle({ userId, caseId, claimActionId: actionId, requestId, emitted: true });

  assert.deepEqual(calls.map(({ name }) => name), [
    "attach_birth_time_rectification_v4_question",
    "load_birth_time_rectification_v4_handoff",
    "claim_birth_time_rectification_v4_handoff",
    "begin_birth_time_rectification_v4_handoff_execution",
    "settle_birth_time_rectification_v4_handoff",
  ]);
  assert.deepEqual(calls[0]?.args, {
    p_user_id: userId,
    p_case_id: caseId,
    p_expected_version: 7,
    p_action_id: actionId,
    p_question: question,
    p_question_fingerprint: rectificationQuestionFingerprint(question),
  });
  assert.deepEqual(calls[2]?.args, {
    p_user_id: userId,
    p_case_id: caseId,
    p_expected_version: 7,
    p_action_id: actionId,
    p_question_fingerprint: rectificationQuestionFingerprint(question),
  });
  assert.deepEqual(calls[3]?.args, {
    p_user_id: userId,
    p_case_id: caseId,
    p_expected_version: 7,
    p_claim_action_id: actionId,
    p_request_id: requestId,
    p_question_fingerprint: rectificationQuestionFingerprint(question),
  });
  assert.deepEqual(calls[4]?.args, {
    p_user_id: userId,
    p_case_id: caseId,
    p_claim_action_id: actionId,
    p_request_id: requestId,
    p_emitted: true,
  });
  assert.deepEqual(execution.acceptedRange, acceptedRange);
});

test("lost v4 claim response retries with the same action id", async () => {
  const bodies: Array<Record<string, unknown>> = [];
  let attempts = 0;
  mock.method(globalThis, "fetch", async (_url: string | URL | Request, init?: RequestInit) => {
    bodies.push(JSON.parse(String(init?.body)) as Record<string, unknown>);
    attempts += 1;
    if (attempts === 1) throw new TypeError("lost response");
    return Response.json(projection("claimed"));
  });
  try {
    const claimed = await claimRectificationV4Handoff({ caseId, caseVersion: 7, question });
    assert.equal(claimed.status, "claimed");
    assert.equal(bodies.length, 2);
    assert.equal(bodies[0]?.actionId, bodies[1]?.actionId);
    assert.equal(claimed.claimActionId, bodies[1]?.actionId);
  } finally {
    mock.restoreAll();
  }
});
