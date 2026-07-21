import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { ConversationalRectificationSurface } from "../src/components/conversational-birth-time-rectification.tsx";
import { createConversationalRectificationController } from "../src/hooks/use-conversational-rectification.ts";
import type { ConversationalRectificationController } from "../src/hooks/use-conversational-rectification.ts";
import { prepareConsultationRoute } from "../src/lib/consultation-route-service.ts";
import type { ConversationalRectificationTurn } from "../src/lib/conversational-rectification/contracts.ts";
import {
  createRectificationQuestionHandoffCoordinator,
} from "../src/lib/rectification-question-handoff.ts";

Object.assign(globalThis, { React });

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

function controllerFor(turn: ConversationalRectificationTurn): ConversationalRectificationController {
  const snapshot = {
    turn,
    draft: "",
    selectedDomain: null,
    correctionTarget: null,
    pending: false,
    error: "",
  } as const;
  return {
    ...snapshot,
    getSnapshot: () => snapshot,
    subscribe: () => () => undefined,
    synchronizeInitialTurn: () => undefined,
    setDraft: () => undefined,
    selectDomain: () => undefined,
    beginEvidenceCorrection: () => undefined,
    cancelEvidenceCorrection: () => undefined,
    start: async () => turn,
    resume: async () => turn,
    answer: async () => turn,
    pause: async () => turn,
    abandon: async () => turn,
    confirm: async () => turn,
  };
}

test("confirmed surface requires an explicit click before continuing the original question", () => {
  let continuationCalls = 0;
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    {
      controller: controllerFor(confirmedTurn()),
      onContinueOriginalQuestion: () => { continuationCalls += 1; },
    },
  ));

  assert.match(markup, /原问题：未来半年是否适合换工作？/);
  assert.match(markup, />使用新确认时间继续回答原问题</);
  assert.equal(continuationCalls, 0);
});

test("continuation action is visibly locked while ordinary consultation is pending", () => {
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    {
      controller: controllerFor(confirmedTurn()),
      continuationPending: true,
      onContinueOriginalQuestion: () => undefined,
    },
  ));

  assert.match(markup, /<button[^>]+disabled=""[^>]*>正在继续回答原问题…<\/button>/);
});

test("choosing rectify-first captures the visible question and passes it only to v3 start", async () => {
  const coordinator = createRectificationQuestionHandoffCoordinator<"career" | "general">();
  const commands: unknown[] = [];
  const handoff = coordinator.capture({
    question: `  ${pendingQuestion}  `,
    sessionId: "session-original",
    theme: "career",
  });
  const firstTurn: ConversationalRectificationTurn = {
    ...confirmedTurn(),
    status: "active" as const,
    turnVersion: 0,
    candidate: {
      ...confirmedTurn().candidate,
      status: "pending_validation" as const,
    },
    actions: ["answer", "pause", "abandon"],
  };
  const rectification = createConversationalRectificationController({
    async send(command) {
      commands.push(command);
      return firstTurn;
    },
    createActionId: () => "00000000-0000-4000-8000-000000001011",
  });

  await rectification.start(handoff.question);

  assert.deepEqual(commands, [{
    type: "start",
    actionId: "00000000-0000-4000-8000-000000001011",
    pendingConsultationQuestion: pendingQuestion,
  }]);
});

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

test("homepage wires the tested handoff coordinator without carrying hidden rectification routing", () => {
  const page = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const chooseStart = page.indexOf("function rectifyBeforePendingConsultation");
  const chooseEnd = page.indexOf("function cancelPendingBirthTimeChoice", chooseStart);
  const chooseHandler = page.slice(chooseStart, chooseEnd);
  const continuationStart = page.indexOf("async function continueRectificationOriginalQuestion");
  const continuationEnd = page.indexOf("function restoreQuestionFromRectification", continuationStart);
  const continuationHandler = page.slice(continuationStart, continuationEnd);
  const restoreStart = continuationEnd;
  const restoreEnd = page.indexOf("function useUnverifiedTimeForPendingConsultation", restoreStart);
  const restoreHandler = page.slice(restoreStart, restoreEnd);

  assert.match(page, /createRectificationQuestionHandoffCoordinator/);
  assert.match(chooseHandler, /\.capture\(\{[\s\S]*question:\s*pending\.question,[\s\S]*sessionId:\s*pending\.sessionId,[\s\S]*theme:\s*pending\.theme/);
  assert.doesNotMatch(chooseHandler, /\/api\/consult|\bsend\(/);
  assert.match(continuationHandler, /continueOriginalQuestion\(/);
  assert.match(continuationHandler, /send\(context\.question, context\.theme, null, null, context\.sessionId\)/);
  assert.match(continuationHandler, /if \(completed\)[\s\S]*setRectificationSurfaceOpen\(false\)/);
  assert.match(restoreHandler, /setDraft\(handoff\.question\)/);
  assert.match(restoreHandler, /setDraftTheme\(handoff\.theme\)/);
  assert.match(restoreHandler, /setDraftEntrypoint\(null\)/);
  assert.doesNotMatch(restoreHandler, /\/api\/consult|\bsend\(/);
  assert.match(page, /continuationPending=\{rectificationContinuationPending\}/);
  assert.match(page, /onContinueOriginalQuestion=\{\(question\) => void continueRectificationOriginalQuestion\(question\)\}/);
  assert.match(page, /\? "返回并恢复原问题"\s*:\s*"返回首页"/);
});

test("ordinary consult remains strict and bills the confirmed continuation through the normal route", () => {
  const route = readFileSync(new URL("../src/app/api/consult/route.ts", import.meta.url), "utf8");
  const chartSchema = route.slice(
    route.indexOf("const chartChatRequestSchema"),
    route.indexOf("const generalChatRequestSchema"),
  );
  const parse = route.indexOf("chatRequestSchema.safeParse");
  const legacyRejection = route.indexOf('parsed.data.entrypoint === "birth_time_rectification"', parse);
  const prepare = route.indexOf("prepareConsultationRoute({", parse);
  const reserve = route.indexOf("reserveConsultationModel(", prepare);

  assert.match(chartSchema, /consultationInputSchema\.extend\([\s\S]*?\)\.strict\(\);/);
  assert.doesNotMatch(route, /continue_original_question|rectificationHandoff|skipBilling/);
  assert.ok(parse >= 0 && legacyRejection > parse && prepare > legacyRejection && reserve > prepare);
  assert.match(route, /"begin_consultation_credit"/);
  assert.match(route, /"complete_consultation_credit"/);
  assert.match(route, /"cancel_consultation_credit"/);
});
