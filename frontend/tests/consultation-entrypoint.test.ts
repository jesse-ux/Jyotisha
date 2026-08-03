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

  assert.match(source, /personalChartAvailable \? "深入看今日"[\s\S]*?"timing",[\s\S]*?personalChartAvailable \? "daily_starlanguage" : null/);
  assert.match(source, /messages:\s*\[\.\.\.preservedMessages,[\s\S]*?\{ role: "user", text: question \}\]/);
  assert.match(source, /body:\s*JSON\.stringify\(\{[\s\S]*?entrypoint:\s*entrypoint \?\? undefined,[\s\S]*?question,/);
  assert.match(source, /onChange=\{\(event\) => \{[\s\S]*?setDraft\(event\.target\.value\);[\s\S]*?setDraftTheme\(null\);[\s\S]*?setDraftEntrypoint\(null\);/);
  assert.match(source, /setDraft\(pending\.question\);[\s\S]*?setDraftTheme\(pending\.theme\);[\s\S]*?setDraftEntrypoint\(pending\.entrypoint\);/);
});

test("homepage birth-time card opens the latest Agentic surface instead of ordinary consultation", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const component = readFileSync(new URL("../src/components/conversational-birth-time-rectification.tsx", import.meta.url), "utf8");

  assert.match(source, /function openBirthTimeRectification/);
  assert.match(source, /<ConversationalBirthTimeRectification/);
  assert.match(component, /<AgenticRectificationChat \{\.\.\.props\} \/>/);
  assert.doesNotMatch(component, /RectificationV4Panel|loadActiveRectificationV4|transitionRectificationV4/);
  assert.match(source, /pendingConsultationQuestion=\{rectificationPendingQuestion\}/);
  assert.doesNotMatch(source.slice(
    source.indexOf("async function openBirthTimeRectification"),
    source.indexOf("function handleConversationalRectificationTurn"),
  ), /sendConversationalRectificationCommand|rectification\/v4/);
  assert.doesNotMatch(source, /chooseSuggestedQuestion\([\s\S]{0,180}"birth_time_rectification"/);
  assert.doesNotMatch(source, /draftBirthTimeRectificationQuestion/);
});

test("homepage mounts the Agentic surface without invoking retired rectification starters", () => {
  const page = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const component = readFileSync(new URL("../src/components/conversational-birth-time-rectification.tsx", import.meta.url), "utf8");
  const chat = readFileSync(new URL("../src/components/rectification-agentic-chat.tsx", import.meta.url), "utf8");
  const start = page.indexOf("async function openBirthTimeRectification");
  const end = page.indexOf("function handleConversationalRectificationTurn", start);
  const handler = page.slice(start, end);

  assert.doesNotMatch(handler, /sendConversationalRectificationCommand|loadRectificationV4Handoff|createRectificationV4/);
  assert.match(page, /<ConversationalBirthTimeRectification/);
  assert.match(component, /<AgenticRectificationChat/);
  assert.match(chat, /void send\(\{ action: "opening" \}, false\)/);
});

test("a stale v4 mutation refreshes the same case after a 409", () => {
  const hook = readFileSync(new URL("../src/hooks/use-rectification-v4.ts", import.meta.url), "utf8");

  assert.match(hook, /caught instanceof RectificationV4RequestError && caught\.status === 409 && data/);
  assert.match(hook, /await refresh\(data\.case\.id\)/);
  assert.match(hook, /loadRectificationV4\(caseId\)/);
});

test("homepage birth-time card opens its dedicated session before the Agent starts", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const start = source.indexOf("async function openBirthTimeRectification");
  const end = source.indexOf("function handleConversationalRectificationTurn", start);
  const handler = source.slice(start, end);
  const create = handler.indexOf('createSession(modelCatalog.defaultModelId, "birth_time_rectification")');
  const firstAwait = handler.indexOf("await ");
  const reveal = handler.indexOf("setActiveSessionId(rectificationSession.id)");

  assert.ok(create >= 0);
  assert.ok(firstAwait > create);
  assert.ok(reveal > create && reveal < firstAwait);
  assert.ok(handler.indexOf("setSessions((current) => [") < firstAwait);
  assert.match(handler, /rectificationOpenInFlight\.current/);
  assert.match(handler, /rectificationOpenInFlight\.current = true;[\s\S]*?finally \{[\s\S]*?rectificationOpenInFlight\.current = false;/);
  assert.doesNotMatch(handler, /onNarrativeDelta|sendConversationalRectificationCommand/);
  assert.match(source, /const rectificationSurfaceOpen = activeRectificationSession\s*&& activeSession\.id === rectificationSessionId/);
  assert.match(source, /rectificationSurfaceOpen && \([\s\S]*?<ConversationalBirthTimeRectification[\s\S]*?pendingConsultationQuestion=\{rectificationPendingQuestion\}/);
});

test("the page persists only the dedicated session shell while the Agent owns opening", () => {
  const page = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const component = readFileSync(new URL("../src/components/conversational-birth-time-rectification.tsx", import.meta.url), "utf8");
  const start = page.indexOf("async function openBirthTimeRectification");
  const end = page.indexOf("function handleConversationalRectificationTurn", start);
  const handler = page.slice(start, end);

  assert.match(handler, /persistSession\(rectificationSession, "create"\)/);
  assert.match(component, /<AgenticRectificationChat/);
  assert.doesNotMatch(component, /loadRectificationV4Handoff|createRectificationV4/);
});

test("a direct homepage start does not restore or create a V4 case", () => {
  const page = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const component = readFileSync(new URL("../src/components/conversational-birth-time-rectification.tsx", import.meta.url), "utf8");
  const start = page.indexOf("async function openBirthTimeRectification");
  const end = page.indexOf("function handleConversationalRectificationTurn", start);
  const handler = page.slice(start, end);

  assert.doesNotMatch(handler, /loadRectificationV4Handoff|createRectificationV4|rectification\/v4/);
  assert.doesNotMatch(component, /loadRectificationV4Handoff|createRectificationV4|RectificationV4Panel/);
});

test("rectification cards render only inside the active rectification session", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");

  assert.match(source, /activeSession\?\.sessionType === "birth_time_rectification"/);
  assert.match(source, /session_type:\s*session\.sessionType/);
  assert.match(source, /rectification_case_id:\s*session\.rectificationCaseId/);
  assert.doesNotMatch(source, /这个会话保存了生时校正入口|恢复生时校正<\/button>/);
});

test("selecting a rectification session resumes it without an intermediate confirmation", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const selectSession = source.slice(
    source.indexOf("function selectSession("),
    source.indexOf("async function selectSessionModel", source.indexOf("function selectSession(")),
  );

  assert.match(selectSession, /nextSession\?\.sessionType === "birth_time_rectification"/);
  assert.match(selectSession, /resumeRectificationSession\.current\(nextSession\)/);
  assert.match(source, /resumeRectificationSession\.current\(activeSession\)/);
  assert.doesNotMatch(source, /RectificationLoadingState|重试恢复/);
  assert.match(source, /<ConversationalBirthTimeRectification/);
});

test("homepage reuses the dedicated rectification session for the Agentic surface", () => {
  const page = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const component = readFileSync(new URL("../src/components/conversational-birth-time-rectification.tsx", import.meta.url), "utf8");
  const start = page.indexOf("async function openBirthTimeRectification");
  const end = page.indexOf("function handleConversationalRectificationTurn", start);
  const handler = page.slice(start, end);

  assert.match(handler, /sessions\.find\(\(session\) => session\.sessionType === "birth_time_rectification"\)/);
  assert.match(handler, /existing \?\? createSession/);
  assert.match(component, /<AgenticRectificationChat/);
});

test("a bound rectification session and homepage restart share the same Agentic session shell", () => {
  const page = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const component = readFileSync(new URL("../src/components/conversational-birth-time-rectification.tsx", import.meta.url), "utf8");
  const start = page.indexOf("async function openBirthTimeRectification");
  const end = page.indexOf("function handleConversationalRectificationTurn", start);
  const handler = page.slice(start, end);

  assert.match(handler, /sourceSession\.sessionType === "birth_time_rectification"[\s\S]*?sourceSession[\s\S]*?sessions\.find/);
  assert.match(component, /<AgenticRectificationChat/);
  assert.doesNotMatch(component, /loadRectificationV4Handoff|loadRectificationV4/);
});

test("rectify-first suggestions hand the source question to a dedicated rectification session", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const start = source.indexOf("function chooseConversationSuggestion");
  const end = source.indexOf("function draftDailyStarlanguageQuestion", start);
  const handler = source.slice(start, end);

  assert.match(handler, /suggestion !== rectifyBeforeConsultationSuggestion/);
  assert.match(handler, /find\(\(message\) => message\.role === "user"\)/);
  assert.match(handler, /rectificationQuestionHandoff\.current\.capture\(\{/);
  assert.match(handler, /sessionId: activeSession\.id/);
  assert.match(handler, /openBirthTimeRectification\(originalQuestion, activeSession\)/);
  assert.match(source, /onClick=\{\(\) => chooseConversationSuggestion\(question\)\}/);
});

test("rectify-first handoffs stay as Agent context without a V4 continuation claim", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const chat = readFileSync(new URL("../src/components/rectification-agentic-chat.tsx", import.meta.url), "utf8");

  assert.match(source, /pendingConsultationQuestion=\{rectificationPendingQuestion\}/);
  assert.match(chat, /pendingConsultationQuestion\?\.trim\(\)/);
  assert.match(chat, /之后再回到你原来的问题/);
  assert.doesNotMatch(source, /onContinueOriginalQuestion|continueRectificationOriginalQuestion|claimRectificationV4Handoff/);
});

test("ordinary consultation uses current birth data without a rectification notice", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const sendStart = source.indexOf("async function send(");
  const consultCall = source.indexOf('fetch("/api/consult"', sendStart);

  assert.ok(sendStart >= 0);
  assert.ok(consultCall > sendStart);
  assert.match(source, /mode: "general_no_birth_time" as const/);
  assert.doesNotMatch(source, /<BirthTimeSoftNotice|setBirthTimeSoftNotice/);
  assert.doesNotMatch(source, /setPendingBirthTimeChoice|<UnverifiedBirthTimeChoice/);
});

test("rectification mutations report pending state while session-level return controls stay absent", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");

  assert.match(source, /onPendingChange=\{setRectificationMutationPending\}/);
  assert.match(source, /disabled=\{productEntrypointsDisabled \|\| rectificationLoading \|\| rectificationMutationPending\}/);
  assert.doesNotMatch(source, /重试恢复/);
  assert.doesNotMatch(source, /返回并恢复原问题|返回首页/);
});

test("session changes contain no birth-time notice state", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const selectSession = source.slice(
    source.indexOf("function selectSession("),
    source.indexOf("async function selectSessionModel", source.indexOf("function selectSession(")),
  );

  assert.doesNotMatch(selectSession, /birthTimeSoftNotice|setBirthTimeSoftNotice/);
  assert.doesNotMatch(source, /dismissBirthTimeSoftNotice/);
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

test("starter homepage stays editorial and hides technical chart parameters", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const styles = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");
  const start = source.indexOf('<div className="starter-list starter-workbench"');
  const end = source.indexOf("{onboardingError &&", start);
  const starterHomepage = source.slice(start, end);

  assert.ok(start >= 0 && end > start);
  assert.match(starterHomepage, /className="starter-hero"/);
  assert.match(starterHomepage, /className="starter-theme-accordion"/);
  assert.match(starterHomepage, /starterSuggestions\.map/);
  assert.doesNotMatch(starterHomepage, /evidencePreview|birthTimeDisplay|Vimshottari|D1|D9/);
  assert.match(source, /const starterSuggestions = starterThemes\.map/);
  assert.match(source, /composer-wrap-starter/);
  assert.match(styles, /\/\* Starter workbench \*\/[\s\S]*?\.starter-list \{[\s\S]*?grid-template-columns: minmax\(0, 1fr\);/);
  assert.match(styles, /\.starter-hero,[\s\S]*?\.product-entrypoints,[\s\S]*?\.starter-themes \{[\s\S]*?width: 100%;/);
});
