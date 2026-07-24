import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { profilePayload } from "../src/app/api/daily-starlanguage/route.ts";
import { payloadFromProfile } from "../src/app/api/birth-rectification/route.ts";
import { birthPayload } from "../src/app/api/synastry/route.ts";
import { resolveMissingBirthTimezoneOffset } from "../src/lib/birth-profile-timezone.ts";
import { parseBirthTimeProfile } from "../src/lib/birth-time-journey-adapters.ts";

const sanFrancisco = Object.freeze({
  date: "1955-02-24",
  time: "19:00",
  countryCode: "US",
  provinceCode: "",
  cityCode: "",
  districtCode: "",
  latitude: 37.7879363,
  longitude: -122.4075201,
  timezoneId: "America/Los_Angeles",
  timezoneOffset: -8,
});

test("daily, synastry, and legacy rectification use global coordinates instead of requiring China codes", async () => {
  const daily = await profilePayload(sanFrancisco, "2026-07-24");
  assert.deepEqual(daily && { lat: daily.lat, lon: daily.lon, tz: daily.tz }, {
    lat: 37.7879363,
    lon: -122.4075201,
    tz: -8,
  });

  const synastry = await birthPayload(sanFrancisco);
  assert.deepEqual({ lat: synastry.lat, lon: synastry.lon, tz: synastry.tz }, {
    lat: 37.7879363,
    lon: -122.4075201,
    tz: -8,
  });

  const legacy = await payloadFromProfile(sanFrancisco);
  assert.deepEqual(legacy && { lat: legacy.lat, lon: legacy.lon, tz: legacy.tz }, {
    lat: 37.7879363,
    lon: -122.4075201,
    tz: -8,
  });
});

test("shared timezone resolver supports camelCase browser profiles and preserves the historical reference time", async () => {
  let requestBody: Record<string, unknown> | null = null;
  const resolved = await resolveMissingBirthTimezoneOffset({
    ...sanFrancisco,
    timezoneOffset: null,
  }, {
    apiBase: "http://jyotish:5200",
    preferredTime: "19:00",
    fetchImpl: async (input, init) => {
      assert.equal(String(input), "http://jyotish:5200/api/location/timezone");
      requestBody = JSON.parse(String(init?.body)) as Record<string, unknown>;
      return new Response(JSON.stringify({
        available: true,
        timezoneId: "America/Los_Angeles",
        timezoneOffset: -8,
      }), { status: 200 });
    },
  }) as Record<string, unknown>;

  assert.deepEqual(requestBody, {
    latitude: 37.7879363,
    longitude: -122.4075201,
    birthDate: "1955-02-24",
    birthTime: "19:00",
  });
  assert.equal(resolved.timezone_offset, -8);
  assert.equal(resolved.timezoneOffset, -8);
});

test("journey entry and stored-case loader resolve nullable offsets before strict chart parsing", async () => {
  const resolved = await resolveMissingBirthTimezoneOffset({
    birth_date: "1955-02-24",
    reported_birth_time: null,
    birth_time_source: "period_only",
    birth_time_period: "evening",
    birth_time_clue: "大约晚上七点",
    uncertainty_before_minutes: null,
    uncertainty_after_minutes: null,
    latitude: 37.7879363,
    longitude: -122.4075201,
    timezone_id: "America/Los_Angeles",
    timezone_offset: null,
  }, {
    fetchImpl: async () => new Response(JSON.stringify({
      available: true,
      timezoneId: "America/Los_Angeles",
      timezoneOffset: -8,
    }), { status: 200 }),
  });
  const assessment = parseBirthTimeProfile(resolved);
  assert.deepEqual(assessment.location, { lat: 37.7879363, lon: -122.4075201, tz: -8 });

  const routeSource = readFileSync(new URL("../src/app/api/birth-time-journey/route.ts", import.meta.url), "utf8");
  const loaderSource = readFileSync(new URL("../src/lib/birth-time-journey-case-loader.ts", import.meta.url), "utf8");
  assert.match(routeSource, /timezone_id,timezone_offset/);
  assert.match(routeSource, /resolveMissingBirthTimezoneOffset\(profile\)/);
  assert.match(loaderSource, /birth_date,reported_birth_time,birth_time_period,latitude,longitude,timezone_id,timezone_offset/);
  assert.match(loaderSource, /resolveMissingBirthTimezoneOffset\(profile\)/);
});
