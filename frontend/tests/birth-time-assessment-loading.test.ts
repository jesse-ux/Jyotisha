import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("onboarding keeps the current card visible while birth-time assessment is pending", () => {
  // Given: saving the selected time can span profile persistence and assessment requests.
  const source = [
    readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8"),
    readFileSync(new URL("../src/components/birth-time-assessment-overlay.tsx", import.meta.url), "utf8"),
  ].join("\n");

  // When: the UI enters either pending phase.
  // Then: the current form stays mounted and exposes one busy status surface.
  assert.match(source, /birthTimeAssessmentPhase/);
  assert.match(source, /const onboardingCardReady = presetMessageFinished \|\| birthTimeAssessmentPhase !== null/);
  assert.match(source, /onboardingStep === "birth" && onboardingCardReady/);
  assert.match(source, /onboardingStep === "place" && onboardingCardReady/);
  assert.match(source, /className="birth-time-assessment-overlay"/);
  assert.match(source, /aria-busy=\{birthTimeAssessmentPhase !== null\}/);
  assert.match(source, /previewMode === "birth-time-assessment-loading"/);
  assert.match(source, /saveOnboardingBirth[\s\S]*?setBirthTimeAssessmentPhase\("saving_profile"\)/);
  assert.match(source, /saveOnboardingPlace[\s\S]*?setBirthTimeAssessmentPhase\("entering_home"\)/);
  assert.match(source, /entering_home:[\s\S]*?title: "正在进入首页"[\s\S]*?detail: "出生资料已保存，正在为你准备首页。"/);
});
