import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  createRectificationHandoffService,
  rectificationQuestionFingerprint,
} from "../src/lib/rectification-handoff-service.ts";
import { createRectificationHandoffHandlers } from "../src/lib/rectification-handoff-route.ts";

const userId = "00000000-0000-4000-8000-000000002001";
const caseId = "00000000-0000-4000-8000-000000002002";
const actionId = "00000000-0000-4000-8000-000000002003";
const requestId = "00000000-0000-4000-8000-000000002004";
const question = "未来半年是否适合换工作？";

function turn(pendingQuestion: string | null = question) {
  return {
    caseId,
    journeyProtocol: "conversational-evidence-v3" as const,
    status: "completed" as const,
    turnVersion: 4,
    narrative: "候选时间已经确认。",
    candidate: {
      status: "confirmed" as const,
      representativeTime: "05:18",
      rangeStart: "05:16",
      rangeEnd: "05:20",
    },
    technicalReceipt: {
      calculationVersion: "rectification-v3",
      stableLayers: ["D1"],
      sensitiveLayers: ["D9"],
      candidateDifferenceRefs: ["candidate-05:18"],
    },
    evidenceRequest: null,
    evidenceRecap: [],
    actions: pendingQuestion ? ["continue_original_question" as const] : [],
    pendingConsultationQuestion: pendingQuestion,
  };
}

function handoff(status: "pending" | "claimed" | "in_progress" | "consumed") {
  return {
    caseId,
    turnVersion: 4,
    question,
    questionFingerprint: rectificationQuestionFingerprint(question),
    requestId,
    status,
    turn: turn(status === "consumed" ? null : question),
  };
}

test("server service binds begin and settlement to one case, claim, and request identity", async () => {
  const calls: Array<{ name: string; args: Readonly<Record<string, unknown>> }> = [];
  const service = createRectificationHandoffService({
    async rpc(name, args) {
      calls.push({ name, args });
      if (name === "begin_conversational_rectification_handoff_execution") {
        return {
          data: { status: "ready", requestId, billingReused: false, credits: 7 },
          error: null,
        };
      }
      if (name === "settle_conversational_rectification_handoff") {
        return { data: { status: "consumed", requestId, credits: 7 }, error: null };
      }
      return { data: null, error: { message: "unexpected_rpc" } };
    },
  });

  const execution = await service.beginExecution({
    userId,
    caseId,
    turnVersion: 4,
    claimActionId: actionId,
    requestId,
    question,
  });
  const settlement = await service.settle({
    userId,
    caseId,
    claimActionId: actionId,
    requestId,
    emitted: true,
  });

  assert.equal(execution.status, "ready");
  assert.equal(settlement.status, "consumed");
  assert.deepEqual(calls.map((call) => call.name), [
    "begin_conversational_rectification_handoff_execution",
    "settle_conversational_rectification_handoff",
  ]);
  assert.deepEqual(calls[0]?.args, {
    p_user_id: userId,
    p_case_id: caseId,
    p_expected_version: 4,
    p_claim_action_id: actionId,
    p_request_id: requestId,
    p_question_fingerprint: rectificationQuestionFingerprint(question),
  });
  assert.deepEqual(calls[1]?.args, {
    p_user_id: userId,
    p_case_id: caseId,
    p_claim_action_id: actionId,
    p_request_id: requestId,
    p_emitted: true,
  });
});

test("pre-output settlement releases the durable question for retry", async () => {
  const calls: unknown[] = [];
  const service = createRectificationHandoffService({
    async rpc(name, args) {
      calls.push({ name, args });
      return { data: { status: "pending", requestId, credits: 8 }, error: null };
    },
  });

  const result = await service.settle({
    userId,
    caseId,
    claimActionId: actionId,
    requestId,
    emitted: false,
  });

  assert.equal(result.status, "pending");
  assert.equal(calls.length, 1);
});

test("handoff route authenticates before parsing and returns owner-safe claim DTO", async () => {
  let serviceCalls = 0;
  const unauthenticated = createRectificationHandoffHandlers({
    authenticate: async () => null,
    service() {
      serviceCalls += 1;
      throw new Error("must not construct");
    },
  });
  const denied = await unauthenticated.post(new Request("https://example.invalid", {
    method: "POST",
    body: "not-json",
  }));
  assert.equal(denied.status, 401);
  assert.equal(serviceCalls, 0);

  const authenticated = createRectificationHandoffHandlers({
    authenticate: async () => ({ userId }),
    service() {
      return {
        attach: async () => turn(),
        load: async () => handoff("pending"),
        claim: async () => handoff("claimed"),
        beginExecution: async () => ({
          status: "ready" as const,
          requestId,
          billingReused: false,
          credits: 8,
        }),
        settle: async () => ({ status: "consumed" as const, requestId, credits: 8 }),
      };
    },
  });
  const response = await authenticated.post(new Request("https://example.invalid", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      type: "claim",
      caseId,
      turnVersion: 4,
      actionId,
      question,
    }),
  }));
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), handoff("claimed"));
});

test("migration keeps claim, billing recovery, settlement and ACL inside locked RPCs", () => {
  const sql = readFileSync(new URL(
    "../supabase/migrations/20260720040000_rectification_question_handoff.sql",
    import.meta.url,
  ), "utf8");

  assert.match(sql, /attach_conversational_rectification_question[\s\S]*for update[\s\S]*pending_consultation_question = p_question/i);
  assert.match(sql, /claim_conversational_rectification_handoff[\s\S]*for update[\s\S]*lease_expires_at/i);
  assert.match(sql, /begin_conversational_rectification_handoff_execution[\s\S]*billingReused[\s\S]*v_request_status = 'reserved'/i);
  assert.match(sql, /settle_conversational_rectification_handoff[\s\S]*complete_consultation_credit[\s\S]*cancel_consultation_credit/i);
  assert.match(sql, /consume_conversational_rectification_handoff[\s\S]*continue_original_question/i);
  assert.match(sql, /consume_conversational_rectification_handoff[\s\S]*pending_consultation_question = null/i);
  for (const functionName of [
    "attach_conversational_rectification_question",
    "load_conversational_rectification_handoff",
    "claim_conversational_rectification_handoff",
    "begin_conversational_rectification_handoff_execution",
    "settle_conversational_rectification_handoff",
  ]) {
    assert.match(sql, new RegExp(`revoke all on function public\\.${functionName}\\([\\s\\S]*?from public, anon, authenticated`, "i"));
    assert.match(sql, new RegExp(`grant execute on function public\\.${functionName}\\([\\s\\S]*?to service_role`, "i"));
  }
});

test("expired handoff leases project as pending so another device can reclaim them", () => {
  const sql = readFileSync(new URL(
    "../supabase/migrations/20260722120000_recover_expired_rectification_handoff.sql",
    import.meta.url,
  ), "utf8");

  assert.match(
    sql,
    /h\.state in \('claimed', 'executing'\)[\s\S]*h\.lease_expires_at <= pg_catalog\.now\(\)[\s\S]*then 'pending'/i,
  );
  assert.match(sql, /create or replace function public\.conversational_rectification_handoff_projection/i);
});
