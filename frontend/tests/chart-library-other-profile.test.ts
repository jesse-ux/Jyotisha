import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");

test("other chart saves do not require the owner's rectification state", () => {
  assert.match(source, /function missingOtherProfileStep\(profile: Profile\)/);
  assert.match(source, /if \(missingOtherProfileStep\(nextProfile\)\)/);
  assert.doesNotMatch(source, /saveOtherChart[\s\S]{0,500}missingProfileStep\(nextProfile\)/);
});
