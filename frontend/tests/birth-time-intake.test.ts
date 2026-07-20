import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  applyBirthTimeDraftPatch,
  assistantIntentCopy,
  birthTimeDisplayState,
  birthTimePersistenceValues,
  describeBirthTimeDraft,
  formatBirthDate,
  isDeclaredBirthProfileComplete,
  isBirthTimeReadyForConsultation,
  isBirthTimeDraftReady,
  parseBirthDate,
  type BirthTimeDraft,
} from "../src/lib/birth-time-intake-model.ts";

const emptyDraft: BirthTimeDraft = {
  date: "1993-04-17",
  time: "",
  reportedTime: "",
  birthTimeSource: "",
  birthTimePeriod: "",
  birthTimeClue: "",
  uncertaintyBeforeMinutes: null,
  uncertaintyAfterMinutes: null,
  birthTimeStatus: "",
};

test("birth time intake requires only the fields selected by the source", () => {
  const hospital = {
    ...emptyDraft,
    birthTimeSource: "hospital_record",
    reportedTime: "08:16",
    uncertaintyBeforeMinutes: 2,
    uncertaintyAfterMinutes: 2,
  } satisfies BirthTimeDraft;
  const period = {
    ...emptyDraft,
    birthTimeSource: "period_only",
    birthTimePeriod: "evening",
  } satisfies BirthTimeDraft;
  const incompleteApproximate = {
    ...emptyDraft,
    birthTimeSource: "approximate",
    reportedTime: "14:30",
  } satisfies BirthTimeDraft;

  assert.equal(isBirthTimeDraftReady(hospital), true);
  assert.equal(isBirthTimeDraftReady(period), true);
  assert.equal(isBirthTimeDraftReady(incompleteApproximate), false);
  assert.equal(isBirthTimeDraftReady({ ...emptyDraft, birthTimeSource: "unknown" }), true);
});

test("a persisted candidate working time can leave rectification onboarding", () => {
  const candidate = {
    ...emptyDraft,
    time: "04:53",
    birthTimeStatus: "candidate",
  } satisfies BirthTimeDraft;

  assert.equal(isBirthTimeReadyForConsultation(candidate), true);
  assert.equal(isBirthTimeReadyForConsultation({ ...candidate, time: "" }), false);
  assert.equal(isBirthTimeReadyForConsultation({ ...candidate, birthTimeStatus: "rectifying" }), false);
});

test("declared birth data completes onboarding without an active or confirmed minute", () => {
  const declaredExact = {
    ...emptyDraft,
    reportedTime: "05:30",
    birthTimeSource: "family_exact",
    uncertaintyBeforeMinutes: 10,
    uncertaintyAfterMinutes: 10,
    birthTimeStatus: "reported",
  } satisfies BirthTimeDraft;
  const declaredPeriod = {
    ...emptyDraft,
    birthTimeSource: "period_only",
    birthTimePeriod: "early_morning",
    birthTimeStatus: "reported",
  } satisfies BirthTimeDraft;

  assert.equal(isDeclaredBirthProfileComplete(declaredExact), true);
  assert.equal(isBirthTimeReadyForConsultation(declaredExact), false);
  assert.equal(isDeclaredBirthProfileComplete(declaredPeriod), true);
  assert.equal(isBirthTimeReadyForConsultation(declaredPeriod), false);
});

test("declared completeness validates the actual calendar date, clock, source fields, and bounds", () => {
  const exact = {
    ...emptyDraft,
    birthTimeSource: "family_exact",
    reportedTime: "05:30",
    uncertaintyBeforeMinutes: 10,
    uncertaintyAfterMinutes: 10,
  } satisfies BirthTimeDraft;

  assert.equal(isDeclaredBirthProfileComplete({ ...exact, date: "2000-02-29" }), true);
  assert.equal(isDeclaredBirthProfileComplete({ ...exact, date: "2001-02-29" }), false);
  assert.equal(isDeclaredBirthProfileComplete({ ...exact, date: "1899-12-31" }), false);
  assert.equal(isDeclaredBirthProfileComplete({ ...exact, date: "2101-01-01" }), false);
  assert.equal(isDeclaredBirthProfileComplete({ ...exact, reportedTime: "24:00" }), false);
  assert.equal(isDeclaredBirthProfileComplete({ ...exact, reportedTime: "5:30" }), false);
  assert.equal(isDeclaredBirthProfileComplete({ ...exact, uncertaintyBeforeMinutes: 7 }), false);
  assert.equal(isDeclaredBirthProfileComplete({
    ...emptyDraft,
    birthTimeSource: "hospital_record",
    reportedTime: "05:30",
  }), false);
  assert.equal(isDeclaredBirthProfileComplete({
    ...emptyDraft,
    birthTimeSource: "period_only",
    birthTimePeriod: "",
  }), false);
  assert.equal(isDeclaredBirthProfileComplete({
    ...emptyDraft,
    birthTimeSource: "period_only",
    birthTimePeriod: "morning",
    uncertaintyBeforeMinutes: 30,
  }), false);
  assert.equal(isDeclaredBirthProfileComplete({
    ...emptyDraft,
    birthTimeSource: "unknown",
    reportedTime: "05:30",
  }), false);
  assert.equal(isDeclaredBirthProfileComplete({
    ...emptyDraft,
    birthTimeSource: "unknown",
    birthTimeClue: "x".repeat(241),
  }), false);
  assert.equal(isDeclaredBirthProfileComplete(exact, {
    label: "中国 · 河北省 · 邯郸市",
    lat: 36.62,
    lon: 114.49,
    tz: 8,
  }), true);
  assert.equal(isDeclaredBirthProfileComplete(exact, {
    label: "越界地点",
    lat: 91,
    lon: 114.49,
    tz: 8,
  }), false);
  assert.equal(isDeclaredBirthProfileComplete(exact, null), false);
});

test("editing an unconfirmed declaration invalidates an old candidate but preserves confirmed active time", () => {
  const candidate = {
    ...emptyDraft,
    time: "05:18",
    reportedTime: "05:30",
    birthTimeSource: "approximate",
    uncertaintyBeforeMinutes: 30,
    uncertaintyAfterMinutes: 30,
    birthTimeStatus: "candidate",
  } satisfies BirthTimeDraft;

  assert.deepEqual(applyBirthTimeDraftPatch(candidate, { reportedTime: "06:10" }), {
    ...candidate,
    time: "",
    reportedTime: "06:10",
    birthTimeStatus: "reported",
  });
  assert.deepEqual(applyBirthTimeDraftPatch(candidate, {
    uncertaintyBeforeMinutes: 60,
    uncertaintyAfterMinutes: 60,
  }), {
    ...candidate,
    time: "",
    uncertaintyBeforeMinutes: 60,
    uncertaintyAfterMinutes: 60,
    birthTimeStatus: "reported",
  });

  const confirmed = { ...candidate, birthTimeStatus: "confirmed" } satisfies BirthTimeDraft;
  assert.deepEqual(applyBirthTimeDraftPatch(confirmed, { reportedTime: "06:10" }), {
    ...confirmed,
    reportedTime: "06:10",
  });
});

test("a persisted candidate working time takes precedence over the reported range", () => {
  // Given: rectification saved a candidate minute while preserving the user's original period.
  const candidate = {
    ...emptyDraft,
    time: "04:53",
    birthTimeSource: "period_only",
    birthTimePeriod: "early_morning",
    birthTimeStatus: "candidate",
  } satisfies BirthTimeDraft;

  // When: a profile surface asks what birth-time state to display.
  const display = birthTimeDisplayState(candidate);

  // Then: the candidate minute is primary and the original period remains secondary.
  assert.deepEqual(display, {
    kind: "candidate",
    activeTime: "04:53",
    reportedLabel: "凌晨 / 清晨（04:00—07:59）",
  });
});

test("birth time declaration payload cannot write deterministic application fields", () => {
  const draft = {
    ...emptyDraft,
    time: "14:24",
    reportedTime: "14:30",
    birthTimeSource: "approximate",
    uncertaintyBeforeMinutes: 30,
    uncertaintyAfterMinutes: 30,
    birthTimeStatus: "confirmed",
  } satisfies BirthTimeDraft;

  assert.deepEqual(birthTimePersistenceValues(draft), {
    reported_birth_time: "14:30",
    birth_time_source: "approximate",
    birth_time_period: null,
    birth_time_clue: null,
    uncertainty_before_minutes: 30,
    uncertainty_after_minutes: 30,
  });
});

test("birth time intake describes uncertainty without claiming false precision", () => {
  const approximate = {
    ...emptyDraft,
    birthTimeSource: "approximate",
    reportedTime: "14:30",
    uncertaintyBeforeMinutes: 30,
    uncertaintyAfterMinutes: 30,
  } satisfies BirthTimeDraft;

  assert.equal(describeBirthTimeDraft(approximate), "1993年4月17日，约 14:30（前后 30 分钟）");
  assert.equal(
    assistantIntentCopy("present_saved_candidate_range"),
    "目前只能保存候选范围，还没有足够证据应用到具体分钟。",
  );
});

test("birth date parsing preserves the local calendar day", () => {
  const parsed = parseBirthDate("1993-04-17");

  assert.equal(parsed?.getFullYear(), 1993);
  assert.equal(parsed?.getMonth(), 3);
  assert.equal(parsed?.getDate(), 17);
});

test("birth date values round trip leap days and reject invalid input", () => {
  const leapDay = parseBirthDate("2000-02-29");

  assert.equal(leapDay === undefined ? undefined : formatBirthDate(leapDay), "2000-02-29");
  assert.equal(parseBirthDate(""), undefined);
  assert.equal(parseBirthDate("2001-02-29"), undefined);
});

test("candidate copy does not claim an unconfirmed minute is automatically in use", () => {
  const source = readFileSync(new URL("../src/components/birth-time-intake.tsx", import.meta.url), "utf8");

  assert.doesNotMatch(source, /已用于当前排盘/);
  assert.match(source, /普通咨询只能临时使用上面的原始填报时间/);
});
