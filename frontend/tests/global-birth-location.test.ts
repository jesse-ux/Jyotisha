import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { birthLocationSearchQuerySchema } from "../src/lib/location-contract.ts";
import { searchGlobalBirthLocations } from "../src/lib/geoapify-location-service.ts";

const migration = readFileSync(
  new URL("../supabase/migrations/20260724010000_global_birth_locations.sql", import.meta.url),
  "utf8",
);
const rectificationContractMigration = readFileSync(
  new URL(
    "../supabase/migrations/20260724020000_align_global_birthplace_rectification_contract.sql",
    import.meta.url,
  ),
  "utf8",
);

test("global birthplace columns keep the account service-role read and upsert path usable", () => {
  assert.match(migration, /grant select, insert, update\s*\([\s\S]*?birth_place_label[\s\S]*?timezone_source[\s\S]*?\) on table public\.profiles to service_role;/i);
});

test("global birthplace metadata is accepted by the durable rectification declaration", () => {
  assert.match(
    rectificationContractMigration,
    /create or replace function public\.conversational_rectification_valid_declared_birth_input/i,
  );
  for (const key of ["placeId", "placeType", "provider", "timezoneId", "timezoneSource"]) {
    assert.match(rectificationContractMigration, new RegExp(`'${key}'`));
  }
  assert.match(
    rectificationContractMigration,
    /\(v_place \? 'city'\) or \(v_place \? 'cityCode'\) or \(v_place \? 'placeId'\)/,
  );
});

test("location search is explicitly unavailable without a server Geoapify key", async () => {
  const result = await searchGlobalBirthLocations({ q: "London", locale: "zh", limit: 5 }, {
    apiKey: "",
    fetchImpl: async () => { throw new Error("must not fetch"); },
  });
  assert.deepEqual(result, { status: "unavailable", reason: "geoapify_not_configured" });
});

test("Geoapify results are normalized and enriched with historical IANA timezone data", async () => {
  const urls: string[] = [];
  const fetchImpl = async (input: string | URL | Request) => {
    const url = String(input);
    urls.push(url);
    if (url.startsWith("https://api.geoapify.com/")) return new Response(JSON.stringify({
      features: [{
        geometry: { coordinates: [-74.006, 40.7128] },
        properties: {
          place_id: "51-test-new-york",
          result_type: "city",
          formatted: "New York, New York, United States",
          city: "New York",
          state: "New York",
          state_code: "NY",
          country: "United States",
          country_code: "us",
        },
      }],
    }), { status: 200 });
    return new Response(JSON.stringify({
      available: true,
      timezoneId: "America/New_York",
      timezoneOffset: -4,
      timezoneSource: "iana_historical",
      localTimeStatus: "resolved",
    }), { status: 200 });
  };

  const result = await searchGlobalBirthLocations({
    q: "New York",
    birthDate: "1990-07-01",
    birthTime: "12:00",
    locale: "en-US",
    limit: 3,
  }, { apiKey: "secret-key", apiBase: "http://api:5200", fetchImpl: fetchImpl as typeof fetch });

  assert.equal(result.status, "ok");
  if (result.status !== "ok") return;
  assert.deepEqual(result.locations[0], {
    provider: "geoapify",
    providerPlaceId: "51-test-new-york",
    placeType: "city",
    label: "New York, New York, United States",
    countryCode: "US",
    countryName: "United States",
    regionCode: "NY",
    regionName: "New York",
    localityName: "New York",
    districtName: null,
    latitude: 40.7128,
    longitude: -74.006,
    timezoneId: "America/New_York",
    timezoneOffset: -4,
    timezoneSource: "iana_historical",
    localTimeStatus: "resolved",
  });
  assert.equal(JSON.stringify(result).includes("secret-key"), false);
  assert.match(urls[0], /format=geojson/);
  assert.match(urls[0], /lang=en(?:&|$)/);
  assert.equal(urls[1], "http://api:5200/api/location/timezone");
});

test("Chinese administrative places use the existing local dataset without spending Geoapify quota", async () => {
  const fetchImpl = async (input: string | URL | Request) => {
    assert.equal(String(input), "http://api:5200/api/location/timezone");
    return new Response(JSON.stringify({
      available: true,
      timezoneId: "Asia/Shanghai",
      timezoneOffset: 8,
      timezoneSource: "iana_historical",
      localTimeStatus: "resolved",
    }), { status: 200 });
  };
  const result = await searchGlobalBirthLocations({
    q: "峰峰矿区",
    birthDate: "1997-08-08",
    birthTime: "06:30",
    locale: "zh-CN",
    limit: 5,
  }, { apiKey: "", apiBase: "http://api:5200", fetchImpl: fetchImpl as typeof fetch });

  assert.equal(result.status, "ok");
  if (result.status !== "ok") return;
  assert.deepEqual(result.locations[0], {
    provider: "china_locations",
    providerPlaceId: "130406",
    placeType: "district",
    label: "中国 · 河北省 · 邯郸市 · 峰峰矿区",
    countryCode: "CN",
    countryName: "中国",
    regionCode: "130000",
    regionName: "河北省",
    localityName: "邯郸市",
    districtName: "峰峰矿区",
    latitude: 36.420487,
    longitude: 114.209936,
    timezoneId: "Asia/Shanghai",
    timezoneOffset: 8,
    timezoneSource: "iana_historical",
    localTimeStatus: "resolved",
  });
});

test("birth time cannot be submitted without a birth date", () => {
  assert.equal(birthLocationSearchQuerySchema.safeParse({ q: "Paris", birthTime: "05:30" }).success, false);
  assert.equal(birthLocationSearchQuerySchema.safeParse({ q: "Paris", birthDate: "2021-02-29" }).success, false);
});
