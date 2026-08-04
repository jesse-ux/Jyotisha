import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const component = readFileSync(
  new URL("../src/components/conversational-birth-time-rectification.tsx", import.meta.url),
  "utf8",
);
const chat = readFileSync(
  new URL("../src/components/rectification-agentic-chat.tsx", import.meta.url),
  "utf8",
);
const route = readFileSync(
  new URL("../src/app/api/rectification/agent/route.ts", import.meta.url),
  "utf8",
);
const page = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");

test("birth-time rectification entry no longer routes through V4", () => {
  assert.doesNotMatch(component, /loadActiveRectificationV4|RectificationV4Panel|transitionRectificationV4/);
  assert.match(component, /return <AgenticRectificationChat \{\.\.\.props\} \/>/);
});

test("opening is a server-owned operation rather than a hidden user prompt", () => {
  assert.doesNotMatch(chat, /agenticOpeningInstruction|用户刚进入生时校正会话/);
  assert.match(chat, /action: "opening"/);
  assert.match(route, /z\.literal\("opening"\)/);
  assert.match(route, /conversation\.action === "opening"/);
});

test("incomplete profiles stay in the shared onboarding flow", () => {
  const opening = page.slice(
    page.indexOf("async function openBirthTimeRectification"),
    page.indexOf("resumeRectificationSession.current ="),
  );
  assert.match(opening, /const missingStep = missingProfileStep\(profile\)/);
  assert.match(opening, /setOnboardingStep\(missingStep\)/);
  assert.ok(
    opening.indexOf("const missingStep = missingProfileStep(profile)")
      < opening.indexOf("setRectificationSessionId(rectificationSession.id)"),
  );
  assert.match(chat, /payload\?\.code === "profile_incomplete"/);
});

test("server profile failures pause automatic rectification resume", () => {
  const resumeEffect = page.slice(
    page.indexOf('useEffect(() => {\n    if (!hydrated'),
    page.indexOf('useEffect(() => {\n    if (!hydrated || !accountId'),
  );
  const incompleteHandler = page.slice(
    page.indexOf("function handleRectificationProfileIncomplete"),
    page.indexOf("async function draftSynastryQuestionFromChart"),
  );
  assert.match(resumeEffect, /\|\| rectificationError\) return/);
  assert.match(incompleteHandler, /setRectificationError\("profile_incomplete"\)/);
  assert.ok(
    incompleteHandler.indexOf('setRectificationError("profile_incomplete")')
      < incompleteHandler.indexOf("setRectificationSessionId(null)"),
  );
});

test("account rehydration normalizes persisted ISO birth dates before completeness checks", () => {
  const profileReader = page.slice(
    page.indexOf("function readProfile"),
    page.indexOf("function readSessions"),
  );
  assert.match(profileReader, /const date = normalizePersistedBirthDate\(/);
});

test("agent tool calls leave a final step for visible prose and never end silently", () => {
  assert.match(route, /const agenticRectificationMaxSteps = 8/);
  assert.match(route, /\{ maxSteps: agenticRectificationMaxSteps \}/);
  assert.match(route, /if \(!emitted \|\| !reply\.text\) \{[\s\S]*type: "error"[\s\S]*await settle\(false\)[\s\S]*return;/);
  assert.doesNotMatch(route, /send\(\{ type: "done", emitted \}\)/);
});

test("rectification messages survive remounts and suppress duplicate openings", () => {
  assert.match(chat, /initialMessages: readonly ChatMessage\[\]/);
  assert.match(chat, /if \(initialMessages\.length > 0 \|\| openingStarted\.current\) return/);
  assert.match(chat, /sessionId,/);
  assert.match(chat, /onMessagesChange\?\.\(/);
  assert.match(page, /key=\{rectificationSessionId\}/);
  assert.match(page, /initialMessages=\{activeSession\?\.messages \?\? \[\]\}/);
  assert.match(page, /onMessagesChange=\{handleRectificationMessagesChange\}/);
});

test("successful Agent turns are persisted by the authenticated rectification route", () => {
  assert.match(route, /sessionId: z\.string\(\)\.uuid\(\)/);
  assert.match(route, /\.from\("chat_sessions"\)[\s\S]*\.eq\("user_id", userId\)/);
  assert.match(route, /conversation\.action === "opening" && persistedMessages\.length > 0/);
  assert.match(route, /\.update\(\{ messages: nextMessages, updated_at:/);
  assert.match(route, /if \(saveError \|\| !savedSession\) throw new Error\("RectificationSessionPersistenceError"\)/);
});


test("candidate results restore only through the authenticated rectification session", () => {
  const getRoute = route.slice(
    route.indexOf("export async function GET"),
    route.indexOf("export async function POST"),
  );
  assert.match(getRoute, /sessionId/);
  assert.match(getRoute, /\.eq\("user_id", user\.id\)/);
  assert.match(getRoute, /session\.session_type !== "birth_time_rectification"/);
  assert.match(getRoute, /loadLatestAgenticRectificationResult\(accounting, user\.id, sessionId\)/);
});

test("candidate acceptance is non-billable and happens before consultation credit reservation", () => {
  const acceptance = route.indexOf('parsed.data.action === "accept_candidate"');
  const reserve = route.indexOf('"begin_consultation_credit"');
  assert.ok(acceptance >= 0 && reserve > acceptance);
});

test("candidate state streams before done and renders relative support controls", () => {
  assert.match(route, /send\(\{ type: "candidates", result: candidateResult \}\)[\s\S]*send\(\{ type: "done", emitted: true \}\)/);
  assert.match(chat, /fetch\(`\/api\/rectification\/agent\?sessionId=/);
  assert.match(chat, /action: "accept_candidate"/);
  assert.match(chat, /相对支持度仅用于本次候选比较，不是统计概率/);
  assert.match(chat, /采用 \$\{candidate\.time\}/);
});

test("stream failures remove empty assistant placeholders", () => {
  assert.match(chat, /streamFailed = true/);
  assert.match(chat, /const succeeded = completed && !streamFailed && Boolean\(parsed\.text\)/);
  assert.match(chat, /current\.filter\(\(message\) => message\.renderKey !== assistantRenderKey\)/);
  assert.match(chat, /if \(succeeded\)/);
});

test("new rectification sessions are created before the Agent surface mounts", () => {
  assert.match(page, /await rectificationPersistence\.current\.enqueue[\s\S]*setRectificationSessionId\(rectificationSession\.id\)/);
  assert.doesNotMatch(page, /setRectificationSessionId\(rectificationSession\.id\)[\s\S]{0,500}persistSession\(rectificationSession, "create"\)/);
});
