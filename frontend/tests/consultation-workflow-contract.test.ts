import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const route = readFileSync(new URL("../src/app/api/consult/route.ts", import.meta.url), "utf8");
const mastra = readFileSync(new URL("../src/mastra/index.ts", import.meta.url), "utf8");

test("runs the Jyotish workflow before streaming a commercial consultation", () => {
  assert.match(route, /runConsultationWorkflow/);
  assert.match(route, /await runConsultationWorkflow\(toolInput\)/);
  assert.match(route, /getJyotishAgent\(selectedModel, workflowContext\)\.stream/);
  assert.ok(route.indexOf("await runConsultationWorkflow(toolInput)") < route.indexOf(".stream("));
});

test("grounds the answer in the server-computed workflow without a second tool run", () => {
  assert.match(mastra, /function getJyotishAgent\(model: ResolvedLanguageModel, workflowContext\?/);
  assert.match(mastra, /workflowContext \? \{\} : \{ consultationTool \}/);
  assert.match(mastra, /server-computed Jyotish workflow/);
});

test("validates and emits a non-sensitive workflow receipt", () => {
  assert.match(mastra, /consultationWorkflowResponseSchema/);
  assert.match(mastra, /safeParse\(data\)/);
  assert.match(mastra, /consultationWorkflowReceipt/);
  assert.match(route, /workflowReceipt/);
  assert.match(route, /x-jyotish-workflow-route/);
  assert.match(route, /x-jyotish-workflow-status/);
});

test("carries commercial technique truth into the model contract", () => {
  assert.match(mastra, /technique_truth/);
  assert.match(mastra, /deterministic_claims_forbidden_for/);
  assert.match(mastra, /reference_only/);
  assert.match(mastra, /Do not use a restricted technique/);
  assert.match(route, /x-jyotish-technique-truth/);
});

test("projects consultation themes through explicit strict workflow taxonomy", () => {
  const projection = readFileSync(new URL("../src/lib/consultation-workflow-request.ts", import.meta.url), "utf8");
  assert.match(projection, /strictWorkflowRoute/);
  assert.match(projection, /claimBoundary/);
  assert.match(projection, /requiredLayers/);
  assert.match(projection, /negative holdout gate/);
});
