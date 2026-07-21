import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  canUseUnverifiedBirthTime,
  birthTimeConsultationOptionsCopy,
  consultationModeForSession,
  createLatestAccountRequestGuard,
  createBirthTimeConsultationConsentState,
  grantBirthTimeConsultationConsent,
  hasBirthTimeConsultationConsent,
  parseRectificationPriceCredits,
  requiresBirthTimeConsent,
  resolveBirthTimeConsultationRoute,
  resolveRectificationCardAction,
  unverifiedBirthTime,
} from "../src/lib/birth-time-consultation-consent.ts";
import type { BirthTimeDraft } from "../src/lib/birth-time-intake-model.ts";

const reportedExactTime = {
  date: "1997-08-08",
  time: "",
  reportedTime: "05:30",
  birthTimeSource: "family_exact",
  birthTimePeriod: "",
  birthTimeClue: "",
  uncertaintyBeforeMinutes: 10,
  uncertaintyAfterMinutes: 10,
  birthTimeStatus: "reported",
} satisfies BirthTimeDraft;

test("an unverified concrete time requires consent only until this chat grants it", () => {
  const initial = createBirthTimeConsultationConsentState();

  assert.equal(canUseUnverifiedBirthTime(reportedExactTime), true);
  assert.equal(requiresBirthTimeConsent(reportedExactTime), true);
  assert.equal(hasBirthTimeConsultationConsent(initial, "chat-a"), false);

  const consented = grantBirthTimeConsultationConsent(initial, "chat-a");
  assert.equal(hasBirthTimeConsultationConsent(consented, "chat-a"), true);
  assert.equal(hasBirthTimeConsultationConsent(consented, "chat-b"), false);
  assert.equal(hasBirthTimeConsultationConsent(initial, "chat-a"), false);
});

test("period-only and unknown declarations never pretend to provide an unverified minute", () => {
  const periodOnly = {
    ...reportedExactTime,
    reportedTime: "",
    birthTimeSource: "period_only",
    birthTimePeriod: "early_morning",
  } satisfies BirthTimeDraft;
  const unknown = {
    ...reportedExactTime,
    reportedTime: "",
    birthTimeSource: "unknown",
    uncertaintyBeforeMinutes: null,
    uncertaintyAfterMinutes: null,
  } satisfies BirthTimeDraft;

  assert.equal(canUseUnverifiedBirthTime(periodOnly), false);
  assert.equal(canUseUnverifiedBirthTime(unknown), false);
  assert.equal(requiresBirthTimeConsent(periodOnly), false);
  assert.equal(requiresBirthTimeConsent(unknown), false);
  assert.match(birthTimeConsultationOptionsCopy(periodOnly), /一般咨询.*校正/);
  assert.match(birthTimeConsultationOptionsCopy(unknown), /一般咨询.*校正/);
  assert.doesNotMatch(birthTimeConsultationOptionsCopy(periodOnly), /使用.*原始填报时间|具体原始时间/);
  assert.doesNotMatch(birthTimeConsultationOptionsCopy(unknown), /使用.*原始填报时间|具体原始时间/);
  assert.match(birthTimeConsultationOptionsCopy(reportedExactTime), /原始填报时间.*校正/);
});

test("the current reported minute wins over an old candidate and never falls back to it", () => {
  const editedCandidate = {
    ...reportedExactTime,
    time: "05:18",
    reportedTime: "06:10",
    birthTimeStatus: "candidate",
  } satisfies BirthTimeDraft;
  const periodCandidate = {
    ...editedCandidate,
    reportedTime: "",
    birthTimeSource: "period_only",
    birthTimePeriod: "early_morning",
  } satisfies BirthTimeDraft;
  const missingReportedCandidate = {
    ...editedCandidate,
    reportedTime: "",
    birthTimeSource: "approximate",
  } satisfies BirthTimeDraft;

  assert.equal(unverifiedBirthTime(editedCandidate), "06:10");
  assert.equal(unverifiedBirthTime(periodCandidate), null);
  assert.equal(unverifiedBirthTime(missingReportedCandidate), null);

  const page = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  assert.match(page, /persistedReportedTime \|\| \(source === "legacy_import" \? time : ""\)/);
});

test("period-only users can explicitly choose a minute-free consultation without carrying it to another chat", () => {
  const periodOnly = {
    ...reportedExactTime,
    reportedTime: "",
    birthTimeSource: "period_only",
    birthTimePeriod: "early_morning",
  } satisfies BirthTimeDraft;
  const initial = createBirthTimeConsultationConsentState();

  assert.deepEqual(resolveBirthTimeConsultationRoute(periodOnly, initial, "chat-a"), {
    kind: "choice",
    canUseUnverifiedTime: false,
  });
  const general = grantBirthTimeConsultationConsent(initial, "chat-a", "general_no_birth_time");
  assert.equal(consultationModeForSession(general, "chat-a"), "general_no_birth_time");
  assert.equal(consultationModeForSession(general, "chat-b"), null);
  assert.deepEqual(resolveBirthTimeConsultationRoute(periodOnly, general, "chat-a"), {
    kind: "consult",
    mode: "general_no_birth_time",
    time: null,
  });
  assert.deepEqual(resolveBirthTimeConsultationRoute(periodOnly, general, "chat-b"), {
    kind: "choice",
    canUseUnverifiedTime: false,
  });
});

test("unverified consent resolves to a chart request and confirmed profiles need no consent", () => {
  const consented = grantBirthTimeConsultationConsent(
    createBirthTimeConsultationConsentState(),
    "chat-a",
    "unverified_birth_time",
  );
  assert.deepEqual(resolveBirthTimeConsultationRoute(reportedExactTime, consented, "chat-a"), {
    kind: "consult",
    mode: "unverified_birth_time",
    time: "05:30",
  });
  assert.deepEqual(resolveBirthTimeConsultationRoute({
    ...reportedExactTime,
    time: "05:28",
    birthTimeStatus: "confirmed",
  }, createBirthTimeConsultationConsentState(), "chat-b"), {
    kind: "consult",
    mode: "verified_chart",
    time: "05:28",
  });
});

test("confirmed time does not request unverified-use consent", () => {
  const confirmed = {
    ...reportedExactTime,
    time: "05:28",
    birthTimeStatus: "confirmed",
  } satisfies BirthTimeDraft;

  assert.equal(canUseUnverifiedBirthTime(confirmed), false);
  assert.equal(requiresBirthTimeConsent(confirmed), false);
});

test("card action resumes unfinished account cases and otherwise starts or revises", () => {
  const unfinishedCase = {
    caseId: "11111111-1111-4111-8111-111111111111",
    journeyProtocol: "conversational-evidence-v3",
    status: "paused",
    turnVersion: 4,
    isRevision: true,
    preservesActiveTime: true,
  } as const;

  assert.equal(resolveRectificationCardAction({ rectificationCase: null, hasConfirmedBirthTime: false }), "start");
  assert.equal(resolveRectificationCardAction({ rectificationCase: unfinishedCase, hasConfirmedBirthTime: true }), "resume");
  assert.equal(resolveRectificationCardAction({
    rectificationCase: { ...unfinishedCase, status: "completed" },
    hasConfirmedBirthTime: true,
  }), "revise");
  assert.equal(resolveRectificationCardAction({
    rectificationCase: { ...unfinishedCase, status: "abandoned" },
    hasConfirmedBirthTime: false,
  }), "start");
});

test("fixed rectification price uses a checked default and rejects invalid configured values", () => {
  assert.equal(parseRectificationPriceCredits(undefined), 1);
  assert.equal(parseRectificationPriceCredits(" 7 "), 7);
  for (const invalid of ["", "0", "101", "1.5", "1e1", "free"]) {
    assert.throws(() => parseRectificationPriceCredits(invalid), /RECTIFICATION_PRICE_CREDITS/);
  }
});

test("account refresh identities reject an older response after a newer case request starts", () => {
  const guard = createLatestAccountRequestGuard();
  const oldCaseRequest = guard.begin();
  const newCaseRequest = guard.begin();

  assert.equal(guard.isCurrent(oldCaseRequest), false);
  assert.equal(guard.isCurrent(newCaseRequest), true);
});

test("soft choice announces itself and locks every action while rectification opens", () => {
  const source = readFileSync(new URL("../src/components/unverified-birth-time-choice.tsx", import.meta.url), "utf8");

  assert.match(source, /aria-live="polite"/);
  assert.match(source, /role="alertdialog"/);
  assert.match(source, /aria-modal="true"/);
  assert.match(source, /keepFocusWithin/);
  assert.match(source, /继续不依赖出生分钟的一般咨询/);
  assert.ok((source.match(/disabled=\{pending\}/g) ?? []).length >= 3);
});

test("homepage and profile result copy use the source-aware consultation options", () => {
  const page = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const intake = readFileSync(new URL("../src/components/birth-time-intake.tsx", import.meta.url), "utf8");

  assert.match(page, /birthTimeConsultationOptionsCopy\(profileDraft\)/);
  assert.match(page, /birthTimeConsultationOptionsCopy\(profile\)/);
  assert.match(intake, /birthTimeConsultationOptionsCopy\(value\)/);
});

test("a saved declaration edit cannot leave the old resumable case in local account state", () => {
  const page = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const saveProfile = page.slice(
    page.indexOf("async function saveProfile"),
    page.indexOf("async function saveOnboardingName"),
  );

  assert.match(saveProfile, /declarationChanged[\s\S]*setAccount\(\(current\)[\s\S]*rectificationCase:\s*null/);
  assert.match(saveProfile, /declarationChanged[\s\S]*void refreshAccount\(\)/);
});
