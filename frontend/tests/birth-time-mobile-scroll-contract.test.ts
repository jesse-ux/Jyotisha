import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const css = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");

test("mobile rectification welcome content starts at the scroll origin", () => {
  assert.match(css, /@media \(max-width: 767px\)[\s\S]*?\.conversation\.is-empty\s*\{[^}]*display:\s*block/);
  assert.match(css, /\.conversation\s*\{[^}]*min-height:\s*0[^}]*overflow-y:\s*auto/);
});
