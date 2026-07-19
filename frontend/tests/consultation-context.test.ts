import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("passes transparent public-case references into the agent context", () => {
  const source = readFileSync(new URL("../src/mastra/index.ts", import.meta.url), "utf8");

  assert.match(source, /reference_transparency:\s*record\(data\.reference_transparency\)/);
  assert.match(source, /vedastro_gateway:\s*record\(data\.vedastro_gateway\)/);
  assert.match(source, /ashtakavarga:\s*chart\.ashtakavarga/);
  assert.match(source, /high_similarity_public_references_available/);
  assert.match(source, /requested_uncovered_domains/);
  assert.match(source, /public_context_only/);
  assert.match(source, /timing_state/);
  assert.match(source, /partial_match/);
  assert.match(source, /narayana_status/);
  assert.match(source, /transit_status/);
  assert.match(source, /Jupiter and Saturn relative houses/);
  assert.match(source, /exact_triggers as technical trigger points/);
  assert.match(source, /production_tuning_allowed=false/);
  assert.match(source, /no_majority_vote/);
  assert.match(source, /method_variant_not_majority_vote/);
  assert.match(source, /Shadbala\/Ashtakavarga component differences/);
  assert.match(source, /D2, D11/);
});

test("keeps strength, Ashtakavarga, and timing evidence available to the answer model", () => {
  const source = readFileSync(new URL("../src/mastra/index.ts", import.meta.url), "utf8");
  assert.match(source, /shadbala: chart\.shadbala/);
  assert.match(source, /shadbala_boundary:/);
  assert.match(source, /ashtakavarga: modules\.ashtakavarga/);
  assert.match(source, /dasha_boundaries: modules\.dasha_boundaries/);
  assert.match(source, /narayana_dasha: modules\.narayana_dasha/);
  assert.match(source, /evidence_contract:/);
  assert.match(source, /missing_route_layers: consumerContext\.missing_route_layers/);
  assert.match(source, /answer_policy: consumerContext\.answer_policy/);
  assert.match(source, /evidence_contract\.answer_policy/);
  assert.match(source, /can_answer_precise_timing/);
  assert.match(source, /boundary: "not_auto_rectified"/);
  assert.match(source, /rectification\.boundary=not_auto_rectified/);
  assert.match(source, /external_engine_evidence:/);
  assert.match(source, /runtime_truth: record\(data\.runtime_truth\)/);
  assert.match(source, /numerical_parity: record\(data\.external_parity_gate\)/);
  assert.match(source, /real_case_calibration: record\(data\.real_case_calibration\)/);
});
