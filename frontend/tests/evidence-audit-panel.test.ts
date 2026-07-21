import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const rowSource = readFileSync(new URL("../src/components/chat-message-row.tsx", import.meta.url), "utf8");
const panelSource = readFileSync(new URL("../src/components/evidence-audit-panel.tsx", import.meta.url), "utf8");
const pageSource = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
const globalStyles = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");

test("assistant messages include a collapsible Technique Audit Table shell", () => {
  assert.match(rowSource, /EvidenceAuditPanel/);
  assert.match(rowSource, /claimStatus=\{message\.techniqueTruth\}/);
  assert.match(rowSource, /workflowReceipt=\{message\.workflowReceipt\}/);
  assert.match(panelSource, /Technique Audit Table/);
  assert.match(panelSource, /Workflow route:/);
  assert.match(panelSource, /Precise timing:/);
  assert.match(panelSource, /Missing route layers/);
  assert.match(panelSource, /D1 \/ Natal/);
  assert.match(panelSource, /Narayana Dasha/);
  assert.match(panelSource, /Functional Benefic\/Malefic/);
  assert.match(panelSource, /MEVG \/ Real Case Calibration/);
  assert.match(panelSource, /组件 parity 未全闭环/);
  assert.match(panelSource, /rawReceipt/);
  assert.match(panelSource, /no_birth_data_or_private_case_raw/);
  assert.match(panelSource, /查看非敏感 raw receipt/);
  assert.match(globalStyles, /\.evidence-audit-panel/);
  assert.match(globalStyles, /\.raw-evidence-receipt/);
});

test("consult responses persist workflow receipt headers for evidence rendering", () => {
  assert.match(pageSource, /x-jyotish-workflow-route/);
  assert.match(pageSource, /x-jyotish-workflow-status/);
  assert.match(pageSource, /x-jyotish-precise-timing/);
  assert.match(pageSource, /x-jyotish-missing-layers/);
  assert.match(pageSource, /workflowReceipt/);
});
