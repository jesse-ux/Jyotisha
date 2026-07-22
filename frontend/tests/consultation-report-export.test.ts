import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { consultationReportMarkdown, downloadMarkdownReport } from "../src/lib/consultation-report-export.ts";
const rowSource = readFileSync(new URL("../src/components/chat-message-row.tsx", import.meta.url), "utf8");
const globalStyles = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");

test("exports latest consultation answer with workflow receipt and claim boundary", () => {
  const report = consultationReportMarkdown({
    title: "事业咨询",
    messages: [
      { role: "user", text: "未来一年事业如何？" },
      {
        role: "assistant",
        text: "先看阶段，不承诺具体日期。",
        techniqueTruth: "partial",
        workflowReceipt: {
          route: "career",
          status: "ready",
          preciseTiming: "blocked",
          missingLayers: ["MEVG"],
        },
      },
    ],
  });
  assert.match(report, /# 事业咨询/);
  assert.match(report, /先看阶段/);
  assert.match(report, /technique_truth: partial/);
  assert.match(report, /workflow_route: career/);
  assert.match(report, /precise_timing: blocked/);
  assert.match(report, /missing_layers: MEVG/);
  assert.match(report, /未闭环内容不得包装成确定预测/);
});

test("assistant answer exposes a markdown report download button", () => {
  assert.equal(typeof downloadMarkdownReport, "function");
  assert.match(rowSource, /下载本次报告/);
  assert.match(rowSource, /downloadMarkdownReport/);
  assert.match(globalStyles, /\.report-download-button/);
});
