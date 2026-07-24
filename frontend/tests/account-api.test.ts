import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  accountProfilePatchSchema,
  resolveAccountBirthTimeApplicationPatch,
} from "../src/lib/account-profile-patch.ts";
import {
  resolveAccountRectificationCase,
} from "../src/lib/account-rectification-case.ts";

const source = readFileSync(new URL("../src/app/api/account/route.ts", import.meta.url), "utf8");
const patchSource = readFileSync(new URL("../src/lib/account-profile-patch.ts", import.meta.url), "utf8");
const caseServiceSource = readFileSync(new URL("../src/lib/account-rectification-case.ts", import.meta.url), "utf8");

test("account API reads and returns the server-configured rectification price", () => {
  assert.match(source, /parseRectificationPriceCredits\(\s*process\.env\.RECTIFICATION_PRICE_CREDITS,?\s*\)/);
  assert.match(source, /rectificationPriceCredits/);
  assert.doesNotMatch(source, /RECTIFICATION_PRICE_CREDITS[^\n]*\?\?\s*["']1["']/);
});

test("account API projects only the minimum case state needed by the homepage", () => {
  const caseSelect = source.match(/\.from\("birth_time_rectification_cases"\)[\s\S]*?\.limit\(\d+\)/)?.[0] ?? "";

  assert.match(caseSelect, /id,journey_protocol,status,turn_version,revision_of_case_id,baseline_active_time,declared_birth_input,updated_at/);
  assert.doesNotMatch(caseSelect, /candidate_scan|event_evidence|validation_receipt|pending_consultation_question|journey_snapshot|turn_state/);
  assert.match(caseServiceSource, /caseId:/);
  assert.match(caseServiceSource, /journeyProtocol:/);
  assert.match(caseServiceSource, /turnVersion:/);
  assert.match(caseServiceSource, /preservesActiveTime:/);
});

test("account API scopes the service-role case lookup to the authenticated account", () => {
  const caseSelect = source.match(/\.from\("birth_time_rectification_cases"\)[\s\S]*?\.limit\(\d+\)/)?.[0] ?? "";

  assert.match(caseSelect, /\.eq\("user_id", user\.id\)/);
  assert.match(caseSelect, /\.eq\("journey_protocol", "conversational-evidence-v3"\)/);
  assert.match(caseSelect, /\.order\("updated_at", \{ ascending: false \}\)/);
});

test("account GET falls back when global birthplace columns are not migrated yet", () => {
  const getSource = source.slice(source.indexOf("export async function GET"), source.indexOf("export async function PATCH"));

  assert.match(getSource, /profileError && isMissingProfileColumn\(profileError\)/);
  assert.match(getSource, /select\("credits,active_birth_time[^"]*timezone_offset"\)/);
  assert.match(getSource, /birth_place_label: undefined/);
  assert.match(getSource, /timezone_id: undefined/);
});

const currentDeclaredProfile = Object.freeze({
  credits: 7,
  active_birth_time: null,
  birth_time_status: "reported",
  rectification_case_id: null,
  birth_date: "1997-08-08",
  reported_birth_time: "05:30:00",
  birth_time_source: "approximate",
  birth_time_period: null,
  birth_time_clue: "家人记得天亮前后",
  uncertainty_before_minutes: 30,
  uncertainty_after_minutes: 30,
  country_code: "CN",
  province_code: "130000",
  city_code: "130400",
  district_code: "130406",
  latitude: 36.420487,
  longitude: 114.209936,
  timezone_offset: 8,
});

const currentDeclaredInput = Object.freeze({
  source: "approximate",
  birthDate: "1997-08-08",
  reportedTime: "05:30",
  uncertaintyBeforeMinutes: 30,
  uncertaintyAfterMinutes: 30,
  birthTimeClue: "家人记得天亮前后",
  birthplace: {
    countryCode: "CN",
    provinceCode: "130000",
    cityCode: "130400",
    districtCode: "130406",
    latitude: 36.420487,
    longitude: 114.209936,
    timezoneOffset: 8,
  },
});

function unfinishedCase(
  declaredBirthInput: unknown = currentDeclaredInput,
  overrides: Record<string, unknown> = {},
) {
  return {
    id: "11111111-1111-4111-8111-111111111111",
    journey_protocol: "conversational-evidence-v3",
    status: "paused",
    turn_version: 4,
    revision_of_case_id: null,
    baseline_active_time: null,
    declared_birth_input: declaredBirthInput,
    private_candidate: { calculationVersion: "must-not-leak" },
    pending_consultation_question: "must-not-leak",
    ...overrides,
  };
}

test("account case projection resumes only an unfinished v3 case matching the current declaration", () => {
  const projected = resolveAccountRectificationCase(
    currentDeclaredProfile,
    [unfinishedCase()],
  );

  assert.deepEqual(projected, {
    caseId: "11111111-1111-4111-8111-111111111111",
    journeyProtocol: "conversational-evidence-v3",
    status: "paused",
    turnVersion: 4,
    isRevision: false,
    preservesActiveTime: false,
  });
  assert.doesNotMatch(
    JSON.stringify(projected),
    /declared|private_candidate|pending_consultation_question|must-not-leak/,
  );
  assert.equal(currentDeclaredProfile.rectification_case_id, null);
});

test("edited declaration fields make old unfinished cases non-resumable without deleting audit rows", () => {
  const declarationMismatches = [
    { ...currentDeclaredInput, birthDate: "1997-08-09" },
    { ...currentDeclaredInput, reportedTime: "05:31" },
    { ...currentDeclaredInput, birthTimeClue: "另一条线索" },
    { ...currentDeclaredInput, uncertaintyBeforeMinutes: 60, uncertaintyAfterMinutes: 60 },
    { ...currentDeclaredInput, birthplace: { ...currentDeclaredInput.birthplace, countryCode: "TW" } },
    { ...currentDeclaredInput, birthplace: { ...currentDeclaredInput.birthplace, provinceCode: "140000" } },
    { ...currentDeclaredInput, birthplace: { ...currentDeclaredInput.birthplace, cityCode: "130500" } },
    { ...currentDeclaredInput, birthplace: { ...currentDeclaredInput.birthplace, districtCode: "130407" } },
    { ...currentDeclaredInput, birthplace: { ...currentDeclaredInput.birthplace, latitude: 36.420488 } },
    { ...currentDeclaredInput, birthplace: { ...currentDeclaredInput.birthplace, longitude: 114.209937 } },
    { ...currentDeclaredInput, birthplace: { ...currentDeclaredInput.birthplace, timezoneOffset: 9 } },
  ];

  for (const declared of declarationMismatches) {
    const row = unfinishedCase(declared);
    assert.equal(resolveAccountRectificationCase(currentDeclaredProfile, [row]), null);
    assert.equal(row.declared_birth_input, declared, "matching must not mutate or delete audit data");
  }

  const periodProfile = {
    ...currentDeclaredProfile,
    reported_birth_time: null,
    birth_time_source: "period_only",
    birth_time_period: "early_morning",
    birth_time_clue: null,
    uncertainty_before_minutes: null,
    uncertainty_after_minutes: null,
  };
  assert.equal(resolveAccountRectificationCase(periodProfile, [unfinishedCase()]), null);
  const periodDeclaration = {
    source: "period_only",
    birthDate: currentDeclaredInput.birthDate,
    reportedPeriod: "early_morning",
    birthTimeClue: null,
    birthplace: currentDeclaredInput.birthplace,
  };
  assert.ok(resolveAccountRectificationCase(periodProfile, [unfinishedCase(periodDeclaration)]));
  assert.equal(resolveAccountRectificationCase(periodProfile, [unfinishedCase({
    ...periodDeclaration,
    reportedPeriod: "morning",
  })]), null);
  assert.equal(resolveAccountRectificationCase(currentDeclaredProfile, [
    unfinishedCase(currentDeclaredInput, { status: "completed" }),
  ]), null);
});

test("account case matching validates optional canonical place labels and can find a later matching row", () => {
  const wrongLabel = unfinishedCase({
    ...currentDeclaredInput,
    birthplace: { ...currentDeclaredInput.birthplace, city: "错误地点" },
  });
  const matching = unfinishedCase(currentDeclaredInput, {
    id: "22222222-2222-4222-8222-222222222222",
    status: "active",
    turn_version: 1,
  });
  const correctlyLabelled = unfinishedCase({
    ...currentDeclaredInput,
    birthplace: {
      ...currentDeclaredInput.birthplace,
      city: "中国 · 河北省 · 邯郸市 · 峰峰矿区",
    },
  });

  assert.ok(resolveAccountRectificationCase(currentDeclaredProfile, [correctlyLabelled]));

  assert.deepEqual(
    resolveAccountRectificationCase(currentDeclaredProfile, [wrongLabel, matching]),
    {
      caseId: "22222222-2222-4222-8222-222222222222",
      journeyProtocol: "conversational-evidence-v3",
      status: "active",
      turnVersion: 1,
      isRevision: false,
      preservesActiveTime: false,
    },
  );
});

test("account case matching resumes a normalized global birthplace without China location codes", () => {
  const globalProfile = {
    ...currentDeclaredProfile,
    country_code: "TW",
    province_code: null,
    city_code: null,
    district_code: null,
    birth_place_label: "台湾 · 台北市",
    birth_place_type: "locality",
    birth_place_provider: "geonames",
    birth_place_provider_id: "1668341",
    timezone_id: "Asia/Taipei",
    timezone_source: "iana_historical",
    latitude: 25.033,
    longitude: 121.5654,
    timezone_offset: 8,
  };
  const globalDeclaration = {
    ...currentDeclaredInput,
    birthplace: {
      city: "台湾 · 台北市",
      placeId: "1668341",
      placeType: "locality",
      provider: "geonames",
      countryCode: "TW",
      latitude: 25.033,
      longitude: 121.5654,
      timezoneId: "Asia/Taipei",
      timezoneSource: "iana_historical",
      timezoneOffset: 8,
    },
  };

  assert.ok(resolveAccountRectificationCase(globalProfile, [unfinishedCase(globalDeclaration)]));
  assert.equal(resolveAccountRectificationCase(globalProfile, [unfinishedCase({
    ...globalDeclaration,
    birthplace: { ...globalDeclaration.birthplace, placeId: "wrong-id" },
  })]), null);
});

test("account case matching recovers an existing global case when profile offset is null and coordinates need durable rounding", () => {
  const globalProfile = {
    ...currentDeclaredProfile,
    country_code: "US",
    province_code: null,
    city_code: null,
    district_code: null,
    birth_place_label: "San Francisco, California, United States",
    birth_place_type: "city",
    birth_place_provider: "geoapify",
    birth_place_provider_id: "sf-place",
    timezone_id: "America/Los_Angeles",
    timezone_source: "iana_historical",
    latitude: 37.7879363,
    longitude: -122.4075201,
    timezone_offset: null,
  };
  const declaration = {
    ...currentDeclaredInput,
    birthplace: {
      city: "San Francisco, California, United States",
      placeId: "sf-place",
      placeType: "city",
      provider: "geoapify",
      countryCode: "US",
      latitude: 37.787936,
      longitude: -122.40752,
      timezoneId: "America/Los_Angeles",
      timezoneSource: "iana_historical",
      timezoneOffset: -8,
    },
  };

  assert.ok(resolveAccountRectificationCase(globalProfile, [unfinishedCase(declaration)]));
  assert.equal(resolveAccountRectificationCase(
    { ...globalProfile, timezone_id: "America/New_York" },
    [unfinishedCase(declaration)],
  ), null);
});

test("account route reads declaration truth only for server matching and does not key resume to profile case id", () => {
  const caseSelect = source.match(/\.from\("birth_time_rectification_cases"\)[\s\S]*?\.limit\(\d+\)/)?.[0] ?? "";
  const responseStart = source.indexOf("return NextResponse.json({\n      user:");
  const responseProjection = source.slice(responseStart, source.indexOf("  } catch", responseStart));

  assert.match(source, /birth_date,reported_birth_time,birth_time_source,birth_time_period,birth_time_clue,uncertainty_before_minutes,uncertainty_after_minutes,country_code,province_code,city_code,district_code,latitude,longitude,timezone_offset/);
  assert.match(caseSelect, /declared_birth_input/);
  assert.match(caseSelect, /\.eq\("user_id", user\.id\)/);
  assert.match(caseSelect, /\.in\("status",/);
  assert.doesNotMatch(caseSelect, /rectification_case_id/);
  assert.match(source, /resolveAccountRectificationCase/);
  assert.doesNotMatch(responseProjection, /declared_birth_input|private_candidate|pending_consultation_question/);
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
  assert.equal(accountProfilePatchSchema.safeParse({
    ...valid,
    timezone_offset: null,
    birth_place_label: "New York, New York, United States",
    birth_place_type: "place",
    birth_place_provider: "mapbox",
    birth_place_provider_id: "place.123",
    timezone_id: "America/New_York",
    timezone_source: "iana_historical",
  }).success, true);
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
    latitude: 36.420487,
    longitude: 114.209936,
    timezone_offset: 8,
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
  for (const coordinatePatch of [
    { latitude: 36.420488 },
    { longitude: 114.209937 },
    { timezone_offset: 9 },
  ]) {
    assert.deepEqual(resolveAccountBirthTimeApplicationPatch(candidate, coordinatePatch), {
      active_birth_time: null,
      birth_time: null,
      birth_time_status: "reported",
      rectification_case_id: null,
    });
  }
  assert.deepEqual(resolveAccountBirthTimeApplicationPatch({
    ...candidate,
    birth_time_status: "confirmed",
  }, edited), {});
  assert.deepEqual(resolveAccountBirthTimeApplicationPatch({
    ...candidate,
    active_birth_time: null,
    birth_time: null,
    birth_time_status: "reported",
  }, { timezone_offset: 7 }), {
    active_birth_time: null,
    birth_time: null,
    birth_time_status: "reported",
    rectification_case_id: null,
  });
});

test("account PATCH uses the shared validator and never writes client birth_time over account truth", () => {
  assert.match(source, /accountProfilePatchSchema\.safeParse/);
  assert.match(source, /resolveAccountBirthTimeApplicationPatch/);
  assert.doesNotMatch(source, /birth_time:\s*nullableString\(payload\.birth_time\)/);
  assert.match(source, /invalidatesUnconfirmedApplication/);
  assert.match(patchSource, /"birth_time_status"/);
  assert.match(patchSource, /"active_birth_time"/);
  assert.match(source, /latitude,longitude,timezone_offset/);
  assert.match(source, /birth_place_label,birth_place_type,birth_place_provider,birth_place_provider_id,timezone_id,timezone_source/);
  assert.match(source, /applyAccountProfileConcurrencyGuards/);
  assert.match(source, /最新确认结果已保留/);
});

test("candidate invalidation compares coordinates and timezone in the conditional write", async () => {
  const { applyAccountProfileConcurrencyGuards } = await import("../src/lib/account-profile-patch.ts");
  const calls: Array<["eq" | "is", string, unknown]> = [];
  const query = {
    eq(column: string, value: unknown) {
      calls.push(["eq", column, value]);
      return this;
    },
    is(column: string, value: null) {
      calls.push(["is", column, value]);
      return this;
    },
  };
  const current = {
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
    country_code: "CN",
    province_code: "130000",
    city_code: "130400",
    district_code: "130406",
    latitude: 36.420487,
    longitude: 114.209936,
    timezone_offset: 8,
  };

  applyAccountProfileConcurrencyGuards(query, current);

  assert.deepEqual(calls.filter((call) => ["latitude", "longitude", "timezone_offset"].includes(call[1])), [
    ["eq", "latitude", 36.420487],
    ["eq", "longitude", 114.209936],
    ["eq", "timezone_offset", 8],
  ]);
  assert.deepEqual(calls.find((call) => call[1] === "active_birth_time"), ["eq", "active_birth_time", "05:18"]);
  assert.deepEqual(calls.find((call) => call[1] === "birth_time_status"), ["eq", "birth_time_status", "candidate"]);
});
