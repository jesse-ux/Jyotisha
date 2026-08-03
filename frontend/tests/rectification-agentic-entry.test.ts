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
  assert.match(route, /parsed\.data\.action === "opening"/);
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
