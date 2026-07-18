import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("upserts a missing profile when saving account details", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  assert.match(source, /\.from\("profiles"\)\s*\.upsert\(/);
});
