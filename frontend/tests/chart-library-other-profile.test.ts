import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
const route = readFileSync(new URL("../src/app/api/chart-profiles/route.ts", import.meta.url), "utf8");

test("other chart saves do not require the owner's rectification state", () => {
  assert.match(source, /function missingOtherProfileStep\(profile: Profile\)/);
  assert.match(source, /if \(missingOtherProfileStep\(nextProfile\)\)/);
  assert.doesNotMatch(source, /saveOtherChart[\s\S]{0,500}missingProfileStep\(nextProfile\)/);
});

test("other chart mutations acknowledge only confirmed cloud writes", () => {
  assert.match(source, /await saveCloudChartProfile\(record\);[\s\S]{0,500}已保存到云端星盘库/);
  assert.doesNotMatch(source, /saveOtherChart[\s\S]{0,500}catch\s*\{[\s\S]{0,500}已添加到星盘库/);
  assert.match(source, /async function deleteOtherChart[\s\S]{0,500}await deleteCloudChartProfile\(recordId\)/);
  assert.doesNotMatch(source, /deleteOtherChart[\s\S]{0,500}void deleteCloudChartProfile/);
});

test("a successful cloud read replaces stale local other charts", () => {
  assert.match(
    source,
    /fetchCloudChartLibrary\(\)[\s\S]{0,800}upsertSelfChart\(cloudLibrary\.filter\(\(record\) => record\.role !== "self"\), profile\)/,
  );
  assert.doesNotMatch(source, /fetchCloudChartLibrary\(\)[\s\S]{0,800}new Map\(\[[\s\S]{0,500}current\.filter\(\(record\) => record\.role === "other"\)/);
});

test("other chart creation lets the database create its UUID", () => {
  assert.match(route, /\.insert\(\{ user_id: user\.id, role, profile: body\.profile, updated_at: updatedAt \}\)/);
  assert.doesNotMatch(route, /\.upsert\(record, \{ onConflict: "id" \}\)/);
  assert.doesNotMatch(source, /id: record\.role === "self" \? undefined : record\.id/);
});

test("cloud save failures preserve the server error message", () => {
  assert.match(source, /const payload = await response\.json\(\)\.catch\(\(\) => null\) as \{ error\?: string \} \| null;/);
  assert.match(source, /throw new Error\(payload\?\.error \|\| "cloud_chart_profile_save_failed"\);/);
});
