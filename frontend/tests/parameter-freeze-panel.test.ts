import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const pageSource = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
const panelSource = readFileSync(new URL("../src/components/parameter-freeze-panel.tsx", import.meta.url), "utf8");
const globalStyles = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");

test("starter workbench shows a parameter freeze panel when profile is complete", () => {
  assert.match(pageSource, /ParameterFreezePanel/);
  assert.match(pageSource, /parameterFreezeRows/);
  assert.match(pageSource, /Ayanamsa/);
  assert.match(pageSource, /Node mode/);
  assert.match(pageSource, /出生时间精度/);
  assert.match(panelSource, /当前排盘参数冻结/);
  assert.match(panelSource, /这些参数会随咨询一起送入证据链/);
  assert.match(globalStyles, /\.parameter-freeze-panel/);
});
