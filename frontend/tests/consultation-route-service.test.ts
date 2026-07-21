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

test("incomplete, inconsistent, or mode-mismatched profile fails before billing", async () => {
  for (const [expectedCode, invalid] of [
    ["profile_incomplete", { ...profile, birth_date: null }],
    ["profile_inconsistent", { ...profile, latitude: 36.5 }],
    ["profile_inconsistent", { ...profile, timezone_offset: 9 }],
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

test("general route reserves without loading chart profile", async () => {
  let profileLoads = 0;
  const prepared = await prepareConsultationRoute({
    userId: "user-1",
    mode: "general_no_birth_time",
    loadProfile: async () => {
      profileLoads += 1;
      return profile;
    },
    reserve: async () => "reserved",
  });

  assert.equal(profileLoads, 0);
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
