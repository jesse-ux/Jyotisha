import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  consultationEntrypointSchema,
  resolveConsultationQuestion,
} from "../src/lib/consultation-entrypoint.ts";

test("plain consultation questions remain user-authored", () => {
  // Given: an ordinary question without a product entrypoint.
  const visibleQuestion = "未来半年适合换工作吗？";

  // When: the server resolves the model-facing question.
  const resolved = resolveConsultationQuestion({
    visibleQuestion,
    entrypoint: undefined,
    currentDate: "2026-07-19",
  });

  // Then: the server does not rewrite ordinary user input.
  assert.deepEqual(resolved, { kind: "plain", modelQuestion: visibleQuestion });
});

test("daily entrypoint selects a private server expansion", () => {
  // Given: the public short label and its closed entrypoint identity.
  const visibleQuestion = "深入看今日";

  // When: the server resolves the request.
  const resolved = resolveConsultationQuestion({
    visibleQuestion,
    entrypoint: "daily_starlanguage",
    currentDate: "2026-07-19",
  });

  // Then: routing is explicit and the model receives more than the public label.
  assert.equal(resolved.kind, "expanded");
  assert.notEqual(resolved.modelQuestion, visibleQuestion);
});

test("birth-time entrypoint selects a private server expansion", () => {
  // Given: a completed profile starts another rectification from a public label.
  const visibleQuestion = "再次校正";

  // When: the server resolves the request.
  const resolved = resolveConsultationQuestion({
    visibleQuestion,
    entrypoint: "birth_time_rectification",
    currentDate: "2026-07-19",
  });

  // Then: the model question is expanded without changing the visible transcript.
  assert.equal(resolved.kind, "expanded");
  assert.notEqual(resolved.modelQuestion, visibleQuestion);
});

test("consultation entrypoints form a closed public request enum", () => {
  assert.equal(consultationEntrypointSchema.safeParse("daily_starlanguage").success, true);
  assert.equal(consultationEntrypointSchema.safeParse("birth_time_rectification").success, true);
  assert.equal(consultationEntrypointSchema.safeParse("client_prompt").success, false);
});

test("browser source does not own private entrypoint prompts", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");

  assert.doesNotMatch(source, /function buildDailyStarlanguageQuestion/);
  assert.doesNotMatch(source, /function buildBirthTimeRectificationQuestion/);
  assert.doesNotMatch(source, /请结合已校验的星盘资料/);
  assert.doesNotMatch(source, /请基于已校验的出生资料继续/);
});

test("ordinary product drafts keep the public question and clear hidden routing after edits", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");

  assert.match(source, /chooseSuggestedQuestion\("深入看今日",[\s\S]*?"timing",[\s\S]*?"daily_starlanguage"\)/);
  assert.match(source, /messages:\s*\[\.\.\.preservedMessages,[\s\S]*?\{ role: "user", text: question \}\]/);
  assert.match(source, /body:\s*JSON\.stringify\(\{[\s\S]*?entrypoint:\s*entrypoint \?\? undefined,[\s\S]*?question,/);
  assert.match(source, /onChange=\{\(event\) => \{[\s\S]*?setDraft\(event\.target\.value\);[\s\S]*?setDraftTheme\(null\);[\s\S]*?setDraftEntrypoint\(null\);/);
  assert.match(source, /setDraft\(pending\.question\);[\s\S]*?setDraftTheme\(pending\.theme\);[\s\S]*?setDraftEntrypoint\(pending\.entrypoint\);/);
});

test("homepage birth-time card opens the v3 surface instead of ordinary consultation", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");

  assert.match(source, /function openBirthTimeRectification/);
  assert.match(source, /<ConversationalBirthTimeRectification/);
  assert.match(source, /rectificationPriceCredits/);
  assert.doesNotMatch(source, /chooseSuggestedQuestion\([\s\S]{0,180}"birth_time_rectification"/);
  assert.doesNotMatch(source, /draftBirthTimeRectificationQuestion/);
});

test("ordinary consultation is softly diverted before calling consult", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const sendStart = source.indexOf("async function send(");
  const consultCall = source.indexOf('fetch("/api/consult"', sendStart);
  const softChoice = source.indexOf("setPendingBirthTimeChoice", sendStart);

  assert.ok(sendStart >= 0);
  assert.ok(softChoice > sendStart && softChoice < consultCall);
  assert.match(source, /grantBirthTimeConsultationConsent\([\s\S]*activeSession\.id/);
  assert.match(source, /pendingConsultationQuestion=/);
});

test("minute-free choice restores an editable general question without an immediate network call or charge", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const start = source.indexOf("function continueGenerallyWithoutBirthTime");
  const end = source.indexOf("function rectifyBeforePendingConsultation", start);
  const handler = source.slice(start, end);

  assert.match(handler, /"general_no_birth_time"/);
  assert.match(handler, /setDraft\(pending\.question\)/);
  assert.match(handler, /setDraftEntrypoint\(null\)/);
  assert.match(handler, /尚未发送，也没有扣点/);
  assert.doesNotMatch(handler, /fetch\(|void send\(|send\(/);
});

test("rectification mutations report pending state to the page and lock card and return actions", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");

  assert.match(source, /onPendingChange=\{setRectificationMutationPending\}/);
  assert.match(source, /disabled=\{productEntrypointsDisabled \|\| rectificationLoading \|\| rectificationMutationPending\}/);
  assert.match(source, /disabled=\{rectificationLoading \|\| rectificationMutationPending\}/);
  assert.match(source, /if \(!rectificationLoading && !rectificationMutationPending\)/);
});

test("switching chats hides rather than destroys another chat's pending soft choice", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const selectSession = source.slice(
    source.indexOf("function selectSession("),
    source.indexOf("async function selectSessionModel", source.indexOf("function selectSession(")),
  );

  assert.doesNotMatch(selectSession, /setPendingBirthTimeChoice\(null\)/);
  assert.match(source, /pendingBirthTimeChoice\?\.sessionId === activeSession\?\.id/);
});

test("profile and place saves do not auto-start the retired assessment flow", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const normalSave = source.slice(source.indexOf("async function saveProfile"), source.indexOf("async function saveOnboardingName"));
  const placeSave = source.slice(source.indexOf("async function saveOnboardingPlace"), source.indexOf("function completeGuidedBirthTime"));

  assert.doesNotMatch(normalSave, /assessSavedBirthTime|requestBirthTimeAssessment/);
  assert.doesNotMatch(placeSave, /assessSavedBirthTime|requestBirthTimeAssessment/);
});

test("consult route expands an optional entrypoint for both Agent and tool input", () => {
  const source = readFileSync(new URL("../src/app/api/consult/route.ts", import.meta.url), "utf8");

  assert.match(source, /entrypoint:\s*consultationEntrypointSchema\.optional\(\)/);
  assert.match(source, /question:\s*resolvedQuestion\.modelQuestion/);
  assert.match(source, /resolvedQuestion\.modelQuestion,[\s\S]*?"\\n需要查询星盘时/);
});

test("homepage entrypoints use two whole-card native actions", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const wholeCardActions = source.match(/className="product-entrypoint-hitarea"/g) ?? [];

  assert.equal(wholeCardActions.length, 2);
  assert.doesNotMatch(source, /className="daily-starlanguage-heading">[\s\S]{0,180}<button/);
});
