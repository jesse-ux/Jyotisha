import assert from "node:assert/strict";
import test from "node:test";
import { dynamicActionReceiptSchema } from "../src/lib/birth-time-dynamic-action-receipt.ts";

const base = {
  actionId: "700406ad-1ca6-437d-9f77-61354ba8e36a",
  turnVersion: 7,
} as const;

test("dynamic receipts strictly bind every user mutation payload", () => {
  for (const receipt of [
    { ...base, kind: "answer_choice", questionId: "question", optionId: "option" },
    {
      ...base,
      kind: "commit_question",
      outcome: "question",
      questionId: "question",
      questionFingerprint: "question-fingerprint",
      partitionFingerprint: "partition-fingerprint",
      submittedQuestionFingerprint: "question-fingerprint",
      submittedPartitionFingerprint: "partition-fingerprint",
    },
    { ...base, kind: "unmatched_context", questionId: "question", note: "大约 2017 年" },
    { ...base, kind: "pause" },
    { ...base, kind: "finish" },
  ]) assert.equal(dynamicActionReceiptSchema.safeParse(receipt).success, true);
});

test("dynamic receipts reject missing, cross-kind, and noncanonical fields", () => {
  for (const receipt of [
    { ...base, kind: "answer_choice", questionId: "question" },
    { ...base, kind: "pause", note: "forged" },
    { ...base, actionId: base.actionId.toUpperCase(), kind: "finish" },
    {
      ...base,
      kind: "commit_question",
      outcome: "terminal",
      questionId: "forged-question",
      questionFingerprint: null,
      partitionFingerprint: null,
      submittedQuestionFingerprint: null,
      submittedPartitionFingerprint: null,
    },
  ]) assert.equal(dynamicActionReceiptSchema.safeParse(receipt).success, false);
});
