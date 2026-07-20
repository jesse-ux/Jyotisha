import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  canUseUnverifiedBirthTime,
  createBirthTimeConsultationConsentState,
  grantBirthTimeConsultationConsent,
  hasBirthTimeConsultationConsent,
  parseRectificationPriceCredits,
  requiresBirthTimeConsent,
  resolveRectificationCardAction,
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

test("soft choice announces itself and locks every action while rectification opens", () => {
  const source = readFileSync(new URL("../src/components/unverified-birth-time-choice.tsx", import.meta.url), "utf8");

  assert.match(source, /aria-live="polite"/);
  assert.equal((source.match(/disabled=\{pending\}/g) ?? []).length, 3);
  assert.match(source, /\{canUseUnverifiedTime && \(/);
});
