import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const identitySource = readFileSync(
  new URL("../src/lib/truth-source-runtime-identity.ts", import.meta.url),
  "utf8",
);
const healthSource = readFileSync(
  new URL("../src/app/api/health/route.ts", import.meta.url),
  "utf8",
);

test("truth source identity records research source without pretending local mount is always present", () => {
  assert.match(identitySource, /DEFAULT_RESEARCH_TRUTH_SOURCE_PATH/);
  assert.doesNotMatch(identitySource, /\/Users\/[^"\n]+/);
  assert.match(identitySource, /resolve\(process\.cwd\(\),\s*"\.\."\)/);
  assert.match(identitySource, /not_mounted/);
  assert.match(identitySource, /claimGateStatus/);
  assert.match(identitySource, /evidencePacketCount/);
  assert.match(identitySource, /oracleSummary/);
});

test("health endpoint exposes truth source identity beside deployment identity", () => {
  assert.match(healthSource, /getTruthSourceRuntimeIdentity/);
  assert.match(healthSource, /truthSource/);
  assert.match(healthSource, /truthSource:\s*truthSourceIdentity/);
  assert.match(healthSource, /researchTruthSource/);
});
