import assert from "node:assert/strict";
import test from "node:test";
import { prepareConsultationRoute } from "../src/lib/consultation-route-service.ts";
import type { ConversationalRectificationTurn } from "../src/lib/conversational-rectification/contracts.ts";
import {
  createDurableRectificationQuestionHandoffClient,
  createRectificationQuestionHandoffCoordinator,
} from "../src/lib/rectification-question-handoff.ts";

const pendingQuestion = "未来半年是否适合换工作？";

function confirmedTurn(): ConversationalRectificationTurn {
  return {
    caseId: "00000000-0000-4000-8000-000000001010",
    journeyProtocol: "conversational-evidence-v3",
    status: "completed",
    turnVersion: 5,
    narrative: "候选时间已经完成确认。",
    candidate: {
      status: "confirmed",
      representativeTime: "05:18",
      rangeStart: "05:16",
      rangeEnd: "05:20",
    },
    technicalReceipt: {
      calculationVersion: "rectification-technical-v1",
      stableLayers: ["D1"],
      sensitiveLayers: ["D9", "D10"],
      candidateDifferenceRefs: ["candidate-05:18"],
    },
    evidenceRequest: null,
    evidenceRecap: [],
    actions: ["continue_original_question"],
    pendingConsultationQuestion: pendingQuestion,
  };
}

test("pause, refresh, and a new device recover the durable question without losing local session and theme", () => {
  const paused = {
    ...confirmedTurn(),
    status: "paused" as const,
    candidate: {
      ...confirmedTurn().candidate,
      status: "pending_validation" as const,
    },
    actions: ["answer", "abandon"] as const,
  };
  const local = createRectificationQuestionHandoffCoordinator<"career" | "timing">();
  local.capture({ question: pendingQuestion, sessionId: "session-original", theme: "career" });

  assert.deepEqual(local.synchronizeDurableQuestion(
    paused.pendingConsultationQuestion,
    { sessionId: "session-after-refresh", theme: "timing" },
  ), {
    question: pendingQuestion,
    sessionId: "session-original",
    theme: "career",
  });

  const newDevice = createRectificationQuestionHandoffCoordinator<"career" | "timing">();
  assert.deepEqual(newDevice.synchronizeDurableQuestion(
    paused.pendingConsultationQuestion,
    { sessionId: "session-current-device", theme: "timing" },
  ), {
    question: pendingQuestion,
    sessionId: "session-current-device",
    theme: "timing",
  });
});

test("explicit continuation uses the confirmed server profile, original session and theme, and one normal reservation", async () => {
  const coordinator = createRectificationQuestionHandoffCoordinator<"career" | "timing">();
  coordinator.capture({ question: pendingQuestion, sessionId: "session-original", theme: "career" });
  let consultationCalls = 0;
  let reservationCalls = 0;
  let selectedMinute = -1;
  let sentContext: unknown = null;

  const continued = await coordinator.continueOriginalQuestion(
    pendingQuestion,
    { sessionId: "session-fallback", theme: "timing" },
    async (context) => {
      consultationCalls += 1;
      sentContext = context;
      const prepared = await prepareConsultationRoute({
        userId: "synthetic-user",
        mode: "verified_chart",
        loadProfile: async () => ({
          name: "测试用户",
          birth_date: "1990-01-02",
          reported_birth_time: "05:30:00",
          active_birth_time: "05:18:00",
          birth_time_source: "approximate",
          birth_time_status: "confirmed",
          country_code: "CN",
          province_code: "130000",
          city_code: "130400",
          district_code: "130406",
          latitude: 36.420487,
          longitude: 114.209936,
          timezone_offset: 8,
        }),
        reserve: async () => {
          reservationCalls += 1;
          return "reserved";
        },
      });
      selectedMinute = prepared.serverChart?.toolInput.minute ?? -1;
      return true;
    },
  );

  assert.equal(continued, true);
  assert.deepEqual(sentContext, {
    question: pendingQuestion,
    sessionId: "session-original",
    theme: "career",
  });
  assert.equal(selectedMinute, 18);
  assert.equal(consultationCalls, 1);
  assert.equal(reservationCalls, 1);
  assert.equal(coordinator.peek(), null);
});

test("double click shares one in-flight continuation and cannot reserve twice", async () => {
  const coordinator = createRectificationQuestionHandoffCoordinator<"career">();
  coordinator.capture({ question: pendingQuestion, sessionId: "session-original", theme: "career" });
  let release!: (success: boolean) => void;
  const result = new Promise<boolean>((resolve) => { release = resolve; });
  let consultationCalls = 0;
  const send = async () => {
    consultationCalls += 1;
    return result;
  };

  const first = coordinator.continueOriginalQuestion(
    pendingQuestion,
    { sessionId: "session-fallback", theme: "career" },
    send,
  );
  const second = coordinator.continueOriginalQuestion(
    pendingQuestion,
    { sessionId: "session-fallback", theme: "career" },
    send,
  );
  release(true);

  assert.equal(await first, true);
  assert.equal(await second, true);
  assert.equal(consultationCalls, 1);
  assert.equal(await coordinator.continueOriginalQuestion(
    pendingQuestion,
    { sessionId: "session-fallback", theme: "career" },
    send,
  ), false);
  assert.equal(consultationCalls, 1);
});

test("failed continuation keeps the question and can retry once the pending lock releases", async () => {
  const coordinator = createRectificationQuestionHandoffCoordinator<"career">();
  const expected = coordinator.capture({
    question: pendingQuestion,
    sessionId: "session-original",
    theme: "career",
  });
  let attempts = 0;
  const send = async () => {
    attempts += 1;
    return attempts > 1;
  };

  assert.equal(await coordinator.continueOriginalQuestion(
    pendingQuestion,
    { sessionId: "session-fallback", theme: "career" },
    send,
  ), false);
  assert.deepEqual(coordinator.peek(), expected);

  assert.equal(await coordinator.continueOriginalQuestion(
    pendingQuestion,
    { sessionId: "session-fallback", theme: "career" },
    send,
  ), true);
  assert.equal(attempts, 2);
  assert.equal(coordinator.peek(), null);
});

test("returning from rectification restores the composer context without consulting or charging", () => {
  const coordinator = createRectificationQuestionHandoffCoordinator<"career" | "timing">();
  const restored = coordinator.synchronizeDurableQuestion(
    pendingQuestion,
    { sessionId: "session-current", theme: "timing" },
  );
  coordinator.clear();

  assert.deepEqual(restored, {
    question: pendingQuestion,
    sessionId: "session-current",
    theme: "timing",
  });
  assert.equal(coordinator.peek(), null);
});

test("lost claim responses replay one stable action and durable request identity", async () => {
  const actionId = "00000000-0000-4000-8000-000000001099";
  const requestId = "00000000-0000-4000-8000-000000001098";
  const bodies: Array<Record<string, unknown>> = [];
  let attempt = 0;
  const client = createDurableRectificationQuestionHandoffClient({
    createActionId: () => actionId,
    async fetch(_url, init) {
      const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
      bodies.push(body);
      attempt += 1;
      if (attempt === 1) throw new TypeError("lost response");
      return Response.json({
        caseId: confirmedTurn().caseId,
        turnVersion: confirmedTurn().turnVersion,
        question: pendingQuestion,
        questionFingerprint: "a".repeat(64),
        requestId,
        status: "claimed",
        turn: confirmedTurn(),
      });
    },
  });

  const claimed = await client.claim({
    caseId: confirmedTurn().caseId,
    turnVersion: confirmedTurn().turnVersion,
    question: pendingQuestion,
  });

  assert.equal(claimed.claimActionId, actionId);
  assert.equal(claimed.requestId, requestId);
  assert.equal(bodies.length, 2);
  assert.equal(bodies[0]?.actionId, actionId);
  assert.deepEqual(bodies[1], bodies[0]);
});

test("two independent devices cannot both claim the same confirmed question", async () => {
  let owner: string | null = null;
  let claimCalls = 0;
  const requestId = "00000000-0000-4000-8000-000000001097";
  const transport = async (_url: RequestInfo | URL, init?: RequestInit) => {
    const command = JSON.parse(String(init?.body)) as { actionId: string };
    claimCalls += 1;
    const status = owner === null || owner === command.actionId ? "claimed" : "in_progress";
    owner ??= command.actionId;
    return Response.json({
      caseId: confirmedTurn().caseId,
      turnVersion: confirmedTurn().turnVersion,
      question: pendingQuestion,
      questionFingerprint: "b".repeat(64),
      requestId,
      status,
      turn: confirmedTurn(),
    });
  };
  const first = createDurableRectificationQuestionHandoffClient({
    fetch: transport,
    createActionId: () => "00000000-0000-4000-8000-000000001091",
  });
  const second = createDurableRectificationQuestionHandoffClient({
    fetch: transport,
    createActionId: () => "00000000-0000-4000-8000-000000001092",
  });

  const [firstResult, secondResult] = await Promise.all([
    first.claim({ caseId: confirmedTurn().caseId, turnVersion: 5, question: pendingQuestion }),
    second.claim({ caseId: confirmedTurn().caseId, turnVersion: 5, question: pendingQuestion }),
  ]);

  assert.equal(firstResult.status, "claimed");
  assert.equal(secondResult.status, "in_progress");
  assert.equal(firstResult.requestId, secondResult.requestId);
  assert.equal(claimCalls, 2);
});

test("refresh restores only the server-owned pending question and replacement wins", async () => {
  let durableQuestion = "旧问题";
  const client = createDurableRectificationQuestionHandoffClient({
    createActionId: () => "00000000-0000-4000-8000-000000001093",
    async fetch(_url, init) {
      if (init?.method === "GET") {
        return Response.json({
          caseId: confirmedTurn().caseId,
          turnVersion: 5,
          question: durableQuestion,
          questionFingerprint: "c".repeat(64),
          requestId: "00000000-0000-4000-8000-000000001094",
          status: "pending",
          turn: { ...confirmedTurn(), pendingConsultationQuestion: durableQuestion },
        });
      }
      const command = JSON.parse(String(init?.body)) as { question: string };
      durableQuestion = command.question;
      return Response.json({ ...confirmedTurn(), pendingConsultationQuestion: durableQuestion });
    },
  });

  const replaced = await client.attach({
    caseId: confirmedTurn().caseId,
    turnVersion: 5,
    question: "新问题",
  });
  const refreshed = await client.load();

  assert.equal(replaced.pendingConsultationQuestion, "新问题");
  assert.equal(refreshed?.question, "新问题");
  assert.equal(refreshed?.turn.pendingConsultationQuestion, "新问题");
});
