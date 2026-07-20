import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  accountProfilePatchSchema,
  resolveAccountBirthTimeApplicationPatch,
} from "../src/lib/account-profile-patch.ts";

const source = readFileSync(new URL("../src/app/api/account/route.ts", import.meta.url), "utf8");

test("account API reads and returns the server-configured rectification price", () => {
  assert.match(source, /parseRectificationPriceCredits\(\s*process\.env\.RECTIFICATION_PRICE_CREDITS,?\s*\)/);
  assert.match(source, /rectificationPriceCredits/);
  assert.doesNotMatch(source, /RECTIFICATION_PRICE_CREDITS[^\n]*\?\?\s*["']1["']/);
});

test("account API projects only the minimum case state needed by the homepage", () => {
  const caseSelect = source.match(/\.from\("birth_time_rectification_cases"\)[\s\S]*?\.limit\(1\)/)?.[0] ?? "";

  assert.match(caseSelect, /id,journey_protocol,status,turn_version,revision_of_case_id,baseline_active_time,updated_at/);
  assert.doesNotMatch(caseSelect, /candidate_scan|event_evidence|validation_receipt|pending_consultation_question|journey_snapshot|turn_state/);
  assert.match(source, /caseId:/);
  assert.match(source, /journeyProtocol:/);
  assert.match(source, /turnVersion:/);
  assert.match(source, /preservesActiveTime:/);
});

test("account API scopes the service-role case lookup to the authenticated account", () => {
  const caseSelect = source.match(/\.from\("birth_time_rectification_cases"\)[\s\S]*?\.limit\(1\)/)?.[0] ?? "";

  assert.match(caseSelect, /\.eq\("user_id", user\.id\)/);
  assert.match(caseSelect, /\.eq\("journey_protocol", "conversational-evidence-v3"\)/);
  assert.match(caseSelect, /\.order\("updated_at", \{ ascending: false \}\)/);
});

test("profile patch schema validates calendar, clock, source requirements, and location bounds", () => {
  const valid = {
    name: "岳辰",
    birth_date: "2000-02-29",
    reported_birth_time: "05:30",
    birth_time_source: "family_exact",
    birth_time_period: null,
    birth_time_clue: null,
    uncertainty_before_minutes: 10,
    uncertainty_after_minutes: 10,
    country_code: "CN",
    province_code: "130000",
    city_code: "130400",
    district_code: "130406",
    latitude: 36.420487,
    longitude: 114.209936,
    timezone_offset: 8,
  };

  assert.equal(accountProfilePatchSchema.safeParse(valid).success, true);
  assert.equal(accountProfilePatchSchema.safeParse({ ...valid, birth_date: "2001-02-29" }).success, false);
  assert.equal(accountProfilePatchSchema.safeParse({ ...valid, reported_birth_time: "24:00" }).success, false);
  assert.equal(accountProfilePatchSchema.safeParse({ ...valid, uncertainty_before_minutes: 7 }).success, false);
  assert.equal(accountProfilePatchSchema.safeParse({ ...valid, latitude: 91 }).success, false);
  assert.equal(accountProfilePatchSchema.safeParse({ reported_birth_time: "05:30" }).success, false);
  assert.equal(accountProfilePatchSchema.safeParse({ ...valid, longitude: null }).success, false);
  assert.equal(accountProfilePatchSchema.safeParse({ name: "只改称呼" }).success, true);
  assert.equal(accountProfilePatchSchema.safeParse({
    ...valid,
    reported_birth_time: null,
    birth_time_source: "period_only",
    birth_time_period: null,
    uncertainty_before_minutes: null,
    uncertainty_after_minutes: null,
  }).success, false);
  assert.equal(accountProfilePatchSchema.safeParse({
    ...valid,
    reported_birth_time: null,
    birth_time_source: "unknown",
    birth_time_period: "morning",
    uncertainty_before_minutes: null,
    uncertainty_after_minutes: null,
  }).success, false);
});

test("ordinary declaration edits clear stale candidate application but never overwrite confirmed active time", () => {
  const candidate = {
    birth_date: "1997-08-08",
    reported_birth_time: "05:30",
    birth_time_source: "approximate",
    birth_time_period: null,
    birth_time_clue: null,
    uncertainty_before_minutes: 30,
    uncertainty_after_minutes: 30,
    active_birth_time: "05:18",
    birth_time: "05:18",
    birth_time_status: "candidate",
    rectification_case_id: "11111111-1111-4111-8111-111111111111",
  } as const;
  const edited = {
    birth_date: candidate.birth_date,
    reported_birth_time: "06:10",
    birth_time_source: candidate.birth_time_source,
    birth_time_period: null,
    birth_time_clue: null,
    uncertainty_before_minutes: 30,
    uncertainty_after_minutes: 30,
  } as const;

  assert.deepEqual(resolveAccountBirthTimeApplicationPatch(candidate, edited), {
    active_birth_time: null,
    birth_time: null,
    birth_time_status: "reported",
    rectification_case_id: null,
  });
  assert.deepEqual(resolveAccountBirthTimeApplicationPatch(candidate, {
    district_code: "130407",
  }), {
    active_birth_time: null,
    birth_time: null,
    birth_time_status: "reported",
    rectification_case_id: null,
  });
  assert.deepEqual(resolveAccountBirthTimeApplicationPatch({
    ...candidate,
    birth_time_status: "confirmed",
  }, edited), {});
});

test("account PATCH uses the shared validator and never writes client birth_time over account truth", () => {
  assert.match(source, /accountProfilePatchSchema\.safeParse/);
  assert.match(source, /resolveAccountBirthTimeApplicationPatch/);
  assert.doesNotMatch(source, /birth_time:\s*nullableString\(payload\.birth_time\)/);
  assert.match(source, /invalidatesUnconfirmedApplication/);
  assert.match(source, /query\.eq\("birth_time_status", currentProfile\.birth_time_status\)/);
  assert.match(source, /query\.eq\("active_birth_time", currentProfile\.active_birth_time\)/);
  assert.match(source, /最新确认结果已保留/);
});
