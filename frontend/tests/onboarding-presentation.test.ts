import assert from "node:assert/strict";
import test from "node:test";
import {
  createOnboardingFallbackGreeting,
  createStartGreeting,
  isCurrentOnboardingRequest,
  onboardingProfileFingerprint,
  onboardingRequestIdentity,
} from "../src/lib/onboarding-client.ts";

const completeProfile = {
  name: "林遥", date: "1990-06-15", time: "12:30", reportedTime: "12:30",
  birthTimeSource: "hospital_record", birthTimePeriod: "", birthTimeClue: "出生证明", birthTimeStatus: "confirmed",
  uncertaintyBeforeMinutes: 0, uncertaintyAfterMinutes: 0, rectificationCaseId: "", countryCode: "CN", provinceCode: "110000", cityCode: "110000-city", districtCode: "110101",
} as const;

test("rejects stale A presentation and derives terminal and fallback greetings from profile B", () => {
  // Given: one account starts onboarding for a complete persisted profile A.
  const firstIdentity = onboardingRequestIdentity("account-1", onboardingProfileFingerprint(completeProfile));

  // When: the name changes before that request completes and profile B is presented.
  const changedProfile = { ...completeProfile, name: "周宁" };
  const currentIdentity = onboardingRequestIdentity("account-1", onboardingProfileFingerprint(changedProfile));
  const terminalGreeting = createStartGreeting(changedProfile.name, new Date("2026-07-19T08:00:00+08:00"), 0);
  const fallbackGreeting = createOnboardingFallbackGreeting(changedProfile.name);

  // Then: stale work is rejected and neither presentation path can retain A's name.
  assert.notEqual(currentIdentity, firstIdentity);
  assert.equal(isCurrentOnboardingRequest(currentIdentity, firstIdentity), false);
  for (const greeting of [terminalGreeting, fallbackGreeting]) {
    assert.match(greeting, /周宁/);
    assert.doesNotMatch(greeting, /林遥/);
  }
  assert.equal(fallbackGreeting, "周宁，从你此刻最关心的问题开始吧。");
});
