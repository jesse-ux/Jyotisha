import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  ConsultationProfileTruthError,
  prepareConsultationRoute,
} from "../src/lib/consultation-route-service.ts";

const profile = Object.freeze({
  name: "岳辰",
  birth_date: "1997-08-08",
  reported_birth_time: "05:30:00",
  active_birth_time: "05:18:00",
  birth_time_source: "approximate",
  birth_time_status: "candidate",
  country_code: "CN",
  province_code: "130000",
  city_code: "130400",
  district_code: "130406",
  latitude: 36.420487,
  longitude: 114.209936,
  timezone_offset: 8,
});

test("route service loads complete server truth before billing and uses only reported time when unverified", async () => {
  const order: string[] = [];
  const prepared = await prepareConsultationRoute({
    userId: "user-1",
    mode: "unverified_birth_time",
    async loadProfile(userId) {
      assert.equal(userId, "user-1");
      order.push("profile");
      return profile;
    },
    async reserve() {
      order.push("reserve");
      return { reservation: "ok" };
    },
  });

  assert.deepEqual(order, ["profile", "reserve"]);
  assert.deepEqual(prepared.reservation, { reservation: "ok" });
  assert.deepEqual(prepared.serverChart?.toolInput, {
    year: 1997,
    month: 8,
    day: 8,
    hour: 5,
    minute: 30,
    city: "中国 · 河北省 · 邯郸市 · 峰峰矿区",
    lat: 36.420487,
    lon: 114.209936,
    tz: 8,
  });
  assert.equal(prepared.serverChart?.name, "岳辰");
  assert.equal(prepared.serverChart?.truth.birthTimeSource, "approximate");
  assert.equal(prepared.serverChart?.truth.birthTimeStatus, "candidate");
  assert.deepEqual(prepared.serverChart?.truth.placeCodes, {
    countryCode: "CN",
    provinceCode: "130000",
    cityCode: "130400",
    districtCode: "130406",
  });
});

test("verified route uses only server active time", async () => {
  const prepared = await prepareConsultationRoute({
    userId: "user-1",
    mode: "verified_chart",
    loadProfile: async () => ({ ...profile, birth_time_status: "confirmed" }),
    reserve: async () => "reserved",
  });

  assert.equal(prepared.serverChart?.toolInput.hour, 5);
  assert.equal(prepared.serverChart?.toolInput.minute, 18);
  assert.equal(prepared.serverChart?.truth.selectedTimeKind, "active");
});

test("global normalized places use their exact coordinates and historical offset", async () => {
  const prepared = await prepareConsultationRoute({
    userId: "user-global",
    mode: "unverified_birth_time",
    loadProfile: async () => ({
      ...profile,
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
      timezone_offset: 9,
    }),
    reserve: async () => "reserved",
  });

  assert.deepEqual(prepared.serverChart?.toolInput, {
    year: 1997,
    month: 8,
    day: 8,
    hour: 5,
    minute: 30,
    city: "台湾 · 台北市",
    lat: 25.033,
    lon: 121.5654,
    tz: 9,
  });
  assert.equal(prepared.serverChart?.truth.placeId, "1668341");
  assert.equal(prepared.serverChart?.truth.timezoneId, "Asia/Taipei");
});

test("legacy China place codes no longer pin exact coordinates to an administrative center", async () => {
  const prepared = await prepareConsultationRoute({
    userId: "user-precise-cn",
    mode: "unverified_birth_time",
    loadProfile: async () => ({ ...profile, latitude: 36.5, timezone_offset: 9 }),
    reserve: async () => "reserved",
  });

  assert.equal(prepared.serverChart?.toolInput.lat, 36.5);
  assert.equal(prepared.serverChart?.toolInput.tz, 9);
});

test("incomplete, inconsistent, or mode-mismatched profile fails before billing", async () => {
  for (const [expectedCode, invalid] of [
    ["profile_incomplete", { ...profile, birth_date: null }],
    ["profile_inconsistent", { ...profile, latitude: 91 }],
    ["profile_inconsistent", { ...profile, timezone_offset: 15 }],
    ["mode_changed", { ...profile, birth_time_status: "confirmed" }],
  ] as const) {
    let reserveCalls = 0;
    await assert.rejects(
      prepareConsultationRoute({
        userId: "user-1",
        mode: "unverified_birth_time",
        loadProfile: async () => invalid,
        reserve: async () => {
          reserveCalls += 1;
          return "reserved";
        },
      }),
      (error: unknown) => error instanceof ConsultationProfileTruthError
        && error.code === expectedCode,
    );
    assert.equal(reserveCalls, 0);
  }
});

test("profile storage failure is stable and never reaches billing", async () => {
  let reserveCalls = 0;
  await assert.rejects(
    prepareConsultationRoute({
      userId: "user-1",
      mode: "verified_chart",
      loadProfile: async () => { throw new Error("raw database detail"); },
      reserve: async () => {
        reserveCalls += 1;
        return "reserved";
      },
    }),
    (error: unknown) => error instanceof ConsultationProfileTruthError
      && error.code === "profile_unavailable"
      && !error.message.includes("raw database detail"),
  );
  assert.equal(reserveCalls, 0);
});

test("verified global chart resolves a missing historical offset using the final active time before billing", async () => {
  const order: string[] = [];
  const prepared = await prepareConsultationRoute({
    userId: "user-global",
    mode: "verified_chart",
    loadProfile: async () => ({
      ...profile,
      birth_time_status: "confirmed",
      birth_place_label: "San Francisco, California, United States",
      country_code: "US",
      province_code: null,
      city_code: null,
      district_code: null,
      latitude: 37.7879363,
      longitude: -122.4075201,
      timezone_id: "America/Los_Angeles",
      timezone_offset: null,
    }),
    async resolveTimezoneOffset(value, selectedTime) {
      order.push("timezone");
      assert.equal(selectedTime, "05:18");
      return { ...(value as Record<string, unknown>), timezone_offset: -8 };
    },
    async reserve() {
      order.push("reserve");
      return "reserved";
    },
  });

  assert.deepEqual(order, ["timezone", "reserve"]);
  assert.equal(prepared.serverChart?.toolInput.tz, -8);
  assert.equal(prepared.serverChart?.toolInput.hour, 5);
  assert.equal(prepared.serverChart?.toolInput.minute, 18);
});

test("historical timezone failure remains pre-billing", async () => {
  let reserveCalls = 0;
  await assert.rejects(prepareConsultationRoute({
    userId: "user-global",
    mode: "verified_chart",
    loadProfile: async () => ({
      ...profile,
      birth_time_status: "confirmed",
      timezone_id: "America/Los_Angeles",
      timezone_offset: null,
    }),
    resolveTimezoneOffset: async () => { throw new Error("timezone unavailable"); },
    reserve: async () => {
      reserveCalls += 1;
      return "reserved";
    },
  }), (error: unknown) => error instanceof ConsultationProfileTruthError
    && error.code === "profile_unavailable");
  assert.equal(reserveCalls, 0);
});

test("stale general mode is upgraded from persisted exact-minute profile truth", async () => {
  const prepared = await prepareConsultationRoute({
    userId: "user-1",
    mode: "general_no_birth_time",
    loadProfile: async () => ({
      ...profile,
      reported_birth_time: "14:49:00",
      birth_time_source: "family_exact",
      birth_time_status: "reported",
    }),
    reserve: async () => "reserved",
  });

  assert.equal(prepared.consultationMode, "unverified_birth_time");
  assert.equal(prepared.serverChart?.toolInput.hour, 14);
  assert.equal(prepared.serverChart?.toolInput.minute, 49);
  assert.equal(prepared.serverChart?.truth.selectedTimeKind, "reported");
  assert.equal(prepared.reservation, "reserved");
});

test("general mode remains general when persisted profile has no concrete minute", async () => {
  const prepared = await prepareConsultationRoute({
    userId: "user-1",
    mode: "general_no_birth_time",
    loadProfile: async () => ({
      ...profile,
      reported_birth_time: null,
      active_birth_time: null,
      birth_time_source: "period_only",
      birth_time_status: "reported",
    }),
    reserve: async () => "reserved",
  });

  assert.equal(prepared.consultationMode, "general_no_birth_time");
  assert.equal(prepared.serverChart, null);
  assert.equal(prepared.reservation, "reserved");
});

test("consult route constructs workflow input from the route service rather than client chart fields", () => {
  const route = readFileSync(new URL("../src/app/api/consult/route.ts", import.meta.url), "utf8");
  const select = "name,birth_date,reported_birth_time,active_birth_time,birth_time_source,birth_time_status,country_code,province_code,city_code,district_code,latitude,longitude,timezone_offset";

  assert.match(route, new RegExp(select));
  assert.match(route, /prepareConsultationRoute/);
  assert.match(route, /\.\.\.prepared\.serverChart\.toolInput/);
  const toolInput = route.slice(route.indexOf("const toolInput = consultationInputSchema.parse"));
  assert.doesNotMatch(toolInput.slice(0, toolInput.indexOf("const workflowContext")), /\.\.\.parsed\.data/);
});
