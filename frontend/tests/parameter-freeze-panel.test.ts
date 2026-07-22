import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";

const pageSource = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
const globalStyles = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");
const panelPath = new URL("../src/components/parameter-freeze-panel.tsx", import.meta.url);

test("starter workbench hides internal chart parameters from users", () => {
  assert.doesNotMatch(pageSource, /ParameterFreezePanel|parameterFreezeRows|当前排盘参数/);
  assert.doesNotMatch(globalStyles, /\.parameter-freeze-panel/);
  assert.equal(existsSync(panelPath), false);
});
