import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("passes transparent public-case references into the agent context", () => {
  const source = readFileSync(new URL("../src/mastra/index.ts", import.meta.url), "utf8");

  assert.match(source, /reference_transparency:\s*record\(data\.reference_transparency\)/);
  assert.match(source, /high_similarity_public_references_available/);
  assert.match(source, /requested_uncovered_domains/);
  assert.match(source, /public_context_only/);
  assert.match(source, /timing_state/);
  assert.match(source, /partial_match/);
  assert.match(source, /exact_triggers as technical trigger points/);
});
