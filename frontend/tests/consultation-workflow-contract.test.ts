import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const route = readFileSync(new URL("../src/app/api/consult/route.ts", import.meta.url), "utf8");
const mastra = readFileSync(new URL("../src/mastra/index.ts", import.meta.url), "utf8");

test("runs the Jyotish workflow before streaming a commercial consultation", () => {
  assert.match(route, /runConsultationWorkflow/);
  assert.match(route, /await runConsultationWorkflow\(toolInput\)/);
  assert.match(route, /getJyotishAgent\(selectedModel, workflowContext\)\.stream/);
  assert.ok(route.indexOf("await runConsultationWorkflow(toolInput)") < route.indexOf(".stream(["));
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
