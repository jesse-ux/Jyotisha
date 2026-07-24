import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  LocationSearchCombobox,
  parseLocationSearchResults,
  type ResolvedBirthLocation,
} from "../src/components/location-search-combobox.tsx";

Object.assign(globalThis, { React });

const taipei: ResolvedBirthLocation = {
  id: "nominatim:1293250",
  label: "台北市, 台湾",
  placeType: "city",
  provider: "nominatim",
  providerPlaceId: "1293250",
  countryCode: "TW",
  countryName: "台湾",
  admin1: "台北市",
  admin2: "",
  locality: "台北市",
  latitude: 25.0375,
  longitude: 121.5637,
  timezoneId: "Asia/Taipei",
  timezoneOffset: 8,
  timezoneSource: "historical_tzdb",
};

test("location search parser keeps only complete coordinate and timezone results", () => {
  assert.deepEqual(parseLocationSearchResults({
    locations: [
      { ...taipei, id: undefined, regionName: taipei.admin1, localityName: taipei.locality },
      { ...taipei, id: "", providerPlaceId: "", label: "invalid" },
      { ...taipei, id: "mapbox:unknown-time", timezoneOffset: null },
    ],
  }), [taipei, { ...taipei, id: "mapbox:unknown-time", timezoneOffset: null }]);
  assert.deepEqual(parseLocationSearchResults({ results: "not-an-array" }), []);
});

test("location combobox exposes accessible search semantics and selected state", () => {
  const emptyMarkup = renderToStaticMarkup(React.createElement(LocationSearchCombobox, {
    value: null,
    birthDate: "1997-08-08",
    birthTime: "06:30",
    onChange: () => undefined,
  }));
  assert.match(emptyMarkup, /role="combobox"/);
  assert.match(emptyMarkup, /aria-autocomplete="list"/);
  assert.match(emptyMarkup, /aria-expanded="false"/);
  assert.match(emptyMarkup, /aria-controls="[^"]+-listbox"/);
  assert.match(emptyMarkup, /输入至少两个字开始搜索/);

  const selectedMarkup = renderToStaticMarkup(React.createElement(LocationSearchCombobox, {
    value: taipei,
    onChange: () => undefined,
  }));
  assert.match(selectedMarkup, /value="台北市, 台湾"/);
  assert.match(selectedMarkup, /已选择 台北市, 台湾/);
  assert.match(selectedMarkup, /aria-label="清除出生地点"/);
});

test("profile integrates global location persistence while retaining legacy China fallback", () => {
  const pageSource = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  assert.match(pageSource, /birthPlaceProviderId:\s*string/);
  assert.match(pageSource, /birth_place_provider_id:\s*nextProfile\.birthPlaceProviderId/);
  assert.match(pageSource, /timezone_id:\s*nextProfile\.timezoneId/);
  assert.match(pageSource, /function selectedLocationValue/);
  assert.match(pageSource, /legacy-cn:/);
  assert.match(pageSource, /provinceCode:\s*""[\s\S]*cityCode:\s*""[\s\S]*districtCode:\s*""/);
  assert.doesNotMatch(pageSource, /目前先支持中国大陆地区/);
});

test("selecting a location cancels stale searches and keeps the result list outside the onboarding card", () => {
  const componentSource = readFileSync(new URL("../src/components/location-search-combobox.tsx", import.meta.url), "utf8");
  const globalStyles = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");
  assert.match(componentSource, /function choose\(location: ResolvedBirthLocation\) \{\s*requestSequence\.current \+= 1;/);
  assert.match(globalStyles, /\.birth-time-transition-card \{ position: relative; overflow: visible; \}/);
});

test("profile accepts a selected IANA location before a numeric offset is resolved", () => {
  const pageSource = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  assert.match(pageSource, /profile\.timezoneId\.trim\(\)/);
  assert.match(pageSource, /profile\.timezoneOffset === null \|\| Number\.isFinite\(profile\.timezoneOffset\)/);
  assert.match(pageSource, /timezoneId: birthPlace\.timezoneId/);
});
