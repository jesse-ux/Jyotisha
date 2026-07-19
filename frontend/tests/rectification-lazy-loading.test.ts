import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const page = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");

test("loads birth-time rectification only when its onboarding stage is reached", () => {
  assert.match(page, /import dynamic from "next\/dynamic"/);
  assert.match(page, /const BirthTimeRectification = dynamic\(/);
  assert.match(page, /import\("@\/components\/birth-time-rectification"\)/);
  assert.match(page, /ssr: false/);
  assert.match(page, /role="status"/);
});
