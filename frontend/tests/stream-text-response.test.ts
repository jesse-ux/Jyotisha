import assert from "node:assert/strict";
import test from "node:test";
import { streamTextResponse } from "../src/lib/stream-text-response.ts";

test("charges a consultation when cancellation happens after partial output", async () => {
  // Given
  let completed = 0;
  let cancelled = 0;
  async function* reply() {
    yield "部分回答";
    yield "剩余回答";
  }
  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000001",
    onComplete: async () => { completed += 1; },
    onCancel: async (emitted) => {
      if (emitted) completed += 1;
      else cancelled += 1;
    },
  });
  const reader = response.body?.getReader();
  assert.ok(reader);
  await reader.read();

  // When
  await reader.cancel();

  // Then
  assert.equal(cancelled, 0);
  assert.equal(completed, 1);
});

test("refunds when cancellation happens before any output", async () => {
  // Given
  let completed = 0;
  let cancelled = 0;
  async function* reply() {
    yield "回答";
  }
  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000003",
    onComplete: async () => { completed += 1; },
    onCancel: async (emitted) => {
      if (emitted) completed += 1;
      else cancelled += 1;
    },
  });
  const reader = response.body?.getReader();
  assert.ok(reader);

  // When
  await reader.cancel();

  // Then
  assert.equal(cancelled, 1);
  assert.equal(completed, 0);
});

test("completes billing only after a non-empty stream finishes", async () => {
  // Given
  let completed = 0;
  async function* reply() {
    yield "完整回答";
  }
  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000002",
    onComplete: async () => { completed += 1; },
  });

  // When
  const answer = await response.text();

  // Then
  assert.equal(answer, "完整回答");
  assert.equal(completed, 1);
});

test("does not run cancellation settlement once completion has started", async () => {
  // Given
  let completed = 0;
  let cancelled = 0;
  let releaseCompletion = () => {};
  const completionGate = new Promise<void>((resolve) => {
    releaseCompletion = resolve;
  });
  let markCompletionStarted = () => {};
  const completionStarted = new Promise<void>((resolve) => {
    markCompletionStarted = resolve;
  });
  async function* reply() {
    yield "完整回答";
  }
  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000004",
    onComplete: async () => {
      completed += 1;
      markCompletionStarted();
      await completionGate;
    },
    onCancel: async () => { cancelled += 1; },
  });
  const reader = response.body?.getReader();
  assert.ok(reader);
  await reader.read();

  // When
  const finalRead = reader.read();
  await completionStarted;
  const cancellation = reader.cancel();
  releaseCompletion();
  await Promise.all([finalRead, cancellation]);

  // Then
  assert.equal(completed, 1);
  assert.equal(cancelled, 0);
});
