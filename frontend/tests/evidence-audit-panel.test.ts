import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const rowSource = readFileSync(new URL("../src/components/chat-message-row.tsx", import.meta.url), "utf8");
const panelSource = readFileSync(new URL("../src/components/evidence-audit-panel.tsx", import.meta.url), "utf8");
const globalStyles = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");

test("assistant messages include a collapsible Technique Audit Table shell", () => {
  assert.match(rowSource, /EvidenceAuditPanel/);
  assert.match(rowSource, /claimStatus=\{message\.techniqueTruth\}/);
  assert.match(panelSource, /Technique Audit Table/);
  assert.match(panelSource, /D1 \/ Natal/);
  assert.match(panelSource, /Narayana Dasha/);
  assert.match(panelSource, /Functional Benefic\/Malefic/);
  assert.match(panelSource, /MEVG \/ Real Case Calibration/);
  assert.match(panelSource, /组件 parity 未全闭环/);
  assert.match(globalStyles, /\.evidence-audit-panel/);
});
