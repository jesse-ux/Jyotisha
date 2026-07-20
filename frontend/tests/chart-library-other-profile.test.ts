import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");

test("other chart saves do not require the owner's rectification state", () => {
  assert.match(source, /function missingOtherProfileStep\(profile: Profile\)/);
  assert.match(source, /if \(missingOtherProfileStep\(nextProfile\)\)/);
  assert.doesNotMatch(source, /saveOtherChart[\s\S]{0,500}missingProfileStep\(nextProfile\)/);
});

test("other chart save falls back to local library when cloud sync fails", () => {
  assert.match(source, /let cloudSaved = false/);
  assert.match(source, /record = await saveCloudChartProfile\(record\);[\s\S]{0,120}cloudSaved = true/);
  assert.match(source, /catch\s*\{[\s\S]{0,300}已保存到本地星盘库；云端同步失败/);
  assert.match(source, /localStorage\.setItem\(chartLibraryStorageKey\(accountId\), JSON\.stringify\(next\)\)/);
  assert.match(source, /if \(cloudSaved\)[\s\S]{0,180}已保存到云端星盘库/);
  assert.match(source, /async function deleteOtherChart[\s\S]{0,500}await deleteCloudChartProfile\(recordId\)/);
  assert.doesNotMatch(source, /deleteOtherChart[\s\S]{0,500}void deleteCloudChartProfile/);
});

test("adding another chart immediately opens the synastry path", () => {
  assert.match(source, /async function saveOtherChart[\s\S]{0,1400}await draftSynastryQuestionFromChart\(record\)/);
  assert.match(source, /用于合盘/);
  assert.match(source, /\/api\/synastry/);
});

test("a successful cloud read replaces stale local other charts", () => {
  assert.match(
    source,
    /fetchCloudChartLibrary\(\)[\s\S]{0,800}upsertSelfChart\(cloudLibrary\.filter\(\(record\) => record\.role !== "self"\), profile\)/,
  );
  assert.doesNotMatch(source, /fetchCloudChartLibrary\(\)[\s\S]{0,800}new Map\(\[[\s\S]{0,500}current\.filter\(\(record\) => record\.role === "other"\)/);
});
